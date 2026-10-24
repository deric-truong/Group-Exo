"""Checks on the saved CFTC file. Run: python3 -m pytest"""
 
import pandas as pd
import pytest
 
from src.data.cftc import OUTPUT_FILE
 
# The data/ folder is not in git: skip (not fail) if the file was never fetched
if not OUTPUT_FILE.exists():
    pytest.skip("run `python3 -m src.data.cftc` first", allow_module_level=True)
 
df = pd.read_parquet(OUTPUT_FILE)
 
 
def test_release_dates_are_fridays():
    assert (df.index.day_name() == "Friday").all()
 
 
def test_release_after_measurement():
    # No look-ahead: data can only be used after it was published
    assert (df.index > df["report_date"]).all()
 
 
def test_no_duplicate_weeks():
    assert not df.index.duplicated().any()
 
 
def test_shutdown_weeks_flagged():
    flagged = df.loc[df["delayed_release"], "report_date"]
    assert flagged.dt.year.isin([2013, 2018, 2019]).all()
    assert len(flagged) > 0
 
 
def test_july_2024_peak():
    # Known value: speculators were about 184,000 contracts net short yen
    assert df.loc["2024-07-01":"2024-07-15", "spec_net"].min() < -180_000
