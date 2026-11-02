"""Retrieve Japan's foreign exchange interventions from the Ministry of Finance.

Source: MoF "Foreign Exchange Intervention Operations"
(https://www.mof.go.jp/english/policy/international_policy/reference/feio/index.html).
One bilingual CSV (Shift-JIS) lists every intervention day since April 1991.

Daily details are only disclosed after the end of each quarter, so the index is
the day of the intervention and ``release_date`` the day it became public.

Owner: TODO
"""

import io

import pandas as pd
import requests

from src import config

OUTPUT_FILE = config.DIRECTORY / "mof_interventions.parquet"

# Days in a quarter are rounded, so their sum can differ a little from the
# quarterly total (MoF note 2). Seen up to 2 (x 100 million yen).
TOTAL_TOLERANCE = 5


def fetch_mof(start=config.START, end=config.END):
    """Download the MoF file and return yen interventions (see ``parse_mof``).

    The result is also saved to ``data/mof_interventions.parquet``.
    """
    response = requests.get(config.MOF_INTERVENTIONS_URL, timeout=60)
    response.raise_for_status()

    df = parse_mof(response.content).loc[start:end]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_FILE)
    return df


def parse_mof(content):
    """Return yen interventions from the raw MoF CSV, one row per intervention day.

    Index: intervention date

    Columns:
        amount_bn_jpy   total size in billions of yen, signed:
                        > 0 = yen bought (to stop the yen falling)
                        < 0 = yen sold (to stop the yen rising)
        release_date    approximate date the day became public (no look-ahead)
    """
    raw = pd.read_csv(
        io.BytesIO(content),
        encoding="cp932",  # Japanese Shift-JIS encoding
        header=None,
        dtype=str,
    )

    # validate the file before using it: fail loudly if MoF changes the format
    if raw.shape[1] != 9:
        raise ValueError(f"MoF file has {raw.shape[1]} columns, expected 9")

    # Keep the English columns only (the first 3 are Japanese dates)
    # and the Japanese label (column 0) to find the quarterly totals ("期計")
    df = raw[[0, 3, 4, 5, 6, 8]].copy()
    df.columns = ["label", "year", "month", "day", "amount", "pair"]
    df["amount"] = df["amount"].str.replace(",", "")

    # Intervention days are the rows with a numeric day
    # (titles, notes and quarterly totals are dropped)
    is_day = df["day"].str.isdigit().fillna(False)
    is_total = df["label"].str.contains("期計").fillna(False)
    if not is_day.any():
        raise ValueError("MoF file has no intervention rows")

    # Each day must add up to its quarterly total (the total row comes after its days)
    quarter = is_total[::-1].cumsum()[::-1]
    day_sums = df.loc[is_day, "amount"].astype(float).groupby(quarter[is_day]).sum()
    totals = df.loc[is_total, "amount"].astype(float).groupby(quarter[is_total]).sum()
    gap = day_sums.sub(totals, fill_value=0).abs()
    if (gap > TOTAL_TOLERANCE).any():
        raise ValueError("MoF daily amounts do not add up to the quarterly totals")

    df = df[is_day]

    # Year and month are only written on the first row of each block
    df[["year", "month"]] = df[["year", "month"]].ffill()
    df["date"] = pd.to_datetime(df["year"] + df["month"] + df["day"], format="%Y%b%d")
    if not df["date"].is_monotonic_increasing:
        raise ValueError("MoF dates are out of order, year/month fill went wrong")

    # Keep interventions involving the yen only
    df = df[df["pair"].str.contains("Japanese yen")]
    bought = df["pair"].str.contains("yen (bought)", regex=False)
    sold = df["pair"].str.contains("yen (sold)", regex=False)
    if not (bought ^ sold).all():
        raise ValueError("MoF currency pair not recognised as yen bought or sold")

    # Amount in 100 million yen -> billions, + if Japan bought yen, - if sold
    amount = df["amount"].astype(float) / 10
    df["amount_bn_jpy"] = amount.where(bought, -amount)

    # Some days had two operations (USD and EUR): add them up
    df = df.groupby("date")[["amount_bn_jpy"]].sum()

    # Daily details come out with the quarterly report, after quarter end
    quarter_end = df.index.to_period("Q").to_timestamp(how="end").normalize()
    df["release_date"] = quarter_end + pd.Timedelta(days=config.MOF_RELEASE_LAG_DAYS)
    return df


if __name__ == "__main__":
    interventions = fetch_mof()
    print(f"Saved {len(interventions)} rows to {OUTPUT_FILE}")
