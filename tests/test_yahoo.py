"""Checks on the saved Yahoo file. Run: python3 -m pytest"""

import pandas as pd
import pytest

from src import config
from src.data.yahoo import OUTPUT_FILE

# The data/ folder is not in git: skip (not fail) if the file was never fetched
if not OUTPUT_FILE.exists():
    pytest.skip("run `python3 -m src.data.yahoo` first", allow_module_level=True)

df = pd.read_parquet(OUTPUT_FILE)


def test_all_assets_present():
    assert list(df.columns) == list(config.YAHOO_TICKERS)


def test_dates_sorted_and_unique():
    assert df.index.is_monotonic_increasing
    assert not df.index.duplicated().any()


def test_prices_positive():
    assert ((df > 0) | df.isna()).all().all()


def test_usdjpy_bad_prints_removed():
    # Known Yahoo errors: one-day spikes that go straight back the next day
    for day in ["2008-04-08", "2008-05-08", "2008-10-08", "2008-12-08"]:
        assert pd.isna(df.loc[day, "usdjpy"])


def test_usdjpy_daily_moves_plausible():
    # USD/JPY has not moved more than 10% in one day since 2000
    returns = df["usdjpy"].dropna().pct_change().abs()
    assert (returns.dropna() < 0.10).all()


def test_usdjpy_level_range():
    # USD/JPY traded between about 75 and 165 since 2000
    assert df["usdjpy"].dropna().between(75, 165).all()


def test_august_2024_crash():
    # Known value: the Nikkei fell more than 12% on 5 August 2024
    nikkei = df["nikkei"].dropna()
    assert nikkei.pct_change().loc["2024-08-05"] < -0.12
