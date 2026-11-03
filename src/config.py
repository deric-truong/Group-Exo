"""Shared project settings: analysis window, tickers, series IDs, paths."""

from datetime import date
from pathlib import Path

# Analysis window
# TODO: check if the data and start/end dates differ across data sources (FRED, Yahoo, BIS,
# CFTC, MOF) - e.g. FRED jp_3m only starts 2002-04 and lags us_3m by a month at the end.
# Need to agree within the group on a common window
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
# BIS: publication lag of the global liquidity indicators, in months after quarter end
# TODO: check the exact release calendar on bis.org before relying on it
BIS_RELEASE_LAG_MONTHS = 4
#MOF data url
MOF_INTERVENTIONS_URL = (
    "https://www.mof.go.jp/english/policy/international_policy/reference/"
    "feio/foreign_exchange_intervention_operations.csv"
)
# MoF: daily details are published once per quarter, about 5-6 weeks after quarter end
# (e.g. Q1 2024 on 9 May, Q2 on 7 Aug, Q3 on 8 Nov 2024, Q4 on 7 Feb 2025); 45 days is on or after every release seen
MOF_RELEASE_LAG_DAYS = 45
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

# Yahoo: series cleaned of one-day bad prints (see remove_spikes in yahoo.py).
# Only FX: for equities, VIX, Bitcoin and oil, big moves that reverse the next day are real
YAHOO_SPIKE_CHECK = ["usdjpy"]

# FRED series (3-month interbank rates, monthly)
FRED_SERIES = {
    "us_3m": "IR3TIB01USM156N",
    "jp_3m": "IR3TIB01JPM156N",
}
# FRED: months after the month start before the monthly average is public
# (US arrives about 1 month after month end, JP about 2)
# TODO: check the exact OECD release timing before relying on it
FRED_RELEASE_LAG_MONTHS = 3

# CFTC: Japanese yen futures contract code
CFTC_JPY_CODE = "097741"

# CFTC: US government shutdowns delayed the Commitments of Traders reports.
# Reports measured in these windows were published weeks late, so their
# release dates are unreliable. Dates are report (Tuesday) dates.
# TODO: check the exact windows on cftc.gov before relying on them
CFTC_DELAYED_WINDOWS = [
    ("2013-10-01", "2013-10-15"),  # October 2013 shutdown
    ("2018-12-25", "2019-01-29"),  # Dec 2018 - Jan 2019 shutdown
]