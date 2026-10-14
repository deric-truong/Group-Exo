"""Shared project settings: analysis window, tickers, series IDs, paths."""

from datetime import date
from pathlib import Path

# Analysis window
START = "2000-01-01"
END = date.today().isoformat()

# Paths
ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data"

# BIS data url
BIS_CREDIT_URL = (
    "https://stats.bis.org/api/v2/data/dataflow/BIS/WS_GLI/1.0/"
    "Q.JPY.3P.N.A.I.B.JPY?format=csv"
)
#MOF data url
MOF_INTERVENTIONS_URL = (
    "https://www.mof.go.jp/english/policy/international_policy/reference/"
    "feio/foreign_exchange_intervention_operations.csv"
)
#CFTC data url
CFTC_HISTORY_BASE_URL = "https://www.cftc.gov/files/dea/history/"

# Yahoo Finance tickers
YAHOO_TICKERS = {
    "usdjpy": "JPY=X",
    "nikkei": "^N225",
    "nasdaq": "^IXIC",
    "sp500": "^GSPC",
    "bitcoin": "BTC-USD",
    "usdmxn": "MXN=X",
    "gold": "GC=F",
    "brent": "BZ=F",
    "vix": "^VIX",
}

# FRED series (3-month interbank rates, monthly)
FRED_SERIES = {
    "us_3m": "IR3TIB01USM156N",
    "jp_3m": "IR3TIB01JPM156N",
}

# CFTC: Japanese yen futures contract code
CFTC_JPY_CODE = "097741"
CFTC_PUBLICATION_LAG_DAYS = 3