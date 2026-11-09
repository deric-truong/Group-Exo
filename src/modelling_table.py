"""Build weekly features and forward-carry targets for modelling."""

import numpy as np
import pandas as pd

from src import config


def attach_monthly(table, series, release_offset):
    """Align a slow-moving series with weekly rows using its release date."""
    monthly = pd.DataFrame(series).dropna(how="all")
    monthly["release_date"] = monthly.index + release_offset
    monthly["release_date"] = monthly["release_date"].astype(table.index.dtype)

    merged = pd.merge_asof(
        table,
        monthly,
        left_index=True,
        right_on="release_date",
        direction="backward",
    )
    return merged.drop(columns=["release_date"])


def weekly_closes(daily):
    """Sample Friday closes and discard a trailing, incomplete Friday bin."""
    weekly = daily.resample("W-FRI").last()
    if not weekly.empty and weekly.index[-1] > daily.index[-1]:
        weekly = weekly.iloc[:-1]
    return weekly


def positioning_features(cftc):
    """Return on-time CFTC features indexed by publication date."""
    on_time = cftc.loc[~cftc["delayed_release"]]
    pos = pd.DataFrame(
        {
            "spec_net_pct_oi": (
                on_time["spec_net"].to_numpy() / on_time["open_interest"].to_numpy()
            )
        },
        index=pd.DatetimeIndex(on_time["release_date"]),
    ).sort_index()
    pos.index.name = None
    pos["spec_net_z"] = (
        pos["spec_net_pct_oi"] - pos["spec_net_pct_oi"].rolling(156, min_periods=52).mean()
    ) / pos["spec_net_pct_oi"].rolling(156, min_periods=52).std()
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

    # Load rate data and align monthly FRED release schedules with weekly data.
    rates = pd.read_parquet(config.DIRECTORY / "fred_rates.parquet")
    # A US monthly average is usable from the first day of the following month.
    table = attach_monthly(table, rates["us_3m"], pd.offsets.MonthBegin(1))
    # Use a two-month lag for the JP rate to avoid look-ahead bias.
    table = attach_monthly(table, rates["jp_3m"], pd.DateOffset(months=2))
    table = table.rename(columns={"us_3m": "us_rate", "jp_3m": "jp_rate"})

    table["rate_diff"] = table["us_rate"] - table["jp_rate"]
    table["carry_to_vol"] = table["rate_diff"] / 100 / table["rv_20d"]
    table["vix_chg_4w"] = table["vix"].diff(4)

    # Forward carry returns are targets, not model features.
    table["fwd_carry_4w"] = np.log(table["usdjpy"].shift(-4) / table["usdjpy"]) + (
        table["rate_diff"] / 100 * 28 / 365
    )
    table["fwd_carry_1w"] = np.log(table["usdjpy"].shift(-1) / table["usdjpy"]) + (
        table["rate_diff"] / 100 * 7 / 365
    )

    # Positioning features use only on-time reports, starting on publication day.
    cftc = pd.read_parquet(config.DIRECTORY / "cftc_jpy.parquet")
    table = attach_monthly(table, positioning_features(cftc), pd.Timedelta(days=0))

    # Credit growth is available only after the configured BIS release lag.
    bis = pd.read_parquet(config.DIRECTORY / "bis_credit.parquet")
    credit_yoy = bis["credit"].pct_change(4).rename("credit_yoy")
    table = attach_monthly(
        table,
        credit_yoy,
        pd.DateOffset(months=config.BIS_RELEASE_LAG_MONTHS),
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
