""" Group features extracted from raw data in a table to be used in modelling, and engineer new features of interest"""


import pandas as pd
from src import config
import numpy as np


#load yahoo data
prices = pd.read_parquet(config.DIRECTORY / "yahoo_prices.parquet")
usdjpy = prices["usdjpy"].dropna()
vix = prices["vix"].dropna()
#realised volatility - rolling 20-day (convention) standard deviation of daily log returns, annualized
realised_vol = np.log(usdjpy).diff().rolling(20).std() * np.sqrt(252)

#start constructing table
daily = pd.DataFrame({"usdjpy": usdjpy, "rv_20d": realised_vol, "vix": vix})
#take weekly closing data - positioning is weekly so NA 4/5 days, fewer overlapping data, etc.
table = daily.resample("W-FRI").last()


#load rate data
rates = pd.read_parquet(config.DIRECTORY / "fred_rates.parquet")
#add rates to table - we need to align monthly FRED release schedules with the weekly data
def attach_monthly (table, series, release_offset):
    """ function allows flexibility in aligning data with different release schedules and standards"""

    monthly = pd.DataFrame(series).dropna(how="all")
    monthly["release_date"] = monthly.index + release_offset

    merged = pd.merge_asof(table, monthly, left_index=True, right_on="release_date", direction="backward")

    return merged.drop(columns=["release_date"])
#US rate is a monthly average released at month-end, so we use the first day of the next month to avoid look-ahead bias
table = attach_monthly(table, rates["us_3m"], pd.offsets.MonthBegin(1))
#FRED website shows a delay of 2-6 weeks for the JP rate, so we use 2 months to avoid look-ahead bias
table = attach_monthly(table, rates["jp_3m"], pd.offsets.DateOffset(months=2)) 
#formatting
table = table.rename(columns={"us_3m": "us_rate", "jp_3m": "jp_rate"})

#calculate rate differential
table["rate_diff"] = table["us_rate"] - table["jp_rate"]

#calculate carry-to-volatility ratio (carry trade return per unit of risk)
table["carry_to_vol"] = table["rate_diff"] / 100 / table["rv_20d"]

#add VIX change over past 4 weeks
table["vix_chg_4w"] = table["vix"].diff(4)

#calculate carry trade return for different time horizons (target variables)
table["fwd_carry_4w"] = np.log(table["usdjpy"].shift(-4)/table["usdjpy"]) + table["rate_diff"] /100 * 28/365
table["fwd_carry_1w"] = np.log(table["usdjpy"].shift(-1)/table["usdjpy"]) + table["rate_diff"] / 100 * 7/365


#load positioning data 
cftc = pd.read_parquet(config.DIRECTORY / "cftc_jpy.parquet")
#divide net positioning by open interest for comparability
pos = pd.DataFrame({"spec_net_pct_oi": cftc["spec_net"] / cftc["open_interest"]})
#calculate z-score with 3 year window (measure of how extreme the positioning is relative to its history)
pos["spec_net_z"] = (pos["spec_net_pct_oi"] - pos["spec_net_pct_oi"].rolling(156, min_periods=52).mean()) / pos["spec_net_pct_oi"].rolling(156, min_periods=52).std()

#add positioning data to table
table = attach_monthly(table, pos, pd.Timedelta(days=0)) 


#load credit data
bis = pd.read_parquet(config.DIRECTORY / "bis_credit.parquet")
#yearly growth
credit_yoy = bis["credit"].pct_change(4).rename("credit_yoy")

#add credit data to table
table = attach_monthly(table, credit_yoy, pd.DateOffset(months=config.BIS_RELEASE_LAG_MONTHS))


#load intervention data
mof = pd.read_parquet(config.DIRECTORY / "mof_interventions.parquet")

#sum per week to align with the weekly table
buy = mof["amount_bn_jpy"].clip(lower=0).resample("W-FRI").sum()
sell = (-mof["amount_bn_jpy"]).clip(lower=0).resample("W-FRI").sum()
table["yen_buy_amt"] = buy.reindex(table.index).fillna(0)
table["yen_sell_amt"] = sell.reindex(table.index).fillna(0)

#write final table to parquet
table.to_parquet(config.DIRECTORY / "modelling_table.parquet", index=True)

#T/F: was there an intervention in the 1 week/4 weeks the target looks over? (not features for the model, but useful for analysis & checking robustness of results (PHASE 5))
def intervention_ahead(amount, weeks):
    """ True if there is an intervention in any of the next `weeks` weeks """
    return sum([amount.shift(-i) > 0 for i in range(1, weeks + 1)]) > 0

buy_4w = intervention_ahead(table["yen_buy_amt"], 4)
any_4w = buy_4w | intervention_ahead(table["yen_sell_amt"], 4)