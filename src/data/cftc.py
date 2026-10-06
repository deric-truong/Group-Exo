"""Retrieve yen futures positioning from the CFTC Commitments of Traders.

Source: CFTC "Legacy - Futures Only" historical files
(https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed).
The CFTC publishes one zip covering 1986-2016, then one zip per year.
Each zip holds a single CSV with every futures market; we keep the
Japanese yen contract only (CME, contract code 097741).

Positions are measured on Tuesday and published on Friday, so each
observation is indexed by its (approximate) release date to avoid
using information the market did not have yet.

Owner: TODO
"""

import io
import zipfile

import pandas as pd
import requests

from src import config

BASE_URL = "https://www.cftc.gov/files/dea/history/"
# Single bundle covering all years up to 2016, then one file per year
BUNDLE_FILE = "deacot1986_2016.zip"
BUNDLE_LAST_YEAR = 2016

RAW_CFTC_DIR = config.RAW_DIR / "cftc"
OUTPUT_FILE = config.PROCESSED_DIR / "cftc_jpy.parquet"

# Original CFTC column names -> short names used in the project
COLUMNS = {
    "As of Date in Form YYYY-MM-DD": "report_date",
    "CFTC Contract Market Code": "contract_code",
    "Open Interest (All)": "open_interest",
    "Noncommercial Positions-Long (All)": "spec_long",
    "Noncommercial Positions-Short (All)": "spec_short",
}


def _files_to_download(start_year, end_year):
    """Return the list of CFTC zip names covering [start_year, end_year]."""
    files = []
    if start_year <= BUNDLE_LAST_YEAR:
        files.append(BUNDLE_FILE)
    first_yearly = max(start_year, BUNDLE_LAST_YEAR + 1)
    files += [f"deacot{year}.zip" for year in range(first_yearly, end_year + 1)]
    return files


def _download(filename, force=False):
    """Download one zip into data/raw/cftc/ (skipped if already cached)."""
    path = RAW_CFTC_DIR / filename
    if path.exists() and not force:
        return path

    RAW_CFTC_DIR.mkdir(parents=True, exist_ok=True)
    response = requests.get(BASE_URL + filename, timeout=120)
    response.raise_for_status()
    path.write_bytes(response.content)
    return path


def _read_yen_rows(path):
    """Read one CFTC zip and keep the yen contract rows and useful columns."""
    with zipfile.ZipFile(path) as archive:
        # Each archive contains a single CSV (annual.txt or FUT86_16.txt)
        csv_name = archive.namelist()[0]
        raw = archive.read(csv_name)

    df = pd.read_csv(
        io.BytesIO(raw),
        usecols=list(COLUMNS),
        dtype={"CFTC Contract Market Code": str},  # keep the leading zero
        skipinitialspace=True,  # numbers are left-padded with spaces
        encoding="latin-1",
    )
    df = df.rename(columns=COLUMNS)

    # Filter on the contract code rather than the market name:
    # the name changed over time ("INTERNATIONAL MONETARY MARKET" -> "CHICAGO
    # MERCANTILE EXCHANGE") while the code stayed the same.
    is_yen = df["contract_code"].str.strip() == config.CFTC_JPY_CODE
    return df.loc[is_yen].drop(columns="contract_code")


def fetch_cftc(start=config.START, end=config.END, force=False, save=True):
    """Download yen speculative positioning and return a weekly DataFrame.

    Parameters
    ----------
    start, end : str
        Analysis window ("YYYY-MM-DD"), filtered on the report date.
    force : bool
        Re-download the raw zips even if they are already cached.
    save : bool
        Also write the result to data/processed/cftc_jpy.parquet.

    Returns
    -------
    pandas.DataFrame indexed by ``release_date`` with columns:
        report_date      Tuesday the positions were measured
        open_interest    total open contracts
        spec_long        non-commercial (speculative) long contracts
        spec_short       non-commercial (speculative) short contracts
        spec_net         spec_long - spec_short (< 0 = net short yen)
        spec_net_pct_oi  spec_net / open_interest, comparable across years
    """
    start, end = pd.Timestamp(start), pd.Timestamp(end)

    files = _files_to_download(start.year, end.year)
    frames = [_read_yen_rows(_download(name, force=force)) for name in files]
    df = pd.concat(frames, ignore_index=True)

    df["report_date"] = pd.to_datetime(df["report_date"])
    df = (
        df.drop_duplicates(subset="report_date")
        .sort_values("report_date")
        .loc[lambda d: d["report_date"].between(start, end)]
    )

    # Futures are quoted in USD per JPY: a net short position is a bet on a
    # weaker yen, i.e. the same direction as a long USD/JPY carry trade.
    df["spec_net"] = df["spec_long"] - df["spec_short"]
    # Normalise by open interest so that 2007 and 2024 levels are comparable
    df["spec_net_pct_oi"] = df["spec_net"] / df["open_interest"]

    # Publication lag: Tuesday data is released on Friday (+3 days).
    # Approximation: holiday weeks are sometimes released one day later.
    lag = pd.Timedelta(days=config.CFTC_PUBLICATION_LAG_DAYS)
    df["release_date"] = df["report_date"] + lag
    df = df.set_index("release_date")

    if save:
        config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(OUTPUT_FILE)

    return df
