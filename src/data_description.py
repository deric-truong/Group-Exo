"""Exploratory data analysis before modeling."""

import pandas as pd
from src import config
from src.data import bis, cftc, fred, mof, yahoo

data_dir = config.ROOT / "raw data"
eda = config.ROOT / "data_des"
eda.mkdir(parents=True, exist_ok=True)

datasets = {"bis": bis, "cftc": cftc, "fred": fred, "mof": mof, "yahoo": yahoo,}
dataframes = {name: pd.read_parquet(data_dir / module.OUTPUT_FILE.name)
    for name, module in datasets.items()
}

#summary statistics for each dataset - count, mean, min, 25%, 50%, 75%, max, std
for name, dataframe in dataframes.items():
    dataframe.describe().to_csv(eda / f"sumstats_{name}.csv")