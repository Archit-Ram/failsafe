"""ORM tables: users, prediction batches, prediction rows."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(32), default="faculty")  # faculty | hod
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    batches: Mapped[list["PredictionBatch"]] = relationship(
        back_populates="created_by", cascade="all, delete-orphan"
    )


class PredictionBatch(Base):
    __tablename__ = "prediction_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    label: Mapped[str] = mapped_column(String(255))
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    n_students: Mapped[int] = mapped_column(Integer, default=0)
    n_at_risk: Mapped[int] = mapped_column(Integer, default=0)
    avg_risk: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped[User] = relationship(back_populates="batches")
    predictions: Mapped[list["StudentPrediction"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class StudentPrediction(Base):
    __tablename__ = "student_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("prediction_batches.id"))
    student_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    risk_score: Mapped[float] = mapped_column(Float)
    at_risk: Mapped[int] = mapped_column(Integer)  # 0/1 for sqlite-friendly
    risk_band: Mapped[str] = mapped_column(String(16))
    base_value: Mapped[float] = mapped_column(Float, default=0.0)
    raw_features: Mapped[dict] = mapped_column(JSON)
    contributions: Mapped[list] = mapped_column(JSON)
    interventions: Mapped[list] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    batch: Mapped[PredictionBatch] = relationship(back_populates="predictions")
