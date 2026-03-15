# ─────────────────────────────────────────────────────────────────────────────
# config.py  ·  Central configuration for the NSE Sector Valuation Heat Map
# ─────────────────────────────────────────────────────────────────────────────

# 12 NSE sectors with their index symbol and constituent tickers (NSE format)
SECTORS = {
    "Nifty IT": {
        "nse_index": "NIFTY IT",
        "tickers": ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS",
                    "LTIM.NS","PERSISTENT.NS","MPHASIS.NS","COFORGE.NS","OFSS.NS"],
        "primary_metrics": ["pe","ev_ebitda"],
    },
    "Nifty Bank": {
        "nse_index": "NIFTY BANK",
        "tickers": ["HDFCBANK.NS","ICICIBANK.NS","KOTAKBANK.NS","AXISBANK.NS",
                    "SBIN.NS","INDUSINDBK.NS","BANDHANBNK.NS","FEDERALBNK.NS",
                    "IDFCFIRSTB.NS","PNB.NS"],
        "primary_metrics": ["pb","div_yield"],
    },
    "Nifty FMCG": {
        "nse_index": "NIFTY FMCG",
        "tickers": ["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS","BRITANNIA.NS",
                    "DABUR.NS","GODREJCP.NS","MARICO.NS","COLPAL.NS",
                    "EMAMILTD.NS","TATACONSUM.NS"],
        "primary_metrics": ["pe","ev_ebitda"],
    },
    "Nifty Auto": {
        "nse_index": "NIFTY AUTO",
        "tickers": ["MARUTI.NS","TATAMOTORS.NS","M&M.NS","BAJAJ-AUTO.NS",
                    "EICHERMOT.NS","HEROMOTOCO.NS","TVSMOTORS.NS","ASHOKLEY.NS",
                    "BALKRISIND.NS","TIINDIA.NS"],
        "primary_metrics": ["pe","ev_ebitda","pb"],
    },
    "Nifty Pharma": {
        "nse_index": "NIFTY PHARMA",
        "tickers": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","DIVISLAB.NS",
                    "BIOCON.NS","LUPIN.NS","AUROPHARMA.NS","TORNTPHARM.NS",
                    "ALKEM.NS","IPCALAB.NS"],
        "primary_metrics": ["pe","ev_ebitda"],
    },
    "Nifty Metal": {
        "nse_index": "NIFTY METAL",
        "tickers": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS","VEDL.NS",
                    "COALINDIA.NS","NMDC.NS","SAIL.NS","NATIONALUM.NS",
                    "HINDCOPPER.NS","APLAPOLLO.NS"],
        "primary_metrics": ["ev_ebitda","pb"],
    },
    "Nifty Energy": {
        "nse_index": "NIFTY ENERGY",
        "tickers": ["RELIANCE.NS","ONGC.NS","NTPC.NS","POWERGRID.NS",
                    "IOC.NS","BPCL.NS","GAIL.NS","TATAPOWER.NS",
                    "ADANIGREEN.NS","ADANIPORTS.NS"],
        "primary_metrics": ["ev_ebitda","div_yield"],
    },
    "Nifty Realty": {
        "nse_index": "NIFTY REALTY",
        "tickers": ["DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS","PHOENIXLTD.NS",
                    "PRESTIGE.NS","BRIGADE.NS","SOBHA.NS","MAHINDCIE.NS",
                    "SUNTECK.NS","KOLTEPATIL.NS"],
        "primary_metrics": ["pb","pe"],
    },
    "Nifty Infra": {
        "nse_index": "NIFTY INFRA",
        "tickers": ["LT.NS","ULTRACEMCO.NS","GRASIM.NS","ACC.NS",
                    "AMBUJACEMENT.NS","SHREECEM.NS","JKCEMENT.NS","RAMCOCEM.NS",
                    "BHARTIARTL.NS","ADANIENT.NS"],
        "primary_metrics": ["ev_ebitda","pb"],
    },
    "Nifty Fin Services": {
        "nse_index": "NIFTY FIN SERVICE",
        "tickers": ["BAJFINANCE.NS","BAJAJFINSV.NS","HDFCLIFE.NS","SBILIFE.NS",
                    "ICICIGI.NS","MUTHOOTFIN.NS","CHOLAFIN.NS","LICHSGFIN.NS",
                    "MANAPPURAM.NS","M&MFIN.NS"],
        "primary_metrics": ["pb","pe"],
    },
    "Nifty Consumer": {
        "nse_index": "NIFTY CONSR DURBL",
        "tickers": ["TITAN.NS","HAVELLS.NS","CROMPTON.NS","VOLTAS.NS",
                    "WHIRLPOOL.NS","BLUESTARCO.NS","BATAINDIA.NS","PAGEIND.NS",
                    "KAJARIACER.NS","VGUARD.NS"],
        "primary_metrics": ["pe","ev_ebitda"],
    },
    "Nifty Healthcare": {
        "nse_index": "NIFTY HEALTHCARE",
        "tickers": ["APOLLOHOSP.NS","FORTIS.NS","MAXHEALTH.NS","NARAYANHLT.NS",
                    "METROPOLIS.NS","DRLALPATH.NS","THYROCARE.NS","KRSNAA.NS",
                    "POLYMED.NS","VIJAYADIAG.NS"],
        "primary_metrics": ["pe","ev_ebitda"],
    },
}

# Metric weights for Composite Richness Score (must sum to 1.0)
DEFAULT_WEIGHTS = {
    "pe":        0.35,
    "ev_ebitda": 0.30,
    "pb":        0.25,
    "div_yield": 0.10,
}

# Sector-specific weight overrides
SECTOR_WEIGHTS = {
    "Nifty Bank":         {"pe": 0.15, "ev_ebitda": 0.05, "pb": 0.60, "div_yield": 0.20},
    "Nifty Fin Services": {"pe": 0.20, "ev_ebitda": 0.10, "pb": 0.55, "div_yield": 0.15},
    "Nifty Metal":        {"pe": 0.20, "ev_ebitda": 0.50, "pb": 0.20, "div_yield": 0.10},
    "Nifty Energy":       {"pe": 0.25, "ev_ebitda": 0.40, "pb": 0.15, "div_yield": 0.20},
}

# Display labels
METRIC_LABELS = {
    "pe":        "P/E",
    "ev_ebitda": "EV/EBITDA",
    "pb":        "P/BV",
    "div_yield": "Div Yield %",
}

# Richness interpretation thresholds
ZONES = {
    "Very Cheap":   (0,  20),
    "Cheap":        (20, 35),
    "Fair":         (35, 65),
    "Expensive":    (65, 80),
    "Very Expensive":(80,101),
}

ZONE_COLORS = {
    "Very Cheap":    "#1D9E75",
    "Cheap":         "#5DCAA5",
    "Fair":          "#B4B2A9",
    "Expensive":     "#EF9F27",
    "Very Expensive":"#E24B4A",
}

# Lookback options in years
LOOKBACK_OPTIONS = {"5 Years": 5, "7 Years": 7, "10 Years": 10}
