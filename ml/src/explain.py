"""SHAP utilities for FAILSAFE.

Wraps shap.TreeExplainer so the backend can ask for a per-student
explanation in a stable, JSON-friendly format.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
import shap
from sklearn.compose import ColumnTransformer
from xgboost import XGBClassifier


@dataclass
class StudentExplanation:
    risk_score: float
    base_value: float
    contributions: list[tuple[str, float, float]]  # (feature, raw_value, shap)

    def to_dict(self) -> dict:
        return {
            "risk_score": float(self.risk_score),
            "base_value": float(self.base_value),
            "contributions": [
                {
                    "feature": feat,
                    "value": float(val) if val is not None else None,
                    "shap": float(shap),
                }
                for feat, val, shap in self.contributions
            ],
        }


class FailsafeExplainer:
    """Wraps a TreeExplainer + the project's preprocessor.

    Caller supplies the *raw* student dataframe (with the canonical
    columns); we transform, predict, and produce SHAP values mapped
    back to the human-readable feature names.
    """

    def __init__(
        self,
        model: XGBClassifier,
        preprocessor: ColumnTransformer,
        feature_names: Iterable[str],
        background: np.ndarray | None = None,
    ) -> None:
        self.model = model
        self.preprocessor = preprocessor
        self.feature_names = list(feature_names)
        if background is not None and len(background) > 0:
            self.explainer = shap.TreeExplainer(
                model,
                data=background,
                feature_perturbation="interventional",
                model_output="probability",
            )
        else:
            self.explainer = shap.TreeExplainer(model)

    @staticmethod
    def _raw_value(
        feature: str,
        raw_row: pd.Series,
    ) -> float | str | None:
        """Best-effort recovery of the original value behind a transformed col."""
        if feature in raw_row.index:
            return raw_row[feature]
        if "_" in feature:
            base, level = feature.split("_", 1)
            if base in raw_row.index:
                return 1.0 if str(raw_row[base]) == level else 0.0
        return None

    def explain_one(
        self,
        raw_row: pd.Series,
        top_k: int = 8,
    ) -> StudentExplanation:
        X = self.preprocessor.transform(raw_row.to_frame().T)
        proba = float(self.model.predict_proba(X)[0, 1])
        sv = self.explainer.shap_values(X)
        if isinstance(sv, list):  # legacy multi-output shape
            sv = sv[1]
        shap_row = np.asarray(sv).reshape(-1)
        base = self.explainer.expected_value
        if isinstance(base, (list, np.ndarray)):
            base = float(np.atleast_1d(base)[-1])
        contribs: list[tuple[str, float, float]] = []
        for feat, sv_val in zip(self.feature_names, shap_row):
            raw_val = self._raw_value(feat, raw_row)
            try:
                num_raw = float(raw_val) if raw_val is not None else None
            except (TypeError, ValueError):
                num_raw = None
            contribs.append((feat, num_raw if num_raw is not None else 0.0, float(sv_val)))
        contribs.sort(key=lambda t: abs(t[2]), reverse=True)
        return StudentExplanation(
            risk_score=proba,
            base_value=float(base),
            contributions=contribs[:top_k],
        )
