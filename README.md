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
| BIS | Credit data | `src/data/bis.py` | TODO |
| MoF Japan | FX interventions | `src/data/mof.py` | TODO |

## Installation

Create and activate a virtual environment from the repository root, then install
the project's dependencies into it:

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run `main.ipynb` with the `.venv` environment selected as the notebook kernel.
The same environment must be used when running Python scripts. Data is
downloaded automatically into `data/` (not versioned).

## Fetching data

Each source can be downloaded on its own from the repository root (use `-m`,
not the file path, so `src` imports resolve):

```bash
python -m src.data.yahoo   # FX, equities, BTC, commodities
python -m src.data.fred    # US/Japan 3-month rates
python -m src.data.cftc    # yen futures positioning
python -m src.data.bis     # BIS credit data
python -m src.data.mof     # MoF interventions
```

Each command saves its output to `data/` and prints the row count.

## Testing

Tests check the saved files in `data/`, so fetch the data first.
A test file is skipped (not failed) if its data has not been downloaded.

```bash
python -m pytest -v                      # run all tests
python -m pytest tests/test_cftc.py -v   # run one source only
```

After pulling changes to a module in `src/data/`, re-run its fetch command
before testing, otherwise the tests check the old file.

## Repository structure

```
main.ipynb       final notebook
src/config.py    analysis window, tickers, series IDs
src/data/        one retrieval module per source
src/             cleaning and analysis modules
tests/           checks on the downloaded data (pytest)
notebooks/       individual exploration notebooks
docs/            data cleaning decisions log
```

## Limitations

TODO

## Team

TODO
