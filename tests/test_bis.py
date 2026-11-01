"""Checks on the saved BIS file. Run: python3 -m pytest"""

import pandas as pd
import pytest

from src.data.bis import OUTPUT_FILE

# The data/ folder is not in git: skip (not fail) if the file was never fetched
if not OUTPUT_FILE.exists():
    pytest.skip("run `python3 -m src.data.bis` first", allow_module_level=True)

df = pd.read_parquet(OUTPUT_FILE)


def test_dates_are_quarter_ends():
    assert df.index.is_quarter_end.all()


def test_no_duplicate_or_missing_quarters():
    assert not df.index.duplicated().any()
    expected = pd.date_range(df.index[0], df.index[-1], freq="QE")
    assert len(df) == len(expected)


def test_no_missing_values():
    assert df["credit"].notna().all()


def test_release_after_measurement():
    # No look-ahead: data can only be used after it was published
    assert (df["release_date"] > df.index).all()


def test_values_in_trillions():
    # Yen credit outside Japan has stayed roughly 30-120 tn JPY since 2000;
    # values outside that mean the unit conversion broke
    assert df["credit"].between(30, 120).all()


def test_no_extreme_jumps():
    # A quarter-on-quarter move above 25% would point to a data error
    assert (df["credit"].pct_change().abs().dropna() < 0.25).all()
