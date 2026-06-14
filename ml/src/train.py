"""Train the FAILSAFE XGBoost classifier and persist all artefacts."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from .config import (
    ALL_FEATURES,
    META_PATH,
    MODEL_PATH,
    PROCESSED_CSV,
    RANDOM_STATE,
    SHAP_BACKGROUND_PATH,
    TARGET_COL,
)
from .data import add_target, feature_frame, load_raw
from .preprocess import (
    feature_names,
    fit_preprocessor,
    save_preprocessor,
    transform,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("train")


def train(
    test_size: float = 0.2,
    n_estimators: int = 400,
    learning_rate: float = 0.05,
    max_depth: int = 4,
) -> dict:
    df = add_target(load_raw())
    df.to_csv(PROCESSED_CSV, sep=";", index=False)
    logger.info("Dataset: %d rows | risk rate = %.2f%%",
                len(df), 100 * df[TARGET_COL].mean())

    X_raw = feature_frame(df)
    y = df[TARGET_COL].astype(int).to_numpy()

    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X_raw, y, test_size=test_size, stratify=y, random_state=RANDOM_STATE
    )

    pre = fit_preprocessor(X_train_raw)
    X_train = transform(pre, X_train_raw)
    X_test = transform(pre, X_test_raw)
    cols = feature_names(pre)

    pos = float((y_train == 1).sum())
    neg = float((y_train == 0).sum())
    spw = neg / max(pos, 1.0)

    model = XGBClassifier(
        n_estimators=n_estimators,
        learning_rate=learning_rate,
        max_depth=max_depth,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        objective="binary:logistic",
        eval_metric="logloss",
        scale_pos_weight=2.0,
        random_state=RANDOM_STATE,
        tree_method="hist",
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "f1": float(f1_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_proba)),
        "test_size": float(test_size),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "scale_pos_weight": float(spw),
    }
    logger.info("Test metrics | %s", json.dumps(metrics, indent=2))
    logger.info(
        "Confusion matrix:\n%s", confusion_matrix(y_test, y_pred)
    )
    logger.info(
        "Classification report:\n%s",
        classification_report(y_test, y_pred, target_names=[
                              "pass", "at_risk"]),
    )

    bg_idx = np.random.default_rng(RANDOM_STATE).choice(
        len(X_train), size=min(100, len(X_train)), replace=False
    )
    background = X_train[bg_idx]

    model.save_model(str(MODEL_PATH))
    save_preprocessor(pre)
    np.save(SHAP_BACKGROUND_PATH, background)

    meta = {
        "metrics": metrics,
        "feature_columns_raw": ALL_FEATURES,
        "feature_columns_transformed": cols,
        "model_path": str(MODEL_PATH),
        "preprocessor_path": str(MODEL_PATH.parent / "preprocessor.joblib"),
        "shap_background_path": str(SHAP_BACKGROUND_PATH),
        "target": TARGET_COL,
        "params": {
            "n_estimators": n_estimators,
            "learning_rate": learning_rate,
            "max_depth": max_depth,
        },
    }
    META_PATH.write_text(json.dumps(meta, indent=2))
    logger.info("Saved model -> %s", MODEL_PATH)
    logger.info("Saved preprocessor -> %s", meta["preprocessor_path"])
    logger.info("Saved metadata -> %s", META_PATH)
    return meta


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--n-estimators", type=int, default=400)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--max-depth", type=int, default=4)
    args = parser.parse_args()
    train(
        test_size=args.test_size,
        n_estimators=args.n_estimators,
        learning_rate=args.learning_rate,
        max_depth=args.max_depth,
    )
