# Yen carry trade unwind (August 2024)

## Research question

How does the left tail of yen carry trade returns depend on speculative positioning, volatility and funding conditions, and does that relationship hold out of sample? The August 2024 unwind is the motivating episode.

## Hypotheses

- **H1**: Carry returns exhibit negative skewness and fat left tails.
- **H2**: Extreme speculative net-short yen positioning precedes lower forward carry returns.
- **H3**: A high carry-to-volatility ratio precedes worse worst-case outcomes.
- **H4**: Fast growth in yen credit to non-residents (BIS) precedes worse left-tail carry returns (funding channel).
- **H5**: The quantile regression forecasts the 5% quantile out of sample better than the historical quantile and the volatility-scaled normal (walk-forward).


## Data sources

| Source | Data | Module | Owner |
|--------|------|--------|-------|
| Yahoo Finance | FX, equities, Bitcoin, commodities | `src/data/yahoo.py` | Adam |
| FRED | US/Japan 3-month interbank rates (monthly, %) | `src/data/fred.py` | Deric |
| CFTC | Yen futures positioning | `src/data/cftc.py` | Thomas |
| BIS | Yen credit to borrowers outside Japan (quarterly, tn JPY) | `src/data/bis.py` | Adam |
| MoF Japan | FX interventions | `src/data/mof.py` | Thomas |

## Installation

This project requires Python 3.11 or newer. Install that version first; using
an older Python version will make the pinned pandas dependency fail to install.

Create and activate a virtual environment from the repository root, then install
the project's dependencies into it:

macOS / Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

Windows (PowerShell):

```powershell
py -3.11 -m venv .venv
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

## Analysis

Run each step from the repository root, in this order; each one reads the file
saved by the previous step:

```bash
python -m src.modelling_table            # saves data/modelling_table.parquet (weekly features and targets)
python -m src.data_description           # summary statistics and plots, saves data_des/*
python -m src.skewness_kurtosis          # H1: skewness and excess kurtosis of carry returns
python -m src.quantile_regressions       # H2-H4: in-sample quantile regressions, saves results/quantile_coefs.*
python -m src.walk_forward               # H5: walk-forward validation, saves results/walk_forward_*
python -m src.robustness.robustness_qr   # robustness of the quantile regressions, saves results/robustness_qr.csv
python -m src.robustness.robustness_wf   # robustness of the walk-forward, saves results/robustness_wf.csv
```

The walk-forward fits the quantile regression at each week on data known at
that date only (4-week embargo, features scaled on the training window), from
July 2012, and compares its 5% quantile forecast with the historical quantile
and a volatility-scaled normal (coverage, Kupiec test, pinball loss).

## Testing

Tests check the saved files in `data/`, so fetch the data first.
A test file is skipped (not failed) if its data has not been downloaded.

```bash
python -m pytest -v                      # run all tests
python -m pytest tests/test_cftc.py -v   # run one source only (or test_bis.py, test_yahoo.py, test_mof.py, test_fred.py, test_cleaning.py, test_modelling_table.py, test_walk_forward.py)
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
results/         outputs of the analysis (tables and figures)
data_des/        outputs of the data description
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

- Breaches of overlapping 4-week targets cluster (lag-1 autocorrelation 0.43, 29 breaches), so Kupiec p-values are too optimistic. Using every 4th week only, coverage is 3.3-4.9%, and the conclusion is unchanged.
- Only about 62 weeks fall in the worst 5% of 4-week carry returns, so tail estimates are imprecise and the August 2024 unwind weighs a lot on them.

## Team

| Member | Data retrieval | Analysis | Reviewed |
|--------|----------------|----------|----------|
| Adam Ouertani | Yahoo Finance, BIS | Modelling table, data description (H1), robustness checks | Quantile regressions |
| Quang Khai (Deric) Truong | FRED | Data validation, cleaning and merge, walk-forward validation (H5) | Robustness checks |
| Thomas Boulier | CFTC, MoF | Quantile regressions (H2-H4) | Modelling table, data description, walk-forward validation |

Each member wrote up their own phases in the report, reviewed by a teammate who did not write the section.
