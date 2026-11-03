"""Retrieve US/Japan 3-month rates from FRED (CSV endpoint, no API key).

Owner: TODO
"""

import pandas as pd
import pandas_datareader.data as web

from src import config

OUTPUT_FILE = config.DIRECTORY / "fred_rates.parquet"


def fetch_fred(start=config.START, end=config.END, series_ids=None):
    """Download FRED series and return a DataFrame indexed by date.

    Index: first day of the month (each value is the monthly average)

    Columns:
        us_3m, jp_3m   3-month interbank rates, in percent (NaN where FRED has no value)
        release_date   approximate date the month became public (no look-ahead)
    """

    if series_ids is None:
        series_ids = config.FRED_SERIES

    raw = web.DataReader(list(series_ids.values()), "fred", start, end)

    #validate the download before using it: fail loudly if FRED changes the series
    if raw.empty:
        raise ValueError("FRED returned no data")
    missing = set(series_ids.values()) - set(raw.columns)
    if missing:
        raise ValueError(f"FRED did not return series {sorted(missing)}")
    if raw.isna().all().any():
        raise ValueError("FRED returned a series with no values")
    if raw.index.duplicated().any():
        raise ValueError("FRED file has duplicate months")
    if not raw.index.is_month_start.all():
        raise ValueError("FRED dates are not month starts, the series may not be monthly")

    #rename by series id, not by position in a list, so US and JP can never be swapped
    df = raw.rename(columns={v: k for k, v in series_ids.items()})
    df = df[list(series_ids.keys())].sort_index()
    df.index.name = "date"

    #rates can be negative (JP 2016-2024) but anything outside this range is an error
    if not df.stack().dropna().between(-2, 25).all():
        raise ValueError("FRED rates outside -2% to 25%, check the units")

    #gaps (jp_3m before 2002-04, us_3m 2020-04, the latest month for jp_3m) are kept as NaN:
    #filling them would invent values, alignment is done in the merge step

    #each value is a monthly average published after the month ends,
    #so it is only usable from release_date on
    df["release_date"] = df.index + pd.DateOffset(months=config.FRED_RELEASE_LAG_MONTHS)

    return df


def save_fred(rates, path=OUTPUT_FILE):
    """Save a table of rates to a Parquet file, creating the folder if needed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    rates.to_parquet(path)


if __name__ == "__main__":
    print("Fetching data from FRED...")
    rates = fetch_fred()
    save_fred(rates)
    print(f"Saved {len(rates)} rows to {OUTPUT_FILE}")
    print(rates.tail())
