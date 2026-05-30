"""Download / load the UCI Student Performance dataset.

Falls back to generating a deterministic synthetic dataset (same schema)
when the network is not available, so the rest of the pipeline always
has something to operate on for demos and tests.
"""
from __future__ import annotations

import io
import logging
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from .config import (
    ALL_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    PASS_THRESHOLD,
    RAW_CSV,
    TARGET_COL,
    UCI_ZIP_URL,
)

logger = logging.getLogger(__name__)


def _download_uci(target_csv: Path = RAW_CSV) -> Path:
    """Fetch student-mat.csv from the UCI archive."""
    target_csv.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading UCI Student Performance dataset...")
    resp = requests.get(UCI_ZIP_URL, timeout=30)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        with zf.open("student-mat.csv") as src, open(target_csv, "wb") as dst:
            dst.write(src.read())
    logger.info("Saved %s", target_csv)
    return target_csv


def _synthetic_dataset(n: int = 600, seed: int = 7) -> pd.DataFrame:
    """Generate a UCI-shaped fallback dataset.

    The structure (columns, dtypes, value domains) mirrors the real
    dataset so downstream code does not need a separate code path.
    """
    rng = np.random.default_rng(seed)
    cat_choices: dict[str, list[str]] = {
        "school": ["GP", "MS"],
        "sex": ["F", "M"],
        "address": ["U", "R"],
        "famsize": ["LE3", "GT3"],
        "Pstatus": ["T", "A"],
        "Mjob": ["teacher", "health", "services", "at_home", "other"],
        "Fjob": ["teacher", "health", "services", "at_home", "other"],
        "reason": ["home", "reputation", "course", "other"],
        "guardian": ["mother", "father", "other"],
        "schoolsup": ["yes", "no"],
        "famsup": ["yes", "no"],
        "paid": ["yes", "no"],
        "activities": ["yes", "no"],
        "nursery": ["yes", "no"],
        "higher": ["yes", "no"],
        "internet": ["yes", "no"],
        "romantic": ["yes", "no"],
    }
    df = pd.DataFrame(
        {col: rng.choice(opts, size=n) for col, opts in cat_choices.items()}
    )
    df["age"] = rng.integers(15, 23, size=n)
    df["Medu"] = rng.integers(0, 5, size=n)
    df["Fedu"] = rng.integers(0, 5, size=n)
    df["traveltime"] = rng.integers(1, 5, size=n)
    df["studytime"] = rng.integers(1, 5, size=n)
    df["failures"] = rng.integers(0, 4, size=n)
    df["famrel"] = rng.integers(1, 6, size=n)
    df["freetime"] = rng.integers(1, 6, size=n)
    df["goout"] = rng.integers(1, 6, size=n)
    df["Dalc"] = rng.integers(1, 6, size=n)
    df["Walc"] = rng.integers(1, 6, size=n)
    df["health"] = rng.integers(1, 6, size=n)
    df["absences"] = rng.integers(0, 35, size=n)

    # Latent risk score that loosely matches the real-world signal.
    risk = (
        0.45 * df["failures"]
        + 0.05 * df["absences"]
        + 0.20 * (df["Dalc"] + df["Walc"])
        + 0.15 * df["goout"]
        - 0.30 * df["studytime"]
        - 0.10 * (df["Medu"] + df["Fedu"])
        + 0.30 * (df["schoolsup"] == "no").astype(int)
        + 0.20 * (df["higher"] == "no").astype(int)
        + rng.normal(0, 1.2, size=n)
    )
    g3 = np.clip(15 - 1.5 * risk + rng.normal(0, 1.5, size=n), 0, 20)
    df["G1"] = np.clip(g3 + rng.normal(0, 2, size=n), 0, 20).round().astype(int)
    df["G2"] = np.clip(g3 + rng.normal(0, 1.5, size=n), 0, 20).round().astype(int)
    df["G3"] = g3.round().astype(int)
    return df


def load_raw(force_download: bool = False) -> pd.DataFrame:
    """Return the raw UCI dataframe; download or synthesise as needed."""
    if force_download or not RAW_CSV.exists():
        try:
            _download_uci()
        except Exception as exc:  # pragma: no cover - network heuristics
            logger.warning(
                "UCI download failed (%s); falling back to synthetic data.", exc
            )
            df = _synthetic_dataset()
            df.to_csv(RAW_CSV, sep=";", index=False)
            return df
    return pd.read_csv(RAW_CSV, sep=";")


def add_target(df: pd.DataFrame, threshold: int = PASS_THRESHOLD) -> pd.DataFrame:
    """Append the binary at-risk label using G3."""
    out = df.copy()
    out[TARGET_COL] = (out["G3"] < threshold).astype(int)
    return out


def feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Return only the early-warning feature columns in canonical order."""
    missing = [c for c in ALL_FEATURES if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")
    out = df[ALL_FEATURES].copy()
    for col in CATEGORICAL_FEATURES:
        out[col] = out[col].astype(str)
    for col in NUMERIC_FEATURES:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out
