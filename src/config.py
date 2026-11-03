"""Shared project settings: analysis window, tickers, series IDs, paths."""

from pathlib import Path

# Download window, fixed so that results do not change from one run to the next.
# END = end of Q3 2026: daily and weekly data are complete up to it; monthly and
# quarterly values published later are handled through release_date
START = "2000-01-01"
END = "2026-09-30"

# Analysis window for tests that need the US-JP rate differential (carry):
# FRED jp_3m only starts in 2002-04. Shorter series (Bitcoin from 2014-09,
# Brent from 2007-07, USD/MXN from 2003-12) are used on their own ranges
ANALYSIS_START = "2002-04-01"

# Paths
ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data"

# BIS data url
BIS_CREDIT_URL = (
    "https://stats.bis.org/api/v2/data/dataflow/BIS/WS_GLI/1.0/"
    "Q.JPY.3P.N.A.I.B.JPY?format=csv"
)
# BIS: publication lag of the global liquidity indicators, in months after quarter end
# Checked: 2026-Q2 (quarter end 30 Jun 2026) was released on 29 Oct 2026, so
# quarter end + 4 months (30 Oct) is on or just after the actual release
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
# Checked on 2026-11-03: the FRED update of 15 Oct 2026 had US up to Sep and JP up to Aug,
# i.e. about 1.5 and 2.5 months after the month start, so 3 months is on the safe side.
# Past release dates (ALFRED vintages) need an API key and were not checked
FRED_RELEASE_LAG_MONTHS = 3

# FRED: jp_3m changes underlying rate in 2025-01. Checked against the JBA PDFs
# (jbatibor.or.jp): from 2025-01 every value equals the month-end 3-month JBA Japanese
# Yen TIBOR exactly; in 2024 values are 6-23bp below it (another rate, probably Euroyen
# TIBOR, which stopped on 30 Dec 2024). Treat changes across this date as a break
JP_3M_BREAK = "2025-01-01"

# CFTC: Japanese yen futures contract code
CFTC_JPY_CODE = "097741"

# CFTC: US government shutdowns delayed the Commitments of Traders reports.
# Reports measured in these windows were published weeks late, so their
# release dates are unreliable. Dates are report (measurement) dates, and run
# until CFTC was back on its normal schedule, not just to the end of the shutdown:
# - 2013: shutdown 1-17 Oct; first late report due 4 Oct, catch-up from 25 Oct,
#   back on schedule 8 Nov (report of 5 Nov on time)
# - 2018-19: shutdown 22 Dec - 25 Jan; first late report due 28 Dec (measured on
#   Monday 24 Dec), two reports a week from 1 Feb, back on schedule 8 Mar (report of 5 Mar on time)
CFTC_DELAYED_WINDOWS = [
    ("2013-10-01", "2013-10-29"),  # October 2013 shutdown
    ("2018-12-24", "2019-02-26"),  # Dec 2018 - Jan 2019 shutdown
]