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
