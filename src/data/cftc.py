"""Retrieve yen futures positioning from the CFTC Commitments of Traders.

Source: CFTC "Legacy - Futures Only" historical files
(https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed).
The CFTC publishes one zip covering 1986-2016, then one zip per year.
Each zip holds a CSV with every futures market; we keep the Japanese yen
contract only (CME, contract code 097741).

Positions are measured on Tuesday and published on Friday, so each
observation is indexed by its release date to avoid look-ahead bias.

Owner: TODO
"""

import io
import zipfile

import pandas as pd
import requests

from src import config

OUTPUT_FILE = config.DIRECTORY / "cftc_jpy.parquet"

# Original CFTC column names -> short names used in the project
COLUMNS = {
    "As of Date in Form YYYY-MM-DD": "report_date",
    "CFTC Contract Market Code": "contract_code",
    "Open Interest (All)": "open_interest",
    "Noncommercial Positions-Long (All)": "spec_long",
    "Noncommercial Positions-Short (All)": "spec_short",
}


def _read_yen_rows(filename):
    """Download one CFTC zip in memory and return the yen rows."""
    response = requests.get(config.CFTC_HISTORY_BASE_URL + filename, timeout=120)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        csv_name = next(name for name in archive.namelist() if not name.endswith("/"))
        with archive.open(csv_name) as csv_file:
            df = pd.read_csv(
                csv_file,
                usecols=list(COLUMNS),
                dtype={"CFTC Contract Market Code": str},  # keep the leading zero
                skipinitialspace=True,  # numbers are left-padded with spaces
                encoding="latin-1",
            ).rename(columns=COLUMNS)

    # Filter on the code, not the name: the market name changed over time
    return df[df["contract_code"].str.strip() == config.CFTC_JPY_CODE]

def save_cftc(df, path=OUTPUT_FILE):
    """Save the CFTC table to a Parquet file, creating the folder if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path)


def fetch_cftc(start=config.START, end=config.END):
    """Return weekly yen speculative positioning, indexed by release date.

    Columns:
        report_date      Tuesday the positions were measured
        open_interest    total open contracts
        spec_long        non-commercial (speculative) long contracts
        spec_short       non-commercial (speculative) short contracts
        spec_net         spec_long - spec_short (< 0 = net short yen)
        spec_net_pct_oi  spec_net / open_interest, comparable across years
        delayed_release  True if publication was delayed by a shutdown
    """
    # 1986-2016 bundle (our window starts in 2000), then one file per year
    end_year = pd.Timestamp(end).year
    files = ["deacot1986_2016.zip"]
    files += [f"deacot{year}.zip" for year in range(2017, end_year + 1)]

    df = pd.concat([_read_yen_rows(name) for name in files])
    df["report_date"] = pd.to_datetime(df["report_date"])
    df = df[df["report_date"].between(start, end)].sort_values("report_date")

    # Futures are quoted in USD per JPY: net short = betting on a weaker yen,
    # the same direction as a long USD/JPY carry trade
    df["spec_net"] = df["spec_long"] - df["spec_short"]
    # Normalise by open interest so that 2007 and 2024 levels are comparable
    df["spec_net_pct_oi"] = df["spec_net"] / df["open_interest"]

    # Positions are measured on Tuesday and released the following Friday.
    # In holiday weeks the measurement day moves (Monday, Wednesday...),
    # so we roll each report date forward to the next Friday instead of
    # adding a fixed 3 days.
    # Week(weekday=4) = "next Friday"; a date that is already a Friday
    # goes to the Friday after it, which is the safe (later) choice.
    df["release_date"] = df["report_date"] + pd.offsets.Week(weekday=4)

    # Flag reports whose publication was delayed by a government shutdown:
    # the "next Friday" rule is wrong for them (see config.CFTC_DELAYED_WINDOWS)
    df["delayed_release"] = False
    for start_delay, end_delay in config.CFTC_DELAYED_WINDOWS:
        in_window = df["report_date"].between(start_delay, end_delay)
        df.loc[in_window, "delayed_release"] = True


    df = df.drop(columns="contract_code").set_index("release_date")
    return df


if __name__ == "__main__":
    cftc = fetch_cftc()
    save_cftc(cftc) # saving now happens here, not inside fetch_cftc()
    print(f"Saved {len(cftc)} rows to {OUTPUT_FILE}")
