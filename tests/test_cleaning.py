"""Checks on the merged daily table. Run: python3 -m pytest"""

import pandas as pd
import pytest

from src import config
from src.cleaning import OUTPUT_FILE, load_sources

# The data/ folder is not in git: skip (not fail) if the file was never built
if not OUTPUT_FILE.exists():
    pytest.skip("run `python3 -m src.cleaning` first", allow_module_level=True)

df = pd.read_parquet(OUTPUT_FILE)
sources = load_sources()


def test_one_row_per_usdjpy_trading_day():
    assert not df.index.duplicated().any()
    assert df.index.is_monotonic_increasing
    assert df["usdjpy"].notna().all()
    assert (df.index.dayofweek < 5).all()


def test_inside_the_window():
    assert df.index[0] >= pd.Timestamp(config.START)
    assert df.index[-1] <= pd.Timestamp(config.END)


def test_prices_not_filled():
    # Market holidays stay NaN: e.g. the Nikkei is closed on 1-3 January
    assert df.loc["2024-01-02", "nikkei"] != df.loc["2024-01-02", "nikkei"]


@pytest.mark.parametrize(
    "name, column",
    [("fred", "us_3m"), ("fred", "jp_3m"), ("bis", "credit")],
)
def test_known_values_only_after_release(name, column):
    # No look-ahead: on each day, the known value is the latest one released
    # strictly before that day
    src = sources[name].dropna(subset=[column]).sort_values("release_date")
    for day in df.index[::5]:
        public = src.loc[src["release_date"] < day, column]
        expected = public.iloc[-1] if len(public) else float("nan")
        got = df.loc[day, f"{column}_known"]
        assert got == expected or (pd.isna(got) and pd.isna(expected))


def test_cftc_known_on_the_monday_after_release():
    # Report of Tuesday 2024-07-02 released Friday 07-05, usable from Monday 07-08
    report = sources["cftc"].loc["2024-07-02", "spec_net"]
    assert df.loc["2024-07-05", "spec_net_known"] != report
    assert df.loc["2024-07-08", "spec_net_known"] == report


def test_cftc_delayed_reports_left_out():
    delayed = sources["cftc"][sources["cftc"]["delayed_release"]]
    assert not df["spec_net_known"].isin(delayed["spec_net"]).loc["2013-10-04":"2013-11-07"].any()


def test_rate_diff_is_us_minus_jp():
    diff = (df["us_3m"] - df["jp_3m"] - df["rate_diff"]).dropna()
    assert (diff.abs() < 1e-12).all()


def test_rates_not_filled_past_last_month():
    # jp_3m stops a month before us_3m: no value may be invented after it
    last_jp = sources["fred"]["jp_3m"].dropna().index[-1]
    assert df.loc[last_jp + pd.offsets.MonthBegin(1):, "jp_3m"].isna().all()


def test_july_2024_interventions_on_their_day():
    assert df.loc["2024-07-11", "intervention_bn_jpy"] > 3000
    assert df.loc["2024-07-12", "intervention_bn_jpy"] > 2000
    assert df.loc["2024-07-10", "intervention_bn_jpy"] == 0


def test_no_intervention_lost():
    assert df["intervention_bn_jpy"].notna().all()
    total = sources["mof"].loc[df.index[0]: df.index[-1], "amount_bn_jpy"].sum()
    assert abs(df["intervention_bn_jpy"].sum() - total) < 1e-6
