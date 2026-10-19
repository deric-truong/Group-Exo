"""Retrieve US/Japan 3-month rates from FRED (CSV endpoint, no API key).

Owner: TODO
"""

from pathlib import Path

import pandas_datareader.data as web
"""Pd-datareader is a Python lib, and the function 'DataReader' used to handle data retriever"""


def fetch_fred(start, end, series_ids=None):
    """Download FRED series and return a DataFrame indexed by date."""

    if series_ids is None:
        # Default OECD Series IDs for US and Japan 3-month rates"
        series_ids ={
            'US': 'IR3TIB01USM156N',
            'Japan': 'IR3TIB01JPM156N'
        }

    # Fetch data automatically using pandas_datareader

    df = web.DataReader(list(series_ids.values()),'fred',start,end)
    
    # Rename columns to the readable country names
    df.columns = list(series_ids.keys())

    return df

# --- Testing Block ---

if __name__ == "__main__":
    # Test dates covering the lead-up and aftermath of the August 2024 event
    test_start = "2024-01-01"
    test_end = "2024-08-31"

    print("Fetching data from FRED...")
    df_test = fetch_fred(test_start, test_end)

    print("\n--- Last 5 Rows ---")
    print(df_test.tail())

    print("\n--- DataFrame Info ---")
    print(df_test.info())

    # Write a CSV for quick visual inspection only (not consumed by the pipeline).
    # /data/ is gitignored, so this file is never committed.
    preview_path = Path(__file__).resolve().parents[2] / "data" / "fred_preview.csv"
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    df_test.to_csv(preview_path, index_label="Date")
    print(f"\nPreview CSV written to {preview_path}")

