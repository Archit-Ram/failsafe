"""Sklearn ColumnTransformer that mirrors what the model expects at inference."""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import CATEGORICAL_FEATURES, NUMERIC_FEATURES, PIPELINE_PATH


def build_preprocessor() -> ColumnTransformer:
    """One-hot for categoricals + standard-scaled numerics."""
    return ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
            ("num", StandardScaler(), NUMERIC_FEATURES),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def fit_preprocessor(X: pd.DataFrame) -> Pipeline:
    pre = build_preprocessor()
    pre.fit(X)
    return pre


def feature_names(preprocessor: ColumnTransformer) -> list[str]:
    return list(preprocessor.get_feature_names_out())


def save_preprocessor(preprocessor: ColumnTransformer, path=PIPELINE_PATH) -> None:
    joblib.dump(preprocessor, path)


def load_preprocessor(path=PIPELINE_PATH) -> ColumnTransformer:
    return joblib.load(path)


def transform(preprocessor: ColumnTransformer, X: pd.DataFrame) -> np.ndarray:
    return preprocessor.transform(X)
