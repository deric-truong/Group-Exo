# Yen carry trade unwind (August 2024)

## Research question

TODO

## Hypotheses

- **H1**: Carry returns exhibit negative skewness and fat left tails.
- **H2**: Extreme speculative net-short yen positioning precedes lower forward carry returns.
- **H3**: A high carry-to-volatility ratio precedes worse worst-case outcomes.

## Data sources

| Source | Data | Module | Owner |
|--------|------|--------|-------|
| Yahoo Finance | FX, equities, Bitcoin, commodities | `src/data/yahoo.py` | TODO |
| FRED | US/Japan 3-month rates | `src/data/fred.py` | TODO |
| CFTC | Yen futures positioning | `src/data/cftc.py` | TODO |

## Installation

```bash
pip install -r requirements.txt
```

Then run `main.ipynb` from top to bottom. Data is downloaded automatically into `data/` (not versioned).

## Repository structure

```
main.ipynb       final notebook
src/config.py    analysis window, tickers, series IDs
src/data/        one retrieval module per source
src/             cleaning and analysis modules
notebooks/       individual exploration notebooks
docs/            data cleaning decisions log
```

## Limitations

TODO

## Team

TODO
