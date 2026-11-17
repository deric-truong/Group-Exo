"""Exploratory data analysis before modeling."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from src import config
from src.data import bis, cftc, fred, mof, yahoo

data_dir = config.ROOT / "raw data"
eda = config.ROOT / "data_des"
eda.mkdir(parents=True, exist_ok=True)

datasets = {"bis": bis, "cftc": cftc, "fred": fred, "mof": mof, "yahoo": yahoo,}
dataframes = {name: pd.read_parquet(data_dir / module.OUTPUT_FILE.name)
    for name, module in datasets.items()
}

#summary statistics - count, mean, min, 25%, 50%, 75%, max, std
for name, dataframe in dataframes.items():
    dataframe.describe().to_csv(eda / f"sumstats_{name}.csv")

#time series plots
skip = ["release_date"]
for name, dataframe in dataframes.items():
    if name == "mof":
        continue  # skip MOF because it is not continuous
    cols = [c for c in dataframe.select_dtypes("number").columns if c not in skip]
    dataframe[cols].plot(subplots=True, figsize=(10, 2.5 * len(cols)))
    fig = plt.gcf()
    fig.savefig(eda / f"plot_{name}.png", bbox_inches="tight")
    plt.close(fig)

#MOF bar chart
mof = dataframes["mof"]
fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(mof.index, mof["amount_bn_jpy"], width=20) 
ax.axhline(0, color="black", linewidth=0.8)
ax.set_title("MoF interventions")
ax.set_xlabel("Date")
ax.set_ylabel("Amount (¥ bn)")
fig.savefig(eda / "plot_mof.png", bbox_inches="tight")
plt.close(fig)

#mean, skew and kurtosis of carry returns
table = pd.read_parquet(data_dir / "modelling_table.parquet") 
targets = table[["fwd_carry_4w", "fwd_carry_1w"]] 
stats_table = pd.DataFrame({"mean": targets.mean(),"skew": targets.skew(),"excess_kurtosis": targets.kurt()})
stats_table.to_csv(eda / "target_stats.csv")

#histogram of 4-week carry returns with 5% quantile
q05 = targets["fwd_carry_4w"].quantile(0.05)
plt.hist(targets["fwd_carry_4w"], bins=50)
plt.axvline(q05, color="red", label="5% quantile")
plt.xlabel("4-week carry return")
plt.ylabel("Number of weeks")
plt.legend()
plt.savefig(eda / "hist_carry_4w.png")
plt.close()

#2024 carry trade unwind
prices = dataframes["yahoo"]
d = prices.loc["2024-06-01":"2024-09-30"]
fig, axes = plt.subplots(2, 1, sharex=True, figsize=(9, 6))
axes[0].plot(d["usdjpy"].dropna())
axes[0].set_ylabel("USD/JPY")
axes[1].plot(d["vix"].dropna())
axes[1].set_ylabel("VIX")
for a in axes:
    a.axvspan(pd.Timestamp("2024-07-11"), pd.Timestamp("2024-08-05"), color="red", alpha=0.15)
fig.autofmt_xdate()
plt.savefig(eda / "2024_unwind.png")
plt.close()

#worst 5% of 4-week carry returns in history
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(targets["fwd_carry_4w"].index, targets["fwd_carry_4w"], linewidth=0.8)
tail = targets["fwd_carry_4w"][targets["fwd_carry_4w"] <= q05]
ax.scatter(tail.index, tail, color="red", s=12, label="Worst 5%")
ax.axhline(q05, color="red", linestyle="--")
ax.yaxis.set_major_formatter(PercentFormatter(1))
ax.set_ylabel("4-week carry return"); ax.set_xlabel("Date"); ax.legend()
plt.savefig(eda / "unwind_in_history.png")
plt.close()