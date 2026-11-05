"""Align sources on a common calendar and handle missing values.

Builds one daily table on USD/JPY trading days from the files saved by
src/data/*. Each source keeps the date convention of docs/decisions.md:

- values tied to the day they refer to (event date) are for the event study
  and for accruing carry;
- columns ending in ``_known`` only use what was public at the time
  (from the trading day after ``release_date``) and are for the predictive
  tests (H2, H3).

Run from the repository root: python -m src.cleaning
"""

import pandas as pd

from src import config
from src.data import bis, cftc, fred, mof, yahoo

OUTPUT_FILE = config.DIRECTORY / "merged_daily.parquet"

RATE_COLUMNS = ["us_3m", "jp_3m"]
CFTC_COLUMNS = ["spec_net", "spec_net_pct_oi", "open_interest"]


def load_sources():
    """Read the saved file of each source, failing with a hint if one is missing."""
    files = {
        "yahoo": yahoo.OUTPUT_FILE,
        "fred": fred.OUTPUT_FILE,
        "cftc": cftc.OUTPUT_FILE,
        "bis": bis.OUTPUT_FILE,
        "mof": mof.OUTPUT_FILE,
    }
    missing = [name for name, path in files.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            f"No saved data for {missing}: run `python -m src.data.<source>` first"
        )
    return {name: pd.read_parquet(path) for name, path in files.items()}


def trading_calendar(prices, start=config.START, end=config.END):
    """Days with a USD/JPY close: the carry trade is priced on this market.

    Weekends (Bitcoin only) and days with no FX close are dropped, so Bitcoin's
    Friday-to-Monday change includes the weekend.
    """
    return prices["usdjpy"].dropna().loc[start:end].index


def as_known(df, columns, calendar):
    """Spread values on the calendar from the trading day after their release.

    Release dates are estimates and data comes out during the day, so a value
    is only used from the next day on (never on its release day). Between
    releases the last public value is carried forward.
    """
    known = df.set_index("release_date")[columns].sort_index()
    # Several values released the same day: keep the latest one
    known = known[~known.index.duplicated(keep="last")]
    # A missing value (e.g. FRED us_3m 2020-04) brings nothing new: the previous
    # public value is still the latest known one
    known = known.ffill()
    known.index = known.index + pd.Timedelta(days=1)
    return known.reindex(calendar, method="ffill")


def rates_as_of(rates, calendar):
    """Give each day the rate of its own month (no filling past the last month).

    Used to accrue carry: the investor earns the rate of the day, not the one
    published months later.
    """
    by_month = rates[RATE_COLUMNS].copy()
    by_month.index = by_month.index.to_period("M")
    return by_month.reindex(calendar.to_period("M")).set_axis(calendar)


def interventions_daily(interventions, calendar):
    """Signed intervention amount on its day, 0 on other days."""
    daily = interventions["amount_bn_jpy"].reindex(calendar).fillna(0.0)

    # Intervention days on which USD/JPY has no close would be lost silently
    lost = interventions.index
    lost = lost[(lost >= calendar[0]) & (lost <= calendar[-1]) & ~lost.isin(calendar)]
    if len(lost):
        raise ValueError(f"Interventions on days without a USD/JPY close: {list(lost.date)}")
    return daily


def build_daily(sources):
    """Return the merged daily table (one row per USD/JPY trading day).

    Columns:
        usdjpy ... vix        Yahoo closes, NaN when that market was closed
                              (not filled, to avoid fake zero returns)
        us_3m, jp_3m          rate of the day's month, in percent (for carry accrual)
        rate_diff             us_3m - jp_3m
        *_3m_known,
        rate_diff_known       rates public on that day (for signals)
        spec_net_known,
        spec_net_pct_oi_known,
        open_interest_known   latest CFTC report public on that day; reports
                              delayed by a shutdown are left out, so the last
                              on-time report is carried forward instead
        credit_known          latest BIS yen credit public on that day, tn JPY
        intervention_bn_jpy   MoF intervention on that day (> 0 yen bought), 0 if none
    """
    prices = sources["yahoo"]
    calendar = trading_calendar(prices)
    daily = prices.reindex(calendar)

    rates = rates_as_of(sources["fred"], calendar)
    daily[RATE_COLUMNS] = rates
    daily["rate_diff"] = rates["us_3m"] - rates["jp_3m"]

    rates_known = as_known(sources["fred"], RATE_COLUMNS, calendar)
    daily[[f"{c}_known" for c in RATE_COLUMNS]] = rates_known
    daily["rate_diff_known"] = rates_known["us_3m"] - rates_known["jp_3m"]

    positions = sources["cftc"]
    on_time = positions[~positions["delayed_release"]]
    daily[[f"{c}_known" for c in CFTC_COLUMNS]] = as_known(on_time, CFTC_COLUMNS, calendar)

    daily["credit_known"] = as_known(sources["bis"], ["credit"], calendar)["credit"]

    daily["intervention_bn_jpy"] = interventions_daily(sources["mof"], calendar)

    daily.index.name = "date"
    daily.columns.name = None
    return daily


def save_daily(daily, path=OUTPUT_FILE):
    """Save the merged table to a Parquet file, creating the folder if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    daily.to_parquet(path)


if __name__ == "__main__":
    merged = build_daily(load_sources())
    save_daily(merged)
    print(f"Saved {len(merged)} rows x {merged.shape[1]} columns to {OUTPUT_FILE}")
    print(merged.notna().mean().round(3).to_string())
