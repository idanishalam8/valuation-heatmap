# ─────────────────────────────────────────────────────────────────────────────
# visuals.py  ·  Chart generation layer
#   · draw_heatmap()           → seaborn + matplotlib heat map
#   · draw_ranking_chart()     → plotly horizontal bar (composite score)
#   · draw_history_chart()     → plotly time-series with bands + current marker
#   · draw_sector_spider()     → plotly radar/spider for sector summary
# ─────────────────────────────────────────────────────────────────────────────

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from datetime import date
from src.config import METRIC_LABELS, ZONES, ZONE_COLORS

METRICS_DISPLAY = ["pe", "pb", "ev_ebitda", "div_yield"]

# ── Color scale: Green (cheap) → Yellow (fair) → Red (expensive) ──────────────
HEAT_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "richness",
    [(0.0,  "#1a7a4a"),   # 0   very cheap
     (0.20, "#5DCAA5"),   # 20  cheap
     (0.50, "#f5f0e8"),   # 50  fair (neutral off-white)
     (0.80, "#EF9F27"),   # 80  expensive
     (1.00, "#c0392b")],  # 100 very expensive
)


def draw_heatmap(
    pct_matrix:  pd.DataFrame,
    zscore_matrix: pd.DataFrame | None = None,
    title_date:  str = None,
    figsize: tuple = (14, 7),
) -> plt.Figure:
    """
    Draw the sector × metric heat map.

    Color  = richness percentile (green=cheap, red=expensive)
    Number = percentile value (0–100)
    Sub-number (small) = Z-Score if zscore_matrix provided
    """
    # Prepare display matrix
    display = pct_matrix[METRICS_DISPLAY].copy()
    display.columns = [METRIC_LABELS.get(c, c) for c in display.columns]
    display.index   = [s.replace("Nifty ","") for s in display.index]

    # Annotation strings
    annot = display.copy().astype(object)
    for r in display.index:
        for c in display.columns:
            val = display.loc[r, c]
            if pd.isna(val):
                annot.loc[r, c] = "—"
            else:
                annot.loc[r, c] = f"{int(round(val))}"

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#0f1117")

    sns.heatmap(
        display.astype(float),
        annot=annot,
        fmt="",
        cmap=HEAT_CMAP,
        vmin=0, vmax=100, center=50,
        linewidths=1.2, linecolor="#1e2228",
        annot_kws={"size": 13, "weight": "bold", "color": "white"},
        cbar_kws={"shrink": 0.6, "pad": 0.02},
        ax=ax,
        square=False,
    )

    # Style axes
    ax.set_xticklabels(ax.get_xticklabels(), color="white", fontsize=11, fontweight="bold")
    ax.set_yticklabels(ax.get_yticklabels(), color="#cccccc", fontsize=10, rotation=0)
    ax.tick_params(colors="white", left=False, bottom=False)

    # Color bar label
    cbar = ax.collections[0].colorbar
    cbar.set_label("Historical percentile rank  →  0 = cheapest  |  100 = most expensive",
                   color="white", fontsize=9)
    cbar.ax.yaxis.set_tick_params(color="white")
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white", fontsize=8)

    # Title
    date_str = title_date or date.today().strftime("%B %Y")
    ax.set_title(
        f"NSE Sector Valuation Heat Map  ·  {date_str}",
        color="white", fontsize=14, fontweight="bold", pad=16,
    )

    # Add legend strip for zones
    zone_text = "  |  ".join(
        [f"■ {label}" for label in list(ZONES.keys())]
    )
    fig.text(0.5, 0.01, zone_text, ha="center", fontsize=8,
             color="#aaaaaa", style="italic")

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    return fig


