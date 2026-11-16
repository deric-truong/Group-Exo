"""Exploratory data analysis before modeling."""

import pandas as pd
from src import config
import matplotlib.pyplot as plt
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
ax.bar(mof["release_date"], mof["amount_bn_jpy"], width=20)   # width in days
ax.axhline(0, color="black", linewidth=0.8)
ax.set_title("MoF interventions")
ax.set_xlabel("Date")
ax.set_ylabel("Amount (¥ bn)")
fig.savefig(eda / "plot_mof.png", bbox_inches="tight")
plt.close(fig)

