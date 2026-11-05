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
| FRED | US/Japan 3-month interbank rates (monthly, %) | `src/data/fred.py` | TODO |
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
python -m pip install -e .
```

Windows (PowerShell):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

Run `main.ipynb` with the `.venv` environment selected as the notebook kernel.
The same environment must be used when running Python scripts. Data is
downloaded automatically into `data/` (not versioned).

## Fetching data

With the editable install above, each source can be run directly from its file
path, from the repository root:

```bash
python src/data/yahoo.py   # FX, equities, BTC, commodities
python src/data/fred.py    # US/Japan 3-month rates
python src/data/cftc.py    # yen futures positioning
python src/data/bis.py     # BIS credit data
python src/data/mof.py     # MoF interventions
```

Alternatively, run them as modules from the repository root:

```bash
python -m src.data.yahoo   # FX, equities, BTC, commodities
python -m src.data.fred    # US/Japan 3-month rates
python -m src.data.cftc    # yen futures positioning
python -m src.data.bis     # BIS credit data
python -m src.data.mof     # MoF interventions
```

Each command saves its output to `data/` and prints the row count.

## Cleaning and merging

Once every source is fetched, build the merged daily table from the repository root:

```bash
python -m src.cleaning   # saves data/merged_daily.parquet
```

One row per USD/JPY trading day, from `START` to `END`:

| Columns | Meaning | Use for |
|---------|---------|---------|
| `usdjpy` … `vix` | Yahoo closes, NaN when that market was closed (not filled) | returns |
| `us_3m`, `jp_3m`, `rate_diff` | rate of the day's month | carry accrual, event study |
| `*_known` (rates, CFTC, BIS `credit_known`) | latest value public on that day, used from the trading day after `release_date` | predictive tests (H2, H3) |
| `intervention_bn_jpy` | MoF intervention on that day (> 0 = yen bought), 0 if none | event study |

CFTC reports delayed by a shutdown are left out of the `_known` columns; the
last on-time report is carried forward instead.

## Testing

Tests check the saved files in `data/`, so fetch the data first.
A test file is skipped (not failed) if its data has not been downloaded.

```bash
python -m pytest -v                      # run all tests
python -m pytest tests/test_cftc.py -v   # run one source only (or test_bis.py, test_yahoo.py, test_mof.py, test_fred.py, test_cleaning.py)
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

## Date conventions

Every source is indexed by the date its value refers to, with the day it became
public in a `release_date` column:

| Source | Index | `release_date` |
|--------|-------|----------------|
| Yahoo | trading day | — (known on the day) |
| FRED | month start | month start + 3 months |
| CFTC | report date (Tuesday) | next Friday |
| BIS | quarter end | quarter end + 4 months |
| MoF | intervention day | quarter end + 45 days |

Which date to align on depends on the test:

- **Event study** → the index (event date). Markets react the same day: the
  11–12 July 2024 interventions moved USD/JPY at once, while their
  `release_date` is 14 Nov 2024.
- **Forward-return / predictive tests (H2, H3)** → `release_date`, so that only
  data public at the time is used.

The download window is fixed in `src/config.py` (`START = 2000-01-01`,
`END = 2026-09-30`) so results do not change between runs. Tests that need the
US–JP rate differential start at `ANALYSIS_START = 2002-04-01` (first jp_3m value).

## Limitations

- BIS credit is quarterly and published with a lag. Its `release_date` assumes
  4 months after quarter end (checked: 2026-Q2 came out on 29 Oct 2026). Past quarters are also revised, so re-fetch before
  final results.
- MoF interventions are indexed by the day they happened, but daily details are
  only published with the quarterly report. `release_date` assumes quarter end
  + 45 days, on or after every release checked (e.g. Q3 2024 out on 8 Nov 2024).
  MoF also publishes a monthly total (no daily split) around month end, which
  reveals an intervention earlier; this is not used here.
- FRED rates are monthly averages (except `jp_3m` from 2025-01, see below). `release_date` assumes 3 months after the
  month start; the October 2026 update had US data about 1.5 months and JP
  about 2.5 months after the month start, so this is on the safe side (past
  release dates not checked). `jp_3m` starts only in 2002-04 and changes
  underlying rate in 2025-01. From then on it equals the month-end 3-month JBA
  Japanese Yen TIBOR (a month-end value, not an average); in 2024 it was 6–23bp
  below that rate. Results are checked without the Dec 2024 → Jan 2025 change.
- Yahoo prices are closes in different time zones: the Nikkei closes about
  15 hours before US markets, so the same date is not the same moment.
- Gold (`GC=F`) and Brent (`BZ=F`) are continuous futures; prices can jump
  when one contract rolls into the next.
- TODO

## Team

TODO
