"""Checks on modelling-table sampling and look-ahead rules."""

import pandas as pd

from src.modelling_table import (
    positioning_features,
    weekly_closes,
    weekly_known_values,
    weekly_sample_dates,
)


def test_monthly_values_are_used_after_release_on_next_trading_day():
    calendar = pd.bdate_range("2024-05-31", "2024-06-07")
    rates = pd.DataFrame(
        {
            "rate": [2.5],
            "release_date": pd.to_datetime(["2024-05-31"]),
        },
        index=pd.to_datetime(["2024-05-01"]),
    )
    sample_dates = pd.Series(
        pd.to_datetime(["2024-05-31", "2024-06-07"]),
        index=pd.to_datetime(["2024-05-31", "2024-06-07"]),
    )

    result = weekly_known_values(rates, ["rate"], calendar, sample_dates)

    assert pd.isna(result.loc["2024-05-31", "rate"])
    assert result.loc["2024-06-07", "rate"] == 2.5


def test_weekly_feature_date_is_actual_fx_close_not_friday_label():
    usdjpy = pd.Series(
        [160.0, 161.0],
        index=pd.to_datetime(["2024-06-27", "2024-07-05"]),
    )
    sample_dates = weekly_sample_dates(usdjpy)
    calendar = pd.bdate_range("2024-06-27", "2024-07-05")
    source = pd.DataFrame(
        {
            "rate": [2.5],
            "release_date": pd.to_datetime(["2024-06-28"]),
        },
        index=pd.to_datetime(["2024-05-01"]),
    )

    result = weekly_known_values(source, ["rate"], calendar, sample_dates)

    assert sample_dates.loc["2024-06-28"] == pd.Timestamp("2024-06-27")
    assert pd.isna(result.loc["2024-06-28", "rate"])
    assert result.loc["2024-07-05", "rate"] == 2.5


def test_cftc_values_wait_until_next_trading_day_and_skip_delayed_reports():
    cftc = pd.DataFrame(
        {
            "spec_net": [10, 90, 30],
            "open_interest": [100, 100, 100],
            "release_date": pd.to_datetime(
                ["2024-06-28", "2024-07-05", "2024-07-12"]
            ),
            "delayed_release": [False, True, False],
        },
        index=pd.to_datetime(["2024-06-25", "2024-07-02", "2024-07-09"]),
    )
    calendar = pd.bdate_range("2024-06-27", "2024-07-19")
    sample_dates = pd.Series(
        pd.to_datetime(
            ["2024-06-28", "2024-07-05", "2024-07-12", "2024-07-19"]
        ),
        index=pd.to_datetime(
            ["2024-06-28", "2024-07-05", "2024-07-12", "2024-07-19"]
        ),
    )
    features = positioning_features(cftc)
    features["release_date"] = features.index

    result = weekly_known_values(
        features,
        ["spec_net_pct_oi"],
        calendar,
        sample_dates,
    )

    assert pd.isna(result.loc["2024-06-28", "spec_net_pct_oi"])
    assert result["spec_net_pct_oi"].iloc[1:].tolist() == [0.1, 0.1, 0.3]


def test_trailing_incomplete_week_is_dropped():
    daily = pd.DataFrame(
        {"usdjpy": [150.0, 151.0, 152.0]},
        index=pd.to_datetime(["2026-09-25", "2026-09-29", "2026-09-30"]),
    )

    weekly = weekly_closes(daily)

    assert weekly.index.tolist() == [pd.Timestamp("2026-09-25")]
