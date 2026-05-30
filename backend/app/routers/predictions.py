"""Prediction endpoints: single, JSON batch, CSV upload, history, dashboard."""
from __future__ import annotations

import io
import logging
from collections import Counter
from typing import Any

import pandas as pd
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..inference import InferenceEngine, get_engine
from ..models import PredictionBatch, StudentPrediction, User
from ..schemas import (
    BatchDetail,
    BatchSummary,
    DashboardStats,
    PredictionResult,
    PredictRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["predictions"])


def _persist_batch(
    db: Session,
    user: User,
    label: str,
    source_filename: str | None,
    results: list[dict[str, Any]],
) -> PredictionBatch:
    n_at_risk = sum(1 for r in results if r["at_risk"])
    avg_risk = (
        float(sum(r["risk_score"] for r in results) / len(results)) if results else 0.0
    )
    batch = PredictionBatch(
        label=label,
        source_filename=source_filename,
        n_students=len(results),
        n_at_risk=n_at_risk,
        avg_risk=avg_risk,
        created_by_id=user.id,
    )
    db.add(batch)
    db.flush()
    for r in results:
        db.add(
            StudentPrediction(
                batch_id=batch.id,
                student_ref=r.get("student_ref"),
                risk_score=r["risk_score"],
                at_risk=int(bool(r["at_risk"])),
                risk_band=r["risk_band"],
                base_value=r["base_value"],
                raw_features=r["raw_features"],
                contributions=r["contributions"],
                interventions=r["interventions"],
            )
        )
    db.commit()
    db.refresh(batch)
    return batch


def _serialize_pred(p: StudentPrediction) -> PredictionResult:
    return PredictionResult(
        student_ref=p.student_ref,
        risk_score=p.risk_score,
        at_risk=bool(p.at_risk),
        risk_band=p.risk_band,  # type: ignore[arg-type]
        base_value=p.base_value,
        contributions=p.contributions,
        interventions=p.interventions,
    )


@router.post("/predict", response_model=list[PredictionResult])
def predict(
    payload: PredictRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    engine: InferenceEngine = Depends(get_engine),
) -> list[PredictionResult]:
    if not payload.students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="students cannot be empty"
        )
    rows = [s.model_dump() for s in payload.students]
    try:
        results = engine.predict_records(rows)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _persist_batch(db, user, payload.label, None, results)
    return [PredictionResult(**{k: v for k, v in r.items() if k != "raw_features"}) for r in results]


@router.post("/predict/csv", response_model=BatchDetail)
async def predict_csv(
    file: UploadFile = File(...),
    label: str | None = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    engine: InferenceEngine = Depends(get_engine),
) -> BatchDetail:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        try:
            df = pd.read_csv(io.BytesIO(raw))
        except Exception:
            df = pd.read_csv(io.BytesIO(raw), sep=";")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {exc}") from exc

    if "student_ref" not in df.columns:
        df.insert(0, "student_ref", [f"S{i+1:04d}" for i in range(len(df))])
    records = df.to_dict(orient="records")
    try:
        results = engine.predict_records(records)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    batch = _persist_batch(
        db, user, label or file.filename or "csv-upload", file.filename, results
    )
    return BatchDetail(
        id=batch.id,
        label=batch.label,
        source_filename=batch.source_filename,
        n_students=batch.n_students,
        n_at_risk=batch.n_at_risk,
        avg_risk=batch.avg_risk,
        created_at=batch.created_at,
        predictions=[_serialize_pred(p) for p in batch.predictions],
    )


@router.get("/batches", response_model=list[BatchSummary])
def list_batches(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
) -> list[BatchSummary]:
    q = db.query(PredictionBatch)
    if user.role != "hod":
        q = q.filter(PredictionBatch.created_by_id == user.id)
    rows = q.order_by(desc(PredictionBatch.created_at)).limit(limit).all()
    return [BatchSummary.model_validate(b) for b in rows]


@router.get("/batches/{batch_id}", response_model=BatchDetail)
def get_batch(
    batch_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BatchDetail:
    batch = db.get(PredictionBatch, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    if user.role != "hod" and batch.created_by_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    return BatchDetail(
        id=batch.id,
        label=batch.label,
        source_filename=batch.source_filename,
        n_students=batch.n_students,
        n_at_risk=batch.n_at_risk,
        avg_risk=batch.avg_risk,
        created_at=batch.created_at,
        predictions=[_serialize_pred(p) for p in batch.predictions],
    )


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardStats:
    batch_q = db.query(PredictionBatch)
    pred_q = db.query(StudentPrediction).join(PredictionBatch)
    if user.role != "hod":
        batch_q = batch_q.filter(PredictionBatch.created_by_id == user.id)
        pred_q = pred_q.filter(PredictionBatch.created_by_id == user.id)

    total_batches = batch_q.count()
    total_students = pred_q.count()
    total_at_risk = pred_q.filter(StudentPrediction.at_risk == 1).count()
    avg_risk_val = pred_q.with_entities(
        func.coalesce(func.avg(StudentPrediction.risk_score), 0.0)
    ).scalar()

    band_counts: dict[str, int] = {"low": 0, "medium": 0, "high": 0}
    for band, n in pred_q.with_entities(
        StudentPrediction.risk_band, func.count()
    ).group_by(StudentPrediction.risk_band).all():
        band_counts[band] = int(n)

    driver_counter: Counter[str] = Counter()
    impact_sum: dict[str, float] = {}
    sample = pred_q.order_by(desc(StudentPrediction.created_at)).limit(500).all()
    for p in sample:
        for c in (p.contributions or [])[:3]:
            feat = c.get("feature")
            shap_val = float(c.get("shap", 0.0))
            if not feat or shap_val <= 0:
                continue
            driver_counter[feat] += 1
            impact_sum[feat] = impact_sum.get(feat, 0.0) + shap_val
    top_drivers = [
        {
            "feature": feat,
            "count": int(driver_counter[feat]),
            "avg_impact": float(impact_sum[feat] / driver_counter[feat]),
        }
        for feat, _ in driver_counter.most_common(8)
    ]

    recent = (
        batch_q.order_by(desc(PredictionBatch.created_at)).limit(5).all()
    )
    return DashboardStats(
        total_batches=total_batches,
        total_students=total_students,
        total_at_risk=total_at_risk,
        avg_risk=float(avg_risk_val or 0.0),
        risk_band_counts=band_counts,
        top_drivers=top_drivers,
        recent_batches=[BatchSummary.model_validate(b) for b in recent],
    )