def draw_ranking_chart(richness_series: pd.Series) -> go.Figure:
    """
    Horizontal bar chart: sectors ranked from cheapest (left) to most expensive (right).
    Color = zone color.
    """
    df = richness_series.reset_index()
    df.columns = ["Sector", "Score"]
    df["Sector_short"] = df["Sector"].str.replace("Nifty ", "")
    df["Color"] = df["Score"].apply(_score_to_color)
    df["Label"] = df["Score"].apply(lambda s: interpret_zone(s)[0])

    fig = go.Figure()
    for _, row in df.iterrows():
        fig.add_trace(go.Bar(
            x=[row["Score"]],
            y=[row["Sector_short"]],
            orientation="h",
            marker_color=row["Color"],
            text=f"{row['Score']:.0f}",
            textposition="outside",
            textfont=dict(size=11, color="white"),
            hovertemplate=(
                f"<b>{row['Sector']}</b><br>"
                f"Richness Score: {row['Score']:.1f} / 100<br>"
                f"Zone: {row['Label']}<extra></extra>"
            ),
            name=row["Label"],
            showlegend=False,
        ))

    # Fair value reference line
    fig.add_vline(x=50, line_dash="dot", line_color="rgba(255,255,255,0.35)",
                  annotation_text="Fair value (50)", annotation_position="top right",
                  annotation_font=dict(color="rgba(255,255,255,0.6)", size=10))

    # Zone shading
    fig.add_vrect(x0=0,  x1=35,  fillcolor="#1a7a4a", opacity=0.06, layer="below", line_width=0)
    fig.add_vrect(x0=65, x1=100, fillcolor="#c0392b", opacity=0.06, layer="below", line_width=0)

    fig.update_layout(
        title=dict(text="Sector Composite Richness Ranking", font=dict(color="white", size=14)),
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
        xaxis=dict(range=[0, 115], showgrid=True, gridcolor="#222",
                   tickfont=dict(color="white"), title="Richness Score (0 = cheapest ← → 100 = most expensive)",
                   title_font=dict(color="#aaa", size=11)),
        yaxis=dict(tickfont=dict(color="white"), autorange="reversed"),
        height=420,
        margin=dict(l=10, r=60, t=50, b=40),
    )
    return fig


