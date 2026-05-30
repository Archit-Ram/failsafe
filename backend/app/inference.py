"""Loads the trained XGBoost + preprocessor and exposes a clean API.

The backend imports `get_engine()` once at startup; the engine is then
reused across requests. We add the project root to `sys.path` so the
`ml.src.*` helpers (interventions, explainer) can be reused without
duplication.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from threading import Lock
from typing import Any

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from .config import get_settings

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = REPO_ROOT / "ml"
if str(ML_ROOT) not in sys.path:
    sys.path.insert(0, str(ML_ROOT))

# Imports below intentionally come after sys.path manipulation.
from src.explain import FailsafeExplainer  # noqa: E402
from src.interventions import generate as generate_interventions  # noqa: E402

logger = logging.getLogger(__name__)
_settings = get_settings()
_lock = Lock()
_engine: "InferenceEngine | None" = None


def _band(score: float) -> str:
    if score >= 0.66:
        return "high"
    if score >= 0.33:
        return "medium"
    return "low"


class InferenceEngine:
    def __init__(self) -> None:
        model_path = Path(_settings.ml_model_path)
        pipeline_path = Path(_settings.ml_pipeline_path)
        background_path = Path(_settings.ml_background_path)
        meta_path = Path(_settings.ml_metadata_path)
        if not model_path.exists() or not pipeline_path.exists():
            raise FileNotFoundError(
                "Trained model artefacts not found. "
                "Run `python -m src.train` from the ml/ directory first."
            )
        self.model = XGBClassifier()
        self.model.load_model(str(model_path))
        self.preprocessor = joblib.load(pipeline_path)
        self.background = (
            np.load(background_path) if background_path.exists() else None
        )
        self.metadata: dict[str, Any] = (
            json.loads(meta_path.read_text()) if meta_path.exists() else {}
        )
        self.feature_columns_raw: list[str] = self.metadata.get(
            "feature_columns_raw", []
        )
        self.feature_columns_transformed: list[str] = list(
            self.preprocessor.get_feature_names_out()
        )
        self.explainer = FailsafeExplainer(
            self.model,
            self.preprocessor,
            self.feature_columns_transformed,
            background=self.background,
        )
        logger.info(
            "Loaded model with %d raw / %d encoded features",
            len(self.feature_columns_raw),
            len(self.feature_columns_transformed),
        )

    def _coerce_row(self, row: dict[str, Any]) -> dict[str, Any]:
        cleaned: dict[str, Any] = {}
        for col in self.feature_columns_raw:
            if col not in row or row[col] in (None, ""):
                raise ValueError(f"Missing required field '{col}'")
            cleaned[col] = row[col]
        return cleaned

    def predict_records(
        self,
        records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not records:
            return []
        cleaned_rows = []
        student_refs: list[str | None] = []
        for r in records:
            student_refs.append(r.get("student_ref"))
            cleaned_rows.append(self._coerce_row(r))
        df = pd.DataFrame(cleaned_rows, columns=self.feature_columns_raw)
        results: list[dict[str, Any]] = []
        for ref, (_, row) in zip(student_refs, df.iterrows()):
            explanation = self.explainer.explain_one(row, top_k=8)
            interventions = generate_interventions(
                explanation.contributions, top_k=4
            )
            score = explanation.risk_score
            results.append(
                {
                    "student_ref": ref,
                    "risk_score": score,
                    "at_risk": bool(score >= 0.5),
                    "risk_band": _band(score),
                    "base_value": explanation.base_value,
                    "contributions": [
                        {"feature": f, "value": v, "shap": s}
                        for f, v, s in explanation.contributions
                    ],
                    "interventions": interventions,
                    "raw_features": row.to_dict(),
                }
            )
        return results


def get_engine() -> InferenceEngine:
    global _engine
    with _lock:
        if _engine is None:
            _engine = InferenceEngine()
    return _engine


def reset_engine() -> None:
    """Used by tests / model-reload endpoints."""
    global _engine
    with _lock:
        _engine = None
