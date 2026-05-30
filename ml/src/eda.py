"""Exploratory Data Analysis for the UCI Student Performance dataset.

Run with `python -m ml.src.eda` from the project root, or
`python src/eda.py` from inside `ml/`. All figures are written to
`ml/reports/` so they can be reviewed without launching a notebook.
"""
from __future__ import annotations

import argparse
import logging

import matplotlib

matplotlib.use("Agg")  # Headless-safe backend (figures are saved to disk).
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

from .config import NUMERIC_FEATURES, REPORTS_DIR, TARGET_COL
from .data import add_target, load_raw

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("eda")

sns.set_theme(style="whitegrid", context="talk")


def _save(fig: plt.Figure, name: str) -> None:
    out = REPORTS_DIR / name
    fig.tight_layout()
    fig.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out)


def plot_target_balance(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    counts = df[TARGET_COL].value_counts().rename({0: "Pass", 1: "At-risk"})
    sns.barplot(x=counts.index, y=counts.values, palette=["#3a86ff", "#ef476f"], ax=ax)
    ax.set_title("Class balance (G3 < 10 ⇒ at-risk)")
    ax.set_ylabel("Students")
    _save(fig, "01_target_balance.png")


def plot_grade_distribution(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.histplot(df["G3"], bins=21, color="#118ab2", kde=True, ax=ax)
    ax.axvline(10, color="crimson", ls="--", label="Pass threshold (10)")
    ax.set_title("Distribution of final grade (G3)")
    ax.legend()
    _save(fig, "02_g3_distribution.png")


def plot_correlation(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 8))
    corr = df[NUMERIC_FEATURES + ["G3", TARGET_COL]].corr(numeric_only=True)
    sns.heatmap(
        corr, cmap="vlag", center=0, annot=False, ax=ax, cbar_kws={"shrink": 0.8}
    )
    ax.set_title("Numeric feature correlations")
    _save(fig, "03_correlation_heatmap.png")


def plot_feature_vs_target(df: pd.DataFrame) -> None:
    cols = ["absences", "failures", "studytime", "Dalc", "Walc", "goout"]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    for ax, col in zip(axes.flat, cols):
        sns.boxplot(
            data=df,
            x=TARGET_COL,
            y=col,
            ax=ax,
            palette=["#3a86ff", "#ef476f"],
        )
        ax.set_xticklabels(["Pass", "At-risk"])
        ax.set_title(f"{col} vs. risk")
    fig.suptitle("Behavioural features stratified by risk", fontsize=18)
    _save(fig, "04_features_vs_target.png")


def plot_categorical_risk(df: pd.DataFrame) -> None:
    cols = ["schoolsup", "higher", "internet", "romantic", "sex", "address"]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    for ax, col in zip(axes.flat, cols):
        rate = df.groupby(col)[TARGET_COL].mean().sort_values()
        sns.barplot(x=rate.index, y=rate.values, ax=ax, palette="rocket")
        ax.set_title(f"At-risk rate by {col}")
        ax.set_ylim(0, 1)
        ax.set_ylabel("P(at-risk)")
    fig.suptitle("Categorical risk rates", fontsize=18)
    _save(fig, "05_categorical_risk.png")


def main(force_download: bool = False) -> None:
    df = add_target(load_raw(force_download=force_download))
    logger.info("Loaded %d rows. At-risk rate = %.2f%%", len(df), 100 * df[TARGET_COL].mean())
    plot_target_balance(df)
    plot_grade_distribution(df)
    plot_correlation(df)
    plot_feature_vs_target(df)
    plot_categorical_risk(df)
    logger.info("EDA complete. Figures in %s", REPORTS_DIR)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-download", action="store_true")
    args = parser.parse_args()
    main(force_download=args.force_download)
