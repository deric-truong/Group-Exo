"""Build weekly features and forward-carry targets for modelling."""

import numpy as np
import pandas as pd

from src import config
from src.cleaning import as_known, rates_as_of, trading_calendar


def weekly_closes(daily):
    """Sample Friday closes and discard a trailing, incomplete Friday bin."""
    weekly = daily.resample("W-FRI").last()
    if not weekly.empty and weekly.index[-1] > daily.index[-1]:
        weekly = weekly.iloc[:-1]
    return weekly


def weekly_sample_dates(usdjpy):
    """Return the actual USD/JPY observation date for each weekly row."""
    observations = usdjpy.dropna()
    dates = pd.Series(observations.index, index=observations.index)
    return dates.resample("W-FRI").last().dropna()


def weekly_known_values(source, columns, calendar, sample_dates):
    """Sample next-trading-day-known values at each week's actual FX close."""
    known_daily = as_known(source, columns, calendar)
    known_weekly = known_daily.reindex(pd.DatetimeIndex(sample_dates.to_numpy()))
    known_weekly.index = sample_dates.index
    return known_weekly


def positioning_features(cftc):
    """Return on-time CFTC features indexed by publication date."""
    on_time = cftc.loc[~cftc["delayed_release"]]
    pos = pd.DataFrame(
        {
            "spec_net_pct_oi": (
                on_time["spec_net"].to_numpy()
                / on_time["open_interest"].to_numpy()
            )
        },
        index=pd.DatetimeIndex(on_time["release_date"]),
    ).sort_index()
    pos.index.name = None
    rolling = pos["spec_net_pct_oi"].rolling(156, min_periods=52)
    pos["spec_net_z"] = (pos["spec_net_pct_oi"] - rolling.mean()) / rolling.std()
    return pos


def build_modelling_table():
    """Load source files and return the weekly modelling table."""
    # Load Yahoo data
    prices = pd.read_parquet(config.DIRECTORY / "yahoo_prices.parquet")
    usdjpy = prices["usdjpy"].dropna()
    vix = prices["vix"].dropna()

    # Calculate realised volatility from daily log returns before sampling weekly.
    realised_vol = np.log(usdjpy).diff().rolling(20).std() * np.sqrt(252)
    daily = pd.DataFrame({"usdjpy": usdjpy, "rv_20d": realised_vol, "vix": vix})
    table = weekly_closes(daily)
    sample_dates = weekly_sample_dates(usdjpy).reindex(table.index)
    has_fx_close = sample_dates.notna()
    table = table.loc[has_fx_close]
    sample_dates = sample_dates.loc[has_fx_close]

    # Keep measurement-month rates for carry accrual, separate from known predictors.
    rates = pd.read_parquet(config.DIRECTORY / "fred_rates.parquet")
    calendar = trading_calendar(prices)
    accrual_rates = rates_as_of(rates, calendar)
    weekly_accrual_rates = accrual_rates.reindex(
        pd.DatetimeIndex(sample_dates.to_numpy())
    )
    weekly_accrual_rates.index = table.index
    table["us_rate"] = weekly_accrual_rates["us_3m"]
    table["jp_rate"] = weekly_accrual_rates["jp_3m"]
    table["rate_diff"] = table["us_rate"] - table["jp_rate"]

    rates_known = weekly_known_values(
        rates,
        ["us_3m", "jp_3m"],
        calendar,
        sample_dates,
    ).rename(columns={"us_3m": "us_3m_known", "jp_3m": "jp_3m_known"})
    table = table.join(rates_known)
    table["rate_diff_known"] = table["us_3m_known"] - table["jp_3m_known"]
    table["carry_to_vol"] = table["rate_diff_known"] / 100 / table["rv_20d"]
    table["vix_chg_4w"] = table["vix"].diff(4)

    # Forward carry returns are targets, not model features.
    table["fwd_carry_4w"] = np.log(
        table["usdjpy"].shift(-4) / table["usdjpy"]
    ) + (table["rate_diff"] / 100 * 28 / 365)
    table["fwd_carry_1w"] = np.log(
        table["usdjpy"].shift(-1) / table["usdjpy"]
    ) + (table["rate_diff"] / 100 * 7 / 365)

    # Use the source publication date and cleaning's next-trading-day convention.
    cftc = pd.read_parquet(config.DIRECTORY / "cftc_jpy.parquet")
    cftc_features = positioning_features(cftc)
    cftc_features["release_date"] = cftc_features.index
    table = table.join(
        weekly_known_values(
            cftc_features,
            ["spec_net_pct_oi", "spec_net_z"],
            calendar,
            sample_dates,
        )
    )

    # BIS release_date already includes the configured release lag.
    bis = pd.read_parquet(config.DIRECTORY / "bis_credit.parquet")
    bis_features = pd.DataFrame(
        {
            "credit_yoy": bis["credit"].pct_change(4),
            "release_date": bis["release_date"],
        },
        index=bis.index,
    )
    table = table.join(
        weekly_known_values(bis_features, ["credit_yoy"], calendar, sample_dates)
    )

    # Sum interventions per week to align with the weekly table.
    mof = pd.read_parquet(config.DIRECTORY / "mof_interventions.parquet")
    buy = mof["amount_bn_jpy"].clip(lower=0).resample("W-FRI").sum()
    sell = (-mof["amount_bn_jpy"]).clip(lower=0).resample("W-FRI").sum()
    table["yen_buy_amt"] = buy.reindex(table.index).fillna(0)
    table["yen_sell_amt"] = sell.reindex(table.index).fillna(0)

    return table


if __name__ == "__main__":
    modelling_table = build_modelling_table()
    modelling_table.to_parquet(
        config.DIRECTORY / "modelling_table.parquet",
        index=True,
    )
