"""Project-wide constants for the FAILSAFE ML pipeline.

Centralising column lists, paths and the labelling rule keeps the data,
preprocessing, training and inference modules in lock-step.
"""
from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
MODEL_DIR = ROOT_DIR / "models"
REPORTS_DIR = ROOT_DIR / "reports"

DATA_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# UCI Student Performance dataset (Math course = student-mat.csv).
UCI_ZIP_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/00320/student.zip"
)
RAW_CSV = DATA_DIR / "student-mat.csv"
PROCESSED_CSV = DATA_DIR / "student_processed.csv"

# Persisted artefacts.
MODEL_PATH = MODEL_DIR / "xgb_failsafe.json"
PIPELINE_PATH = MODEL_DIR / "preprocessor.joblib"
META_PATH = MODEL_DIR / "metadata.json"
SHAP_BACKGROUND_PATH = MODEL_DIR / "shap_background.npy"

# Behavioural / attendance features used for *early* prediction.
# G1/G2/G3 are intentionally excluded so faculty can intervene
# before the final grade is observed.
CATEGORICAL_FEATURES: list[str] = [
    "school",
    "sex",
    "address",
    "famsize",
    "Pstatus",
    "Mjob",
    "Fjob",
    "reason",
    "guardian",
    "schoolsup",
    "famsup",
    "paid",
    "activities",
    "nursery",
    "higher",
    "internet",
    "romantic",
]

NUMERIC_FEATURES: list[str] = [
    "age",
    "Medu",
    "Fedu",
    "traveltime",
    "studytime",
    "failures",
    "famrel",
    "freetime",
    "goout",
    "Dalc",
    "Walc",
    "health",
    "absences",
]

ALL_FEATURES: list[str] = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET_COL = "at_risk"
PASS_THRESHOLD = 10  # UCI grade 0-20; <10 is a fail.

RANDOM_STATE = 42
