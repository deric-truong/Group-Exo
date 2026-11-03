"""Checks on the saved CFTC file. Run: python3 -m pytest"""
 
import pandas as pd
import pytest
 
from src.data.cftc import OUTPUT_FILE
 
# The data/ folder is not in git: skip (not fail) if the file was never fetched
if not OUTPUT_FILE.exists():
    pytest.skip("run `python3 -m src.data.cftc` first", allow_module_level=True)
 
df = pd.read_parquet(OUTPUT_FILE)
 
 
def test_release_dates_are_fridays():
    assert (df["release_date"].dt.day_name() == "Friday").all()
 
 
def test_release_after_measurement():
    # No look-ahead: data can only be used after it was published
    assert (df["release_date"] > df.index).all()
 
 
def test_no_duplicate_weeks():
    assert not df.index.duplicated().any()
 
 
def test_shutdown_weeks_flagged():
    flagged = df.index[df["delayed_release"]]
    assert flagged.year.isin([2013, 2018, 2019]).all()
    assert len(flagged) > 0
 
 
def test_shutdown_windows_cover_catch_up():
    # Reports stay delayed until CFTC is back on schedule (8 Nov 2013, 8 Mar 2019)
    for day in ["2013-10-29", "2018-12-24", "2019-02-26"]:
        assert df.loc[day, "delayed_release"]
    for day in ["2013-11-05", "2019-03-05"]:
        assert not df.loc[day, "delayed_release"]


def test_july_2024_peak():
    # Known value: speculators were about 184,000 contracts net short yen
    assert df.loc["2024-07-01":"2024-07-15", "spec_net"].min() < -180_000
