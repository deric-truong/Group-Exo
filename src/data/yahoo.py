
import yfinance as yf

from src import config

OUTPUT_FILE = config.DIRECTORY / "yahoo_prices.parquet"


def download_prices(
    tickers=config.YAHOO_TICKERS,
    start=config.START,
    end=config.END,
):
    """Download daily prices of related assets from Yahoo Finance."""

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

def save_prices(prices, path=OUTPUT_FILE):
    """Save a table of prices to a Parquet file, creating the folder if needed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    prices.to_parquet(path)


if __name__ == "__main__":
    prices = download_prices()
    save_prices(prices)
    print(f"Saved {len(prices)} rows to {OUTPUT_FILE}")
    print(prices.tail())