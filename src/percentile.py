# ─────────────────────────────────────────────────────────────────────────────
# percentile.py  ·  Core statistical ranking engine
#   · Historical percentile rank (scipy.stats.percentileofscore)
#   · Z-Score for secondary signal
#   · Composite Richness Score (weighted average of metric percentiles)
#   · Interpretation labelling
# ─────────────────────────────────────────────────────────────────────────────

import numpy as np
import pandas as pd
from scipy import stats
from src.config import (
    SECTORS, DEFAULT_WEIGHTS, SECTOR_WEIGHTS,
    ZONES, ZONE_COLORS,
)

# Metrics where HIGHER value = CHEAPER (invert percentile)
INVERTED_METRICS = {"div_yield"}

NUMERIC_COLS = ["pe", "pb", "ev_ebitda", "div_yield"]


def _get_hist_series(hist_df: pd.DataFrame, metric: str) -> np.ndarray:
    """Extract clean numpy array from historical DataFrame for a metric."""
    col_map = {
        "pe":        ["pe", "p/e", "pe_ratio"],
        "pb":        ["pb", "p/b", "p/bv", "pb_ratio"],
        "ev_ebitda": ["ev_ebitda", "ev/ebitda"],
        "div_yield": ["div_yield", "dividend_yield", "div yield"],
    }
    for candidate in col_map.get(metric, [metric]):
        for col in hist_df.columns:
            if col.lower().replace(" ","_") == candidate.replace(" ","_"):
                arr = pd.to_numeric(hist_df[col], errors="coerce").dropna().values
                return arr[arr > 0]
    return np.array([])


def percentile_rank(current_value: float, historical_array: np.ndarray) -> float | None:
    """
    Compute what % of historical observations are BELOW current_value.
    Returns value in [0, 100]. Returns None if data insufficient.
    """
    if current_value is None or np.isnan(current_value):
        return None
    if len(historical_array) < 20:
        return None
    return round(stats.percentileofscore(historical_array, current_value, kind="rank"), 1)


def z_score(current_value: float, historical_array: np.ndarray) -> float | None:
    """Standard deviations above/below the historical mean."""
    if current_value is None or np.isnan(current_value):
        return None
    if len(historical_array) < 20:
        return None
    mu    = historical_array.mean()
    sigma = historical_array.std()
    if sigma == 0:
        return 0.0
    return round((current_value - mu) / sigma, 2)


def richness_percentile(raw_pct: float, metric: str) -> float | None:
    """
    Convert raw percentile to a 'richness' score where:
      100 = most expensive in history (always)
      0   = cheapest in history (always)

    For inverted metrics (div_yield): higher yield = cheaper, so invert.
    """
    if raw_pct is None:
        return None
    if metric in INVERTED_METRICS:
        return round(100 - raw_pct, 1)
    return raw_pct


