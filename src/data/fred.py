"""Retrieve US/Japan 3-month rates from FRED (CSV endpoint, no API key).

Owner: TODO
"""

import pandas_datareader.data as web

from src import config

OUTPUT_FILE = config.DIRECTORY / "fred_rates.parquet"


def fetch_fred(start=config.START, end=config.END, series_ids=None):
    """Download FRED series and return a DataFrame indexed by date."""

    if series_ids is None:
        series_ids = config.FRED_SERIES

    df = web.DataReader(list(series_ids.values()), "fred", start, end)
    # Rename columns to the readable country names
    df.columns = list(series_ids.keys())

    return df


if __name__ == "__main__":
    print("Fetching data from FRED...")
    rates = fetch_fred()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    rates.to_parquet(OUTPUT_FILE)
    print(f"Saved {len(rates)} rows to {OUTPUT_FILE}")
