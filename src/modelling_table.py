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

    monthly = series.dropna().to_frame()                      # changed: Series -> one-column table
    monthly["release_date"] = monthly.index + release_offset  # changed: set on that table

    merged = pd.merge_asof(table, monthly, left_index=True, right_on="release_date", direction="backward")

    return merged.drop(columns=["release_date"])
#US rate is a monthly average released at month-end
table = attach_monthly(table, rates["us_3m"], pd.offsets.MonthBegin(1))
#FRED website shows a delay of 2-6 weeks for the JP rate, so we use 2 months to be safe and avoid look-ahead bias
table = attach_monthly(table, rates["jp_3m"], pd.offsets.DateOffset(months=2)) 

#calculate rate differential
table["rate_diff"] = table["us_3m"] - table["jp_3m"]

print(table.loc["2002-05-24":"2002-06-14"])