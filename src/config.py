"""Shared project settings: analysis window, tickers, series IDs, paths."""

from pathlib import Path

# Fixed analysis window (do not change once agreed)
START = "2000-01-01"
END = "2025-12-31"

# Paths
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

# Yahoo Finance tickers
YAHOO_TICKERS = {
    "usdjpy": "JPY=X",
}

# FRED series (3-month interbank rates, monthly)
FRED_SERIES = {
    "us_3m": "IR3TIB01USM156N",
    "jp_3m": "IR3TIB01JPM156N",
}

# CFTC: Japanese yen futures contract code
CFTC_JPY_CODE = "097741"
CFTC_PUBLICATION_LAG_DAYS = 3
