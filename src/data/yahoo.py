
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

    for name in config.YAHOO_SPIKE_CHECK:
        if name in closes.columns:
            closes[name] = remove_spikes(closes[name])

    return closes


def remove_spikes(prices, jump=0.03, reverse=0.02):
    """Replace one-day bad prints with NaN.

    A price is a bad print when it jumps more than `jump` away from both the
    day before and the day after, in the same direction, while those two days
    stay within `reverse` of each other (the price goes straight back).
    Example: USD/JPY 2008-12-08 = 109.24 between 92.82 and 92.30.
    """

    s = prices.dropna()
    before, after = s.shift(1), s.shift(-1)
    bad = (
        ((s / before - 1).abs() > jump)
        & ((s / after - 1).abs() > jump)
        & ((after / before - 1).abs() < reverse)
        & ((s - before) * (s - after) > 0)  #higher (or lower) than both neighbours
    )

    prices = prices.copy()
    prices[bad[bad].index] = float("nan")
    return prices

def save_prices(prices, path=OUTPUT_FILE):
    """Save a table of prices to a Parquet file, creating the folder if needed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    prices.to_parquet(path)


if __name__ == "__main__":
    prices = download_prices()
    save_prices(prices)
    print(f"Saved {len(prices)} rows to {OUTPUT_FILE}")
    print(prices.tail())