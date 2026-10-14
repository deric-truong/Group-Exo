from pathlib import Path
import pandas as pd

#API upload
url = "https://stats.bis.org/api/v2/data/dataflow/BIS/WS_GLI/1.0/Q.JPY.3P.N.A.I.B.JPY?format=csv"
output_file = Path("data") / "bis_credit.parquet"   # changed: .csv -> .parquet

def download_credit(url):

    """Download BIS  data on yen-denominated credit to borrowers outside Japan"""

    raw = pd.read_csv(url)   # the download itself is still a CSV, so this stays

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
    credit["credit"] = credit["credit"]/1_000_000 #convert to trillions of yen

    return credit

def save_credit(credit, path):

    """Save a table of credit to a Parquet file, creating the folder if needed."""   # changed: CSV -> Parquet

    path.parent.mkdir(exist_ok=True) #mkdir creates the folder, exist_ok=T prevents  error if it already exists
    credit.to_parquet(path)   # changed: to_csv -> to_parquet

if __name__ == "__main__":
    credit = download_credit(url)
    save_credit(credit, output_file)
    print(credit.tail())