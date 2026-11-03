import pandas as pd
from src import config

OUTPUT_FILE = config.DIRECTORY / "bis_credit.parquet"


def download_credit(url=config.BIS_CREDIT_URL, start=config.START, end=config.END):
    """Download BIS  data on yen-denominated credit to borrowers outside Japan

    Index: quarter-end date (when the stock is measured)

    Columns:
        credit         bank loans + debt securities, in trillions of yen
        release_date   approximate date the quarter became public (no look-ahead)
    """

    raw = pd.read_csv(url)

    #validate the file before using it: fail loudly if BIS changes the format
    if raw["UNIT_MEASURE"].nunique() != 1 or raw["UNIT_MULT"].nunique() != 1:
        # (data homogeneity): check that dataset contains exactly one unique unit of measurement + one unique multiplier
        raise ValueError("BIS file mixes several series or units")
    if raw["UNIT_MEASURE"].iloc[0] != "JPY" or raw["UNIT_MULT"].iloc[0] != 6:
        #(math scale): verif format of dataset, currency is Japanese Yen, multiplier is 10^6 (millions)
        raise ValueError("BIS units changed, the conversion to trillions is wrong")
    if raw["TIME_PERIOD"].duplicated().any():
        # (uniqueness - time series integrity): no duplicate dates or quarters in the timeline
        raise ValueError("BIS file has duplicate quarters")
    # coercion and cleaning: convert the OBS_VALUE column to numeric, dropping rows that cannot be converted (e.g., missing or malformed data)
    raw["OBS_VALUE"] = pd.to_numeric(raw["OBS_VALUE"], errors="coerce")
    raw = raw.dropna(subset=["OBS_VALUE"])

    #filtering for just the data we need
    credit = raw[["TIME_PERIOD", "OBS_VALUE"]].copy() #had to make a copy to avoid error message

    #converting the text date to a period index
    quarters = pd.PeriodIndex(credit["TIME_PERIOD"], freq="Q")

    #changing from quarter to day (picked last day of quarter)
    credit["TIME_PERIOD"] = quarters.to_timestamp(how="end").normalize() #remove time

    #create new dataframe with the format we want
    credit = credit.rename(columns={"OBS_VALUE": "credit", "TIME_PERIOD": "date"})
    credit = credit[["date", "credit"]]

    #format credit column
    #BIS reports in millions of yen (UNIT_MEASURE = JPY, UNIT_MULT = 6),
    #so dividing by 1,000,000 gives trillions of yen (e.g. 2026-Q1 = 65.9 tn JPY)
    credit["credit"] = credit["credit"] / 1_000_000
    credit = credit.set_index("date").sort_index().loc[start:end]

    #BIS publishes each quarter with a lag of about 4 months,
    #so the value is only usable from release_date on
    credit["release_date"] = credit.index + pd.DateOffset(months=config.BIS_RELEASE_LAG_MONTHS)

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