"""Checks on modelling-table sampling and look-ahead rules."""

import pandas as pd

from src.modelling_table import attach_monthly, positioning_features, weekly_closes


def test_monthly_values_are_used_only_from_release_date():
    table = pd.DataFrame(
        index=pd.to_datetime(["2024-05-31", "2024-06-07", "2024-06-14"])
    )
    monthly = pd.Series(
        [2.5],
        index=pd.to_datetime(["2024-05-01"]),
        name="rate",
    )

    result = attach_monthly(table, monthly, pd.offsets.MonthBegin(1))

    assert pd.isna(result.loc["2024-05-31", "rate"])
    assert result.loc["2024-06-07", "rate"] == 2.5


def test_cftc_values_use_release_date_and_skip_delayed_reports():
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
    table = pd.DataFrame(
        index=pd.to_datetime(
            ["2024-06-27", "2024-06-28", "2024-07-05", "2024-07-12"]
        )
    )

    result = attach_monthly(
        table,
        positioning_features(cftc)[["spec_net_pct_oi"]],
        pd.Timedelta(days=0),
    )

    assert pd.isna(result.loc["2024-06-27", "spec_net_pct_oi"])
    assert result["spec_net_pct_oi"].iloc[1:].tolist() == [0.1, 0.1, 0.3]


def test_trailing_incomplete_week_is_dropped():
    daily = pd.DataFrame(
        {"usdjpy": [150.0, 151.0, 152.0]},
        index=pd.to_datetime(["2026-09-25", "2026-09-29", "2026-09-30"]),
    )

    weekly = weekly_closes(daily)

    assert weekly.index.tolist() == [pd.Timestamp("2026-09-25")]
