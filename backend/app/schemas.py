"""Pydantic request/response models."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=6)
    department: str | None = None
    role: Literal["faculty", "hod"] = "faculty"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    department: str | None = None
    role: str
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------- predictions ----------
class StudentRecord(BaseModel):
    """Raw student row exactly as expected by the model.

    Categorical columns accept strings ("yes"/"no", "GP"/"MS", ...);
    numeric columns accept ints/floats.
    """

    model_config = ConfigDict(extra="allow")
    student_ref: str | None = None


class Contribution(BaseModel):
    feature: str
    value: float | None
    shap: float


class InterventionItem(BaseModel):
    title: str
    detail: str
    category: str
    driver: str
    impact: float


class PredictionResult(BaseModel):
    student_ref: str | None
    risk_score: float
    at_risk: bool
    risk_band: Literal["low", "medium", "high"]
    base_value: float
    contributions: list[Contribution]
    interventions: list[InterventionItem]


class PredictRequest(BaseModel):
    students: list[StudentRecord]
    label: str = "ad-hoc"


class BatchSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    label: str
    source_filename: str | None
    n_students: int
    n_at_risk: int
    avg_risk: float
    created_at: datetime


class BatchDetail(BatchSummary):
    predictions: list[PredictionResult]


class DashboardStats(BaseModel):
    total_batches: int
    total_students: int
    total_at_risk: int
    avg_risk: float
    risk_band_counts: dict[str, int]
    top_drivers: list[dict[str, Any]]
    recent_batches: list[BatchSummary]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    feature_count: int
