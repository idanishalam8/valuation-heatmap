# ─────────────────────────────────────────────────────────────────────────────
# app.py  ·  NSE Sector Valuation Heat Map  ·  Streamlit Dashboard
# ─────────────────────────────────────────────────────────────────────────────
#
#  Layout:
#   Sidebar  →  controls (lookback, metric filter, refresh)
#   Tab 1    →  Heat Map  (seaborn, full 12×4 matrix)
#   Tab 2    →  Sector Ranking  (plotly bar, composite score)
#   Tab 3    →  Sector Deep Dive  (select sector → history chart + stats table + radar)
#   Tab 4    →  Methodology  (explanatory)
#
# ─────────────────────────────────────────────────────────────────────────────

import os, time, warnings
import numpy as np
import pandas as pd
import streamlit as st
from datetime import date

warnings.filterwarnings("ignore")

# Page config — must be first Streamlit call
st.set_page_config(
    page_title="NSE Sector Valuation Heat Map",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com",
        "About":    "NSE Sector Valuation Heat Map · Built with Python + Streamlit",
    },
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Dark financial theme */
body, .stApp { background-color: #0f1117; color: #e8e6e0; }
[data-testid="stSidebar"] { background-color: #111316; border-right: 1px solid #1e2228; }
[data-testid="stSidebar"] * { color: #cccccc !important; }
.stTabs [data-baseweb="tab-list"] { background-color: #111316; border-bottom: 1px solid #1e2228; }
.stTabs [data-baseweb="tab"] { color: #888; font-size: 13px; font-weight: 500; }
.stTabs [aria-selected="true"] { color: white !important; border-bottom: 2px solid #c9a84c !important; }
.metric-card {
    background: #111316; border: 1px solid #1e2228; border-radius: 8px;
    padding: 14px 16px; text-align: center;
}
.metric-card .label { font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: .1em; margin-bottom: 4px; }
.metric-card .value { font-size: 22px; font-weight: 500; }
.zone-badge {
    display: inline-block; padding: 3px 10px; border-radius: 10px;
    font-size: 11px; font-weight: 600; letter-spacing: .04em;
}
h1,h2,h3 { color: #e8e6e0 !important; }
.stDataFrame { background: #111316 !important; }
.stButton button { background: #c9a84c; color: #0f1117; font-weight: 600; border: none; }
.stButton button:hover { background: #e8c96a; }
hr { border-color: #1e2228; }
p, li { color: #aaa; }
</style>
""", unsafe_allow_html=True)

# ── Lazy imports (after page config) ──────────────────────────────────────────
from src.config import SECTORS, LOOKBACK_OPTIONS, METRIC_LABELS, ZONE_COLORS
from src.fetch import (
    fetch_all_sectors_current,
    fetch_all_historical,
    load_all_historical_from_cache,
    clear_cache,
)
from src.metrics import aggregate_to_sector, describe_sector_multiples
from src.percentile import (
    build_percentile_matrix,
    build_zscore_matrix,
    build_richness_series,
    composite_richness_score,
    interpret_score,
    sector_stats_table,
)
from src.visuals import (
    draw_heatmap,
    draw_ranking_chart,
    draw_history_chart,
    draw_spider_chart,
    interpret_zone,
)

SECTOR_NAMES = list(SECTORS.keys())
METRICS      = ["pe", "pb", "ev_ebitda", "div_yield"]


# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING  (cached with st.session_state to avoid re-fetching on every
# widget interaction)
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=14400, show_spinner=False)   # 4-hour cache
def load_current_data():
    return fetch_all_sectors_current()


@st.cache_data(ttl=86400, show_spinner=False)   # 24-hour cache
def load_historical_data(years: int):
    # Try loading from disk cache first
    cached = load_all_historical_from_cache(years)
    if cached:
        return cached
    return fetch_all_historical(years)


def get_sector_df(years: int):
    """Returns (current_sector_df, historical_dict, pct_matrix, zscore_matrix, richness_series)."""
    with st.spinner("Loading market data…"):
        raw_company_df = load_current_data()
        historical     = load_historical_data(years)

    current_sector_df = aggregate_to_sector(raw_company_df)
    pct_matrix        = build_percentile_matrix(current_sector_df, historical)
    zscore_matrix     = build_zscore_matrix(current_sector_df, historical)
    richness_series   = build_richness_series(pct_matrix)

    return current_sector_df, historical, pct_matrix, zscore_matrix, richness_series


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style='padding:12px 0 18px'>
      <div style='font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#c9a84c;margin-bottom:6px'>NSE Sector Intelligence</div>
      <div style='font-size:17px;font-weight:500;color:white;line-height:1.3'>Valuation<br>Heat Map</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    lookback_label = st.selectbox(
        "Historical lookback",
        options=list(LOOKBACK_OPTIONS.keys()),
        index=2,
        help="How many years of history to use for percentile calculation",
    )
    years = LOOKBACK_OPTIONS[lookback_label]

    st.markdown("")
    selected_metrics = st.multiselect(
        "Metrics to display",
        options=METRICS,
        default=METRICS,
        format_func=lambda m: METRIC_LABELS.get(m, m),
        help="Choose which valuation multiples appear in the heat map",
    )
    if not selected_metrics:
        selected_metrics = METRICS

    st.divider()

    st.markdown("##### Filters")
    min_score, max_score = st.slider(
        "Richness score range",
        min_value=0, max_value=100,
        value=(0, 100),
        help="Show only sectors within this richness band",
    )

    st.divider()

    if st.button("🔄  Refresh data", use_container_width=True):
        clear_cache()
        st.cache_data.clear()
        st.success("Cache cleared. Data will re-fetch.")
        time.sleep(1)
        st.rerun()

    st.markdown("""
    <div style='margin-top:24px;font-size:11px;color:#444'>
      <div style='color:#666;margin-bottom:4px'>Data sources</div>
      NSE India · yfinance API<br>
      <span style='color:#555'>Updated: """ + date.today().strftime("%d %b %Y") + """</span>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════════════════════

current_sector_df, historical, pct_matrix, zscore_matrix, richness_series = get_sector_df(years)

# Apply richness filter to ranking
filtered_richness = richness_series[
    (richness_series >= min_score) & (richness_series <= max_score)
]


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<div style='padding:8px 0 20px'>
  <div style='font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#c9a84c;margin-bottom:8px'>
    Equity Research Tool · {date.today().strftime('%B %Y')}
  </div>
  <div style='font-size:26px;font-weight:500;color:white;line-height:1.2;margin-bottom:6px'>
    NSE Sector Valuation Heat Map
  </div>
  <div style='font-size:13px;color:#888'>
    Historical percentile ranking across 12 sectors  ·  {lookback_label} lookback  ·
    P/E, P/BV, EV/EBITDA, Dividend Yield
  </div>
</div>
""", unsafe_allow_html=True)

# ── Summary metric cards ───────────────────────────────────────────────────────
if len(richness_series) > 0:
    cheapest   = richness_series.idxmin().replace("Nifty ","")
    expensive  = richness_series.idxmax().replace("Nifty ","")
    avg_rich   = richness_series.mean()
    n_cheap    = (richness_series < 35).sum()
    n_exp      = (richness_series > 65).sum()
    zone_label, zone_color = interpret_score(avg_rich)

    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        (c1, "Market Richness", f"{avg_rich:.0f}/100", zone_color),
        (c2, "Cheapest Sector", cheapest, "#5DCAA5"),
        (c3, "Most Expensive",  expensive, "#EF9F27"),
        (c4, "Cheap Sectors",   f"{n_cheap} / 12", "#5DCAA5"),
        (c5, "Exp. Sectors",    f"{n_exp} / 12",   "#E24B4A"),
    ]
    for col, label, val, color in cards:
        with col:
            st.markdown(f"""
            <div class='metric-card'>
              <div class='label'>{label}</div>
              <div class='value' style='color:{color}'>{val}</div>
            </div>""", unsafe_allow_html=True)

st.markdown("")


# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs([
    "📊  Heat Map",
    "📈  Sector Ranking",
    "🔍  Deep Dive",
    "📖  Methodology",
])


# ────────────────────────────────────────────────────────────────────────────
# TAB 1 · HEAT MAP
# ────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("")

    # Filter matrix to selected metrics
    display_pct = pct_matrix[selected_metrics].copy() if selected_metrics else pct_matrix.copy()

    fig_hm = draw_heatmap(
        display_pct,
        zscore_matrix[selected_metrics] if selected_metrics else zscore_matrix,
        title_date=date.today().strftime("%B %Y"),
    )
    st.pyplot(fig_hm, use_container_width=True)

    # Colour legend
    st.markdown("")
    leg_cols = st.columns(5)
    for i, (zone, color) in enumerate(ZONE_COLORS.items()):
        with leg_cols[i]:
            st.markdown(
                f"<div style='text-align:center'>"
                f"<span class='zone-badge' style='background:{color}22;color:{color};border:1px solid {color}55'>"
                f"{zone}</span></div>",
                unsafe_allow_html=True,
            )

    # Raw data expander
    with st.expander("Show raw percentile data"):
        styled = (
            display_pct
            .rename(columns=METRIC_LABELS)
            .rename(index=lambda s: s.replace("Nifty ",""))
            .style
            .background_gradient(cmap="RdYlGn_r", vmin=0, vmax=100, axis=None)
            .format("{:.0f}", na_rep="—")
        )
        st.dataframe(styled, use_container_width=True)

    with st.expander("Show current sector multiples"):
        raw_display = (
            current_sector_df
            .rename(columns=METRIC_LABELS)
            .rename(index=lambda s: s.replace("Nifty ",""))
            .style.format("{:.2f}", na_rep="N/A")
        )
        st.dataframe(raw_display, use_container_width=True)


# ────────────────────────────────────────────────────────────────────────────
# TAB 2 · SECTOR RANKING
# ────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("")

    if len(filtered_richness) == 0:
        st.warning("No sectors match the current richness filter. Adjust the slider in the sidebar.")
    else:
        fig_rank = draw_ranking_chart(filtered_richness)
        st.plotly_chart(fig_rank, use_container_width=True)

        st.markdown("##### Sector Score Table")
        rows = []
        for sector in filtered_richness.index:
            score  = filtered_richness[sector]
            zone, color = interpret_score(score)
            mults  = current_sector_df.loc[sector] if sector in current_sector_df.index else pd.Series()
            desc   = describe_sector_multiples(mults)
            rows.append({
                "Sector":     sector.replace("Nifty ",""),
                "Score":      f"{score:.0f} / 100",
                "Zone":       zone,
                "P/E":        desc.get("P/E","N/A"),
                "P/BV":       desc.get("P/BV","N/A"),
                "EV/EBITDA":  desc.get("EV/EBITDA","N/A"),
                "Div Yield":  desc.get("Div Yield","N/A"),
            })

        df_table = pd.DataFrame(rows)
        st.dataframe(
            df_table.style.applymap(
                lambda v: "color: #5DCAA5" if "Cheap" in str(v) else
                          ("color: #E24B4A" if "Expensive" in str(v) else ""),
                subset=["Zone"],
            ),
            use_container_width=True,
            hide_index=True,
        )


# ────────────────────────────────────────────────────────────────────────────
# TAB 3 · DEEP DIVE
# ────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("")

    col_sel, col_met = st.columns([1, 1])
    with col_sel:
        sel_sector = st.selectbox(
            "Select sector",
            options=SECTOR_NAMES,
            format_func=lambda s: s.replace("Nifty ",""),
            index=0,
        )
    with col_met:
        sel_metric = st.selectbox(
            "Select metric",
            options=METRICS,
            format_func=lambda m: METRIC_LABELS.get(m, m),
            index=0,
        )

    st.markdown("")

    # Top summary row for the selected sector
    if sel_sector in pct_matrix.index:
        pct_row  = pct_matrix.loc[sel_sector]
        score    = composite_richness_score(pct_matrix, sel_sector)
        zone_lbl, zone_col = interpret_score(score or 50)

        sc1, sc2, sc3, sc4, sc5 = st.columns(5)
        mults = current_sector_df.loc[sel_sector] if sel_sector in current_sector_df.index else pd.Series()

        sc1.markdown(f"""<div class='metric-card'>
          <div class='label'>Richness Score</div>
          <div class='value' style='color:{zone_col}'>{score:.0f}</div>
        </div>""", unsafe_allow_html=True)

        for col_ui, (mk, ml) in zip([sc2,sc3,sc4,sc5], [
            ("pe","P/E"),("pb","P/BV"),("ev_ebitda","EV/EBITDA"),("div_yield","Div Yield")
        ]):
            val = mults.get(mk)
            pct = pct_row.get(mk)
            _, pcolor = interpret_score(pct or 50)
            disp  = f"{val:.1f}" if (val and not pd.isna(val)) else "N/A"
            col_ui.markdown(f"""<div class='metric-card'>
              <div class='label'>{ml}</div>
              <div class='value' style='color:{pcolor}'>{disp}</div>
              <div style='font-size:10px;color:#555;margin-top:2px'>{pct:.0f}th pct</div>
            </div>""" if (pct and not pd.isna(pct)) else f"""<div class='metric-card'>
              <div class='label'>{ml}</div>
              <div class='value'>{disp}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("")

    # History chart + spider side by side
    chart_col, spider_col = st.columns([2, 1])

    with chart_col:
        curr_val = None
        if sel_sector in current_sector_df.index:
            v = current_sector_df.loc[sel_sector, sel_metric]
            curr_val = float(v) if not pd.isna(v) else None

        if sel_sector in historical:
            fig_hist = draw_history_chart(
                sel_sector, sel_metric,
                historical[sel_sector],
                curr_val, years,
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Historical data not available for this sector.")

    with spider_col:
        if sel_sector in pct_matrix.index:
            fig_spider = draw_spider_chart(pct_matrix.loc[sel_sector], sel_sector)
            st.markdown("<div style='padding-top:8px'></div>", unsafe_allow_html=True)
            st.plotly_chart(fig_spider, use_container_width=True)

    # Detailed stats table
    st.markdown("##### Detailed statistics")
    if sel_sector in current_sector_df.index and sel_sector in historical:
        stats_df = sector_stats_table(
            sel_sector,
            current_sector_df.loc[sel_sector],
            historical[sel_sector],
            pct_matrix.loc[sel_sector] if sel_sector in pct_matrix.index else pd.Series(),
        )
        st.dataframe(
            stats_df.style.applymap(
                lambda v: "color: #E24B4A" if (isinstance(v, str) and int(v.replace("th","")) > 70
                           if v.endswith("th") and v.replace("th","").isdigit() else False)
                          else ("color: #5DCAA5" if (isinstance(v, str) and v.endswith("th")
                           and v.replace("th","").isdigit() and int(v.replace("th","")) < 30) else ""),
                subset=["Pct Rank"],
            ),
            hide_index=True,
            use_container_width=True,
        )


# ────────────────────────────────────────────────────────────────────────────
# TAB 4 · METHODOLOGY
# ────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("")
    st.markdown("""
## How this tool works

### What it measures
This dashboard answers one question: **is each Indian stock market sector cheap or expensive right now, relative to its own history?**

Rather than showing raw valuation multiples (which are hard to interpret without context), every cell in the heat map shows a **historical percentile rank** — how today's multiple compares to the full distribution of values over the past 5–10 years.

---

### The 4 valuation multiples

| Multiple | Formula | Best used for |
|---|---|---|
| **P/E** | Price ÷ Earnings per share | IT, FMCG, Consumer, Pharma |
| **P/BV** | Price ÷ Book Value per share | Banks, Financial Services |
| **EV/EBITDA** | Enterprise Value ÷ Operating Cash Profit | Metals, Energy, Infra |
| **Dividend Yield** | Annual Dividend ÷ Price × 100 | Energy, Banks (inverted) |

---

### The percentile rank calculation

For every sector × multiple cell:

```python
from scipy import stats
percentile = stats.percentileofscore(historical_10yr_array, today_value)
# 0 = cheapest in history    50 = fair value    100 = most expensive in history
```

**Dividend Yield is inverted**: high yield = cheap (not expensive), so:
```python
richness_score = 100 − percentileofscore(historical_yield, today_yield)
```

---

### Composite Richness Score (0–100)

Each sector gets one overall score — a weighted average of its 4 metric percentiles:

| Metric | Default weight | Bank/NBFC override |
|---|---|---|
| P/E | 35% | 15% |
| EV/EBITDA | 30% | 5% |
| P/BV | 25% | 60% |
| Div Yield | 10% | 20% |

Banks use a P/BV-heavy weight because their earnings are volatile but asset quality (captured in P/BV) is the more reliable signal.

---

### Data sources

- **Current multiples**: Yahoo Finance via `yfinance` Python library
- **Historical index data**: NSE India's official P/E, P/BV, Div Yield series
  (downloadable from NSE website → Indices → Historical Data)
- **Aggregation**: Company-level multiples are collapsed to sector medians
  (median is used, not mean, to neutralise outlier distortion)

---

### Interpretation guide

| Score range | Zone | Interpretation |
|---|---|---|
| 0 – 20 | Very Cheap | Historically cheap — potentially strong value entry point |
| 20 – 35 | Cheap | Below-average valuation — watch for catalysts |
| 35 – 65 | Fair | Near historical norms — sector is fairly priced |
| 65 – 80 | Expensive | Above average — elevated expectations priced in |
| 80 – 100 | Very Expensive | Near historical peaks — requires strong earnings delivery |

> **Important**: Valuation alone is not a trading signal. A sector can remain expensive for extended periods if earnings growth justifies it. This tool provides *context*, not *direction*.

---

### Technical stack

```
Python 3.11
├── yfinance        → market data API
├── pandas / numpy  → data manipulation
├── scipy           → percentileofscore, z-score
├── seaborn         → heat map rendering
├── plotly          → interactive charts
└── streamlit       → web dashboard
```
    """)


# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    f"<div style='text-align:center;font-size:11px;color:#333;padding:8px'>"
    f"NSE Sector Valuation Heat Map  ·  Built with Python + Streamlit  ·  "
    f"Data: NSE India + Yahoo Finance  ·  Updated {date.today().strftime('%d %b %Y')}"
    f"</div>",
    unsafe_allow_html=True,
)
