import pandas as pd
from src import config

OUTPUT_FILE = config.DIRECTORY / "bis_credit.parquet"


def download_credit(url=config.BIS_CREDIT_URL, start=config.START, end=config.END):
    """Download BIS  data on yen-denominated credit to borrowers outside Japan"""

    raw = pd.read_csv(url)

    #filtering for just the data we need
    credit = raw[["TIME_PERIOD", "OBS_VALUE"]].copy() #had to make a copy to avoid error message

    #converting the text date to a period index
    quarters = pd.PeriodIndex(credit["TIME_PERIOD"], freq="Q")

    #changing from quarter to day (picked last day of quarter)
    credit["TIME_PERIOD"] = quarters.to_timestamp(how="end").normalize() #remove time

    #create new dataframe with the format we want
    credit = credit.rename(columns={"OBS_VALUE": "credit", "TIME_PERIOD": "date"})
    credit = credit[["date", "credit"]]
    credit = credit.set_index("date").sort_index()

    #format credit column
    credit["credit"] = credit["credit"] / 1_000_000
    credit = credit.loc[start:end]

    return credit


def save_credit(credit, path=OUTPUT_FILE):
    """Save a table of credit to a Parquet file, creating the folder if needed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    credit.to_parquet(path)

if __name__ == "__main__":
    credit = download_credit()
    save_credit(credit)
    print(f"Saved {len(credit)} rows to {OUTPUT_FILE}")
    print(credit.tail())