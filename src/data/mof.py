"""Retrieve Japan's foreign exchange interventions from the Ministry of Finance.

Source: MoF "Foreign Exchange Intervention Operations"
(https://www.mof.go.jp/english/policy/international_policy/reference/feio/index.html).
One bilingual CSV (Shift-JIS) lists every intervention day since April 1991.

Daily details are only disclosed at the end of each quarter, so dates are
the day of the intervention, not the day the market learned about it.

Owner: TODO
"""

import pandas as pd
import requests

from src import config

URL = (
    "https://www.mof.go.jp/english/policy/international_policy/reference/"
    "feio/foreign_exchange_intervention_operations.csv"
)
RAW_FILE = config.RAW_DIR / "mof_interventions.csv"
OUTPUT_FILE = config.PROCESSED_DIR / "mof_interventions.parquet"


def fetch_mof(start=config.START, end=config.END):
    """Return yen interventions, one row per intervention day.

    Column:
        amount_bn_jpy   total size in billions of yen, signed:
                        > 0 = yen bought (to stop the yen falling)
                        < 0 = yen sold (to stop the yen rising)

    The result is also saved to data/processed/mof_interventions.parquet.
    """
    # Download once, then reuse the cached file
    if not RAW_FILE.exists():
        RAW_FILE.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(URL, timeout=60)
        response.raise_for_status()
        RAW_FILE.write_bytes(response.content)

    # Keep the English columns only (the first 3 are Japanese dates)
    df = pd.read_csv(
        RAW_FILE,
        encoding="cp932",  # Japanese Shift-JIS encoding
        header=None,
        usecols=[3, 4, 5, 6, 8],
        names=["year", "month", "day", "amount", "pair"],
        dtype=str,
    )

    # Intervention days are the rows with a numeric day
    # (titles, notes and quarterly totals are dropped)
    df = df[df["day"].str.isdigit().fillna(False)]

    # Year and month are only written on the first row of each block
    df[["year", "month"]] = df[["year", "month"]].ffill()
    df["date"] = pd.to_datetime(df["year"] + df["month"] + df["day"], format="%Y%b%d")

    # Keep interventions involving the yen only
    df = df[df["pair"].str.contains("Japanese yen")]

    # Amount in 100 million yen -> billions, + if Japan bought yen, - if sold
    amount = df["amount"].str.replace(",", "").astype(float) / 10
    df["amount_bn_jpy"] = amount.where(df["pair"].str.contains("yen (bought)", regex=False), -amount)

    # Some days had two operations (USD and EUR): add them up
    df = df.groupby("date")[["amount_bn_jpy"]].sum().loc[start:end]

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_FILE)
    return df
