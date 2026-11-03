"""Checks on the saved FRED file. Run: python3 -m pytest"""

import pandas as pd
import pytest

from src.data.fred import OUTPUT_FILE

# The data/ folder is not in git: skip (not fail) if the file was never fetched
if not OUTPUT_FILE.exists():
    pytest.skip("run `python3 -m src.data.fred` first", allow_module_level=True)

df = pd.read_parquet(OUTPUT_FILE)


def test_dates_are_month_starts():
    # is_month_start gives True/False for each data
    # .all() requires all values to be True, otherwise the test fails
    assert df.index.is_month_start.all()


def test_no_duplicate_or_missing_months():
    # .duplicated().any() checks if there are any duplicate dates
    assert not df.index.duplicated().any()
    # complete list of month starts from the first to the last date
    expected = pd.date_range(df.index[0], df.index[-1], freq="MS")
    assert len(df) == len(expected)


def test_columns_are_us_and_jp():
    # US rates have averaged well above JP rates since 2000 (about 2.2% vs 0.3%);
    # if this fails, the columns were probably swapped
    assert df["us_3m"].mean() > df["jp_3m"].mean() + 1


def test_release_after_measurement():
    # No look-ahead: a monthly average can only be used after the month ends
    assert (df["release_date"] > df.index + pd.offsets.MonthEnd(0)).all()


def test_values_in_percent():
    # Rates in percent: JP went slightly negative, neither went above ~7% since 2000
    rates = df[["us_3m", "jp_3m"]].stack().dropna()
    assert rates.between(-1, 10).all()


def test_no_extreme_jumps():
    # A month-on-month move above 2 percentage points would point to a data error
    # (largest real move: US -1.65 in 2008-11)
    assert (df[["us_3m", "jp_3m"]].diff().abs().stack().dropna() < 2).all()
