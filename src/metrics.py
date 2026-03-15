# ─────────────────────────────────────────────────────────────────────────────
# metrics.py  ·  Data cleaning + sector-level aggregation
# ─────────────────────────────────────────────────────────────────────────────

import numpy as np
import pandas as pd
from src.config import SECTORS, METRIC_LABELS

NUMERIC_COLS = ["pe", "pb", "ev_ebitda", "div_yield"]

# Per-metric validation bounds (values outside these are treated as errors)
VALID_BOUNDS = {
    "pe":        (0.5,  150),
    "pb":        (0.1,   60),
    "ev_ebitda": (0.5,   80),
    "div_yield": (0.0,   20),
}


def clean_company_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean raw yfinance output:
     1. Cast all metric columns to numeric
     2. Drop rows where ALL metrics are missing
     3. Remove negative P/E (loss-making — uninformative)
     4. Clip extreme outliers using VALID_BOUNDS
    """
    df = df.copy()
    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows with all metrics missing
    df = df.dropna(subset=NUMERIC_COLS, how="all")

    # Remove negative P/E
    df.loc[df["pe"] < 0, "pe"] = np.nan

    # Clip bounds
    for col, (lo, hi) in VALID_BOUNDS.items():
        if col in df.columns:
            df[col] = df[col].clip(lower=lo, upper=hi)
            df.loc[df[col] <= lo, col] = np.nan   # below lower = invalid

    return df


def aggregate_to_sector(df_all: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse company-level DataFrame (all sectors combined) into sector medians.

    Returns DataFrame indexed by sector name with columns: pe, pb, ev_ebitda, div_yield.
    Uses MEDIAN (not mean) — robust against outliers.
    """
    df_clean = clean_company_data(df_all)

    sector_df = (
        df_clean
        .groupby("sector")[NUMERIC_COLS]
        .median()
    )
    sector_df.index.name = "sector"
    return sector_df


def get_sector_detail(df_all: pd.DataFrame, sector_name: str) -> pd.DataFrame:
    """Return cleaned company-level data for a single sector."""
    sub = df_all[df_all["sector"] == sector_name].copy()
    return clean_company_data(sub)


def label_metric(metric_key: str) -> str:
    return METRIC_LABELS.get(metric_key, metric_key)


def describe_sector_multiples(row: pd.Series) -> dict:
    """Return human-readable descriptions for sector multiples."""
    return {
        "P/E":        f"{row['pe']:.1f}x" if not pd.isna(row.get("pe")) else "N/A",
        "P/BV":       f"{row['pb']:.2f}x" if not pd.isna(row.get("pb")) else "N/A",
        "EV/EBITDA":  f"{row['ev_ebitda']:.1f}x" if not pd.isna(row.get("ev_ebitda")) else "N/A",
        "Div Yield":  f"{row['div_yield']:.2f}%" if not pd.isna(row.get("div_yield")) else "N/A",
    }
