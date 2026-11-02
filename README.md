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
| BIS | Yen credit to borrowers outside Japan (quarterly, tn JPY) | `src/data/bis.py` | TODO |
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
python -m pytest tests/test_cftc.py -v   # run one source only (or test_bis.py, test_yahoo.py, test_mof.py)
python -m pytest -v tests/test_bis.py -v
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

- BIS credit is quarterly and published with a lag. Its `release_date` assumes
  4 months after quarter end, an approximation still to be checked against the
  BIS release calendar. Past quarters are also revised, so re-fetch before
  final results.
- MoF interventions are indexed by the day they happened, but daily details are
  only published with the quarterly report. `release_date` assumes quarter end
  + 45 days, on or after every release checked (e.g. Q3 2024 out on 8 Nov 2024).
  MoF also publishes a monthly total (no daily split) around month end, which
  reveals an intervention earlier; this is not used here.
- Yahoo prices are closes in different time zones: the Nikkei closes about
  15 hours before US markets, so the same date is not the same moment.
- Gold (`GC=F`) and Brent (`BZ=F`) are continuous futures; prices can jump
  when one contract rolls into the next.
- TODO

## Team

TODO
