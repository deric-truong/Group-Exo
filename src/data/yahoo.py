
from pathlib import Path
import pandas as pd
import yfinance as yf

#our own short names on the left, Yahoo Finance's ticker codes on the right
tickers = {"usdjpy": "JPY=X", "nikkei": "^N225", "nasdaq": "^IXIC", "sp500": "^GSPC", "bitcoin": "BTC-USD", "usdmxn": "MXN=X", "gold": "GC=F", "brent": "BZ=F", "vix": "^VIX"}

start_date = "2005-01-01"
end_date = pd.Timestamp.today().strftime("%Y-%m-%d")
output_file = Path("data") / "yahoo_prices.csv"


def download_prices(tickers, start, end):

    """Download daily prices of various related assets from Yahoo Finance"""   

    raw = yf.download(list(tickers.values()), start=start, end=end, auto_adjust=True, progress=False, threads=False)
    closes = raw["Close"]  # keep only the closing prices

    #replace Yahoo's codes with our own
    names = {ticker: name for name, ticker in tickers.items()}
    closes = closes.rename(columns=names)

    #stop with a clear message if an asset did not download
    missing = [name 
               for name in tickers 
               if name not in closes.columns or closes[name].isna().all()]
    if missing:
        raise ValueError(f"No data came back for: {missing}")

    closes = closes[list(tickers)]  #put in same column order as tickers
    closes.index.name = "date"

    return closes

def save_prices(prices, path):

    """Save a table of prices to a CSV file, creating the folder if needed."""

    path.parent.mkdir(exist_ok=True) #mkdir creates the folder, exist_ok=T prevents  error if it already exists
    prices.to_csv(path)


if __name__ == "__main__":
    prices = download_prices(tickers, start_date, end_date)
    save_prices(prices, output_file)
    print(prices.tail())