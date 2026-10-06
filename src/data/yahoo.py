"""Download daily prices from Yahoo Finance and save them as a CSV file."""

from pathlib import Path

import pandas as pd
import yfinance as yf

# Our own short names on the left, Yahoo Finance's ticker codes on the right.
TICKERS = {
    "usdjpy": "JPY=X",
    "nikkei": "^N225",
    "nasdaq": "^IXIC",
    "sp500": "^GSPC",
    "bitcoin": "BTC-USD",
    "usdmxn": "MXN=X",
    "gold": "GC=F",
    "brent": "BZ=F",
    "vix": "^VIX",
}

START_DATE = "2005-01-01"
END_DATE = "2025-12-31"  # Yahoo treats the end date as exclusive
OUTPUT_FILE = Path("data") / "yahoo_prices.csv"


def download_prices(tickers, start, end):
    """Download daily closing prices and return one column per asset."""
    raw = yf.download(
        list(tickers.values()),
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    closes = raw["Close"]  # keep only the closing prices

    # Replace Yahoo's codes (JPY=X) with our own names (usdjpy).
    names = {ticker: name for name, ticker in tickers.items()}
    closes = closes.rename(columns=names)

    # Stop with a clear message if an asset did not download.
    missing = [
        name
        for name in tickers
        if name not in closes.columns or closes[name].isna().all()
    ]
    if missing:
        raise ValueError(f"No data came back for: {missing}")

    closes = closes[list(tickers)]  # same column order as TICKERS
    closes.index.name = "date"
    return closes


def save_prices(prices, path):
    """Save a table of prices to a CSV file, creating the folder if needed."""
    path.parent.mkdir(exist_ok=True)
    prices.to_csv(path)


if __name__ == "__main__":
    prices = download_prices(TICKERS, START_DATE, END_DATE)
    save_prices(prices, OUTPUT_FILE)
    print(prices.tail())