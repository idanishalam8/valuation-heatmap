# NSE Sector Valuation Heat Map 📊

A live equity research tool that answers: **are Indian stock market sectors cheap or expensive right now?**

It tracks P/E, P/BV, EV/EBITDA, and Dividend Yield across 12 NSE sectors, computes historical percentile ranks using 10 years of data, and renders a colour-coded heat map — **green = cheap, red = expensive**.

---

## Features

- **12 NSE sectors** — IT, Bank, FMCG, Auto, Pharma, Metal, Energy, Realty, Infra, Fin Services, Consumer, Healthcare
- **4 valuation multiples** — P/E, P/BV, EV/EBITDA, Dividend Yield
- **Historical percentile rank** — where is today's multiple vs 10-year history?
- **Composite Richness Score** — one number per sector (0=cheapest, 100=most expensive)
- **Sector drill-down** — 10-year history chart + stats table + radar chart
- **Live data** — fetched fresh from Yahoo Finance + NSE India
- **Auto-caching** — 4h cache for current data, 24h for history

---

## Project Structure

```
valuation-heatmap/
├── app.py                 ← Streamlit main dashboard
├── src/
│   ├── config.py          ← Sectors, tickers, weights, zones
│   ├── fetch.py           ← Data fetching (yfinance + NSE + fallback)
│   ├── metrics.py         ← Cleaning + sector aggregation
│   ├── percentile.py      ← Percentile ranking + composite score
│   └── visuals.py         ← All chart generation
├── data/cache/            ← Auto-created pickle cache
├── requirements.txt
└── README.md
```

---

## Run Locally

```bash
# 1. Clone / download the project
git clone https://github.com/YOUR_USERNAME/valuation-heatmap.git
cd valuation-heatmap

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

Visit `http://localhost:8501` in your browser.

---

## Deploy to Streamlit Community Cloud (Free)

1. Push this project to a **public GitHub repository**
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click **"New app"**
5. Select your repository → branch `main` → file `app.py`
6. Click **Deploy**
7. Your live URL: `https://YOUR_USERNAME-valuation-heatmap-app-XXXXX.streamlit.app`

**Put this URL on your CV under Projects.**

---

## How it Works (Pipeline)

```
NSE India CSVs ─┐
                ├─→ fetch.py ──→ metrics.py ──→ percentile.py ──→ visuals.py ──→ app.py
yfinance API  ──┘
```

1. **Fetch**: Pull current multiples via yfinance API; historical P/E/PB from NSE
2. **Clean**: Remove negative P/E, cap outliers, handle NaN
3. **Aggregate**: Company-level → sector median (never mean)
4. **Rank**: `scipy.stats.percentileofscore(10yr_array, today_value)` for each cell
5. **Score**: Weighted average of metric percentiles = Composite Richness Score
6. **Render**: Seaborn heatmap + Plotly charts in Streamlit

---

## Data Sources

| Source | Data | How |
|--------|------|-----|
| Yahoo Finance (via yfinance) | Current P/E, P/BV, EV/EBITDA, Div Yield | Python API |
| NSE India | Historical index P/E, P/BV, Div Yield | CSV download / API |
| Synthetic fallback | Realistic historical data | Generated if NSE unavailable |

---

## Key Concepts Used

| Concept | Where used |
|---------|-----------|
| Valuation multiples (P/E, P/BV, EV/EBITDA) | All calculations |
| `scipy.stats.percentileofscore()` | Core ranking engine |
| Median aggregation (not mean) | Company → sector collapse |
| Weighted average | Composite Richness Score |
| Z-Score | Secondary signal in stats table |
| Diverging colour scale | Heat map (green/white/red) |
| ETL pipeline architecture | fetch → metrics → percentile → visuals |

---

## Interview Pitch (2 min)

> "I built a Python dashboard that replicates the sector valuation scorecard used by institutional equity strategists. It pulls 10 years of NSE index P/E data, computes historical percentile ranks for P/E, P/BV, EV/EBITDA, and Dividend Yield, and renders them as an interactive heat map. The key design choice was using percentile rank rather than raw multiples — because a 20x P/E for IT in 2024 is very different from 2016. [Share live URL and walk through one real finding.]"

---

*Built with Python · Streamlit · yfinance · NSE India data*