def draw_history_chart(
    sector:       str,
    metric:       str,
    hist_df:      pd.DataFrame,
    current_val:  float | None,
    years:        int = 10,
) -> go.Figure:
    """
    10-year time series for a sector + metric with:
     · Main line (history)
     · Shaded fair-value band (25th–75th percentile)
     · Current value horizontal dashed line
     · Percentile rank annotation
    """
    # Get the metric column
    col_map = {"pe": "pe", "pb": "pb", "ev_ebitda": "ev_ebitda", "div_yield": "div_yield"}
    col     = col_map.get(metric, metric)

    date_col = "date" if "date" in hist_df.columns else hist_df.columns[0]
    hist_df  = hist_df.copy()
    hist_df[date_col] = pd.to_datetime(hist_df[date_col], errors="coerce")
    cutoff   = pd.Timestamp.today() - pd.DateOffset(years=years)
    hist_df  = hist_df[hist_df[date_col] >= cutoff]

    if col not in hist_df.columns:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
            title=dict(text="No data available", font=dict(color="white")),
        )
        return fig

    y_vals = pd.to_numeric(hist_df[col], errors="coerce")
    x_vals = hist_df[date_col]

    p25  = float(np.nanpercentile(y_vals, 25))
    p50  = float(np.nanpercentile(y_vals, 50))
    p75  = float(np.nanpercentile(y_vals, 75))

    fig  = go.Figure()

    # Fair value band
    fig.add_trace(go.Scatter(
        x=list(x_vals) + list(x_vals)[::-1],
        y=[p75]*len(x_vals) + [p25]*len(x_vals),
        fill="toself", fillcolor="rgba(74,140,106,0.12)",
        line=dict(width=0), name="25th–75th pct (fair zone)",
        hoverinfo="skip", showlegend=True,
    ))

    # Median line (dashed)
    fig.add_hline(y=p50, line_dash="dash", line_color="rgba(74,140,106,0.5)",
                  line_width=1)

    # Historical line
    fig.add_trace(go.Scatter(
        x=x_vals, y=y_vals,
        mode="lines", name="Historical",
        line=dict(color="#4a7fb5", width=1.8),
        hovertemplate="%{x|%b %Y}: %{y:.1f}x<extra></extra>",
    ))

    # Current value line
    if current_val and not np.isnan(current_val):
        from scipy import stats as spstats
        arr = y_vals.dropna().values
        pct = spstats.percentileofscore(arr, current_val, kind="rank")
        zone_label, zone_color = interpret_zone(pct)

        fig.add_hline(
            y=current_val, line_dash="solid", line_color=zone_color, line_width=2.5,
            annotation_text=f"  Today: {current_val:.1f}x  ({pct:.0f}th pct · {zone_label})",
            annotation_position="top left",
            annotation_font=dict(color=zone_color, size=11),
        )

    metric_label = METRIC_LABELS.get(metric, metric)
    sector_short = sector.replace("Nifty ", "")

    fig.update_layout(
        title=dict(
            text=f"{sector_short}  ·  {metric_label}  ·  {years}-Year History",
            font=dict(color="white", size=13),
        ),
        paper_bgcolor="#0f1117",
        plot_bgcolor="#161b22",
        xaxis=dict(
            showgrid=True, gridcolor="#1e2228",
            tickfont=dict(color="#aaa"), title_font=dict(color="#aaa"),
            rangeslider=dict(visible=False),
        ),
        yaxis=dict(
            showgrid=True, gridcolor="#1e2228",
            tickfont=dict(color="#aaa"),
            title=f"{metric_label}", title_font=dict(color="#aaa", size=11),
        ),
        legend=dict(font=dict(color="white"), bgcolor="rgba(0,0,0,0)"),
        height=340,
        margin=dict(l=10, r=20, t=50, b=30),
        hovermode="x unified",
    )
    return fig


def draw_spider_chart(pct_row: pd.Series, sector: str) -> go.Figure:
    """Radar chart showing the 4 metric percentiles for a sector."""
    metrics = METRICS_DISPLAY
    labels  = [METRIC_LABELS.get(m, m) for m in metrics]
    values  = [float(pct_row.get(m, 50) or 50) for m in metrics]
    values  += values[:1]  # close the polygon
    labels  += labels[:1]

    fig = go.Figure(go.Scatterpolar(
        r=values, theta=labels,
        fill="toself",
        fillcolor="rgba(74,127,181,0.2)",
        line=dict(color="#4a7fb5", width=2),
        name=sector.replace("Nifty ",""),
    ))

    # Add 50-line reference
    ref = [50] * len(labels)
    fig.add_trace(go.Scatterpolar(
        r=ref, theta=labels,
        mode="lines", line=dict(color="rgba(255,255,255,0.2)", dash="dot", width=1),
        name="Fair value", hoverinfo="skip",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(color="#888", size=9),
                            gridcolor="#222"),
            angularaxis=dict(tickfont=dict(color="white", size=11), gridcolor="#222"),
            bgcolor="#0f1117",
        ),
        paper_bgcolor="#0f1117",
        showlegend=False,
        height=280,
        margin=dict(l=30, r=30, t=30, b=30),
    )
    return fig


# ── Helpers ────────────────────────────────────────────────────────────────────

def _score_to_color(score: float) -> str:
    for label, (lo, hi) in ZONES.items():
        if lo <= score < hi:
            return ZONE_COLORS[label]
    return ZONE_COLORS["Fair"]


def interpret_zone(score: float) -> tuple[str, str]:
    for label, (lo, hi) in ZONES.items():
        if lo <= score < hi:
            return label, ZONE_COLORS[label]
    return "Fair", ZONE_COLORS["Fair"]
