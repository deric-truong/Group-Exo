"""Retrieve US/Japan 3-month rates from FRED (CSV endpoint, no API key).

Owner: TODO
"""

from logging import config

import pandas as pd
import pandas_datareader.data as web #Pd-datareader is a Python lib, and the function 'DataReader' used to handle data retriever
from pathlib import Path

def fetch_fred(start, end, series_ids=None):
    """Download FRED series and return a DataFrame indexed by date."""

    if series_ids is None:
        # Default OECD Series IDs for US and Japan 3-month rates
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
    test_start = "2000-01-01"
    test_end = pd.Timestamp.today().strftime("%Y-%m-%d")

    print("Fetching data from FRED...")
    df_test = fetch_fred(test_start, test_end)

    output_file = Path("data/fred_rates.parquet")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_test.to_parquet(output_file, index=True)
    print(f"Saved data to {output_file}")

    print("\n--- Last 5 Rows ---")
    print(df_test.tail())

    print("\n--- DataFrame Info ---")
    print(df_test.info())