def build_percentile_matrix(
    current_sector_df: pd.DataFrame,
    historical_dict:   dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Build the 12 × 4 percentile matrix.

    Parameters
    ----------
    current_sector_df : sector-level median multiples (from metrics.aggregate_to_sector)
    historical_dict   : {sector_name: historical DataFrame}

    Returns
    -------
    DataFrame indexed by sector, columns = [pe, pb, ev_ebitda, div_yield]
    Values are richness percentiles (0=cheapest, 100=most expensive).
    """
    matrix = pd.DataFrame(
        index=list(SECTORS.keys()),
        columns=NUMERIC_COLS,
        dtype=float,
    )

    for sector in SECTORS:
        if sector not in historical_dict:
            continue
        hist_df = historical_dict[sector]

        for metric in NUMERIC_COLS:
            hist_arr = _get_hist_series(hist_df, metric)
            try:
                curr_val = float(current_sector_df.loc[sector, metric])
            except (KeyError, TypeError, ValueError):
                curr_val = None

            raw   = percentile_rank(curr_val, hist_arr)
            rich  = richness_percentile(raw, metric)
            matrix.loc[sector, metric] = rich

    return matrix


def build_zscore_matrix(
    current_sector_df: pd.DataFrame,
    historical_dict:   dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Same shape as percentile matrix but contains Z-Scores."""
    zmat = pd.DataFrame(index=list(SECTORS.keys()), columns=NUMERIC_COLS, dtype=float)

    for sector in SECTORS:
        if sector not in historical_dict:
            continue
        hist_df = historical_dict[sector]
        for metric in NUMERIC_COLS:
            hist_arr = _get_hist_series(hist_df, metric)
            try:
                curr_val = float(current_sector_df.loc[sector, metric])
            except (KeyError, TypeError, ValueError):
                curr_val = None
            z = z_score(curr_val, hist_arr)
            # Invert for div_yield
            if z is not None and metric in INVERTED_METRICS:
                z = -z
            zmat.loc[sector, metric] = z

    return zmat


def composite_richness_score(
    pct_matrix: pd.DataFrame,
    sector:     str,
) -> float | None:
    """
    Weighted average of available metric percentiles for a sector.
    Uses sector-specific weights if defined.
    Returns a score in [0, 100] or None if no data.
    """
    weights = SECTOR_WEIGHTS.get(sector, DEFAULT_WEIGHTS)
    total_w = 0.0
    total_s = 0.0

    for metric, w in weights.items():
        val = pct_matrix.loc[sector, metric] if sector in pct_matrix.index else None
        if val is not None and not (isinstance(val, float) and np.isnan(val)):
            total_s += float(val) * w
            total_w += w

    if total_w == 0:
        return None
    return round(total_s / total_w, 1)


def build_richness_series(pct_matrix: pd.DataFrame) -> pd.Series:
    """
    Returns Series: sector → Composite Richness Score (0–100).
    Sorted ascending (cheapest first).
    """
    scores = {}
    for sector in pct_matrix.index:
        scores[sector] = composite_richness_score(pct_matrix, sector)
    return pd.Series(scores, name="richness").dropna().sort_values()


def interpret_score(score: float) -> tuple[str, str]:
    """Returns (zone_label, hex_color)."""
    for label, (lo, hi) in ZONES.items():
        if lo <= score < hi:
            return label, ZONE_COLORS[label]
    return "Fair", ZONE_COLORS["Fair"]


def sector_stats_table(
    sector:      str,
    current_row: pd.Series,
    hist_df:     pd.DataFrame,
    pct_row:     pd.Series,
) -> pd.DataFrame:
    """Build a summary stats table for the sector drill-down view."""
    rows = []
    for metric in NUMERIC_COLS:
        hist_arr = _get_hist_series(hist_df, metric)
        curr     = float(current_row[metric]) if not pd.isna(current_row.get(metric)) else None
        pct      = pct_row.get(metric)
        z        = z_score(curr, hist_arr) if curr and len(hist_arr) > 20 else None

        if len(hist_arr) > 20:
            lo, hi, med, avg = hist_arr.min(), hist_arr.max(), np.median(hist_arr), hist_arr.mean()
            p25, p75 = np.percentile(hist_arr, 25), np.percentile(hist_arr, 75)
        else:
            lo = hi = med = avg = p25 = p75 = None

        from src.config import METRIC_LABELS
        rows.append({
            "Metric":    METRIC_LABELS.get(metric, metric),
            "Current":   f"{curr:.1f}" if curr else "N/A",
            "10Y Low":   f"{lo:.1f}"   if lo   else "N/A",
            "10Y Median":f"{med:.1f}"  if med  else "N/A",
            "10Y High":  f"{hi:.1f}"   if hi   else "N/A",
            "Pct Rank":  f"{pct:.0f}th" if pct else "N/A",
            "Z-Score":   f"{z:+.2f}"   if z    else "N/A",
        })
    return pd.DataFrame(rows)
