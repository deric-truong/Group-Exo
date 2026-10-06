import pandas as pd

url = "https://stats.bis.org/api/v2/data/dataflow/BIS/WS_GLI/1.0/Q.JPY.3P.N.A.I.B.JPY?format=csv"
raw = pd.read_csv(url)

credit = raw[["TIME_PERIOD", "OBS_VALUE"]]

print(credit.head())

