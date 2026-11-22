"""
Phase 4: walk-forward validation of the 5% quantile of 4-week carry returns

At each week t, fit the quantile regression on data known at t only,
forecast the 5% quantile, and compare with two benchmarks.
Functions take tau, target and horizon so robustness checks can reuse them.
Run with ''python -m src.walk_forward''
results go to ''results/''.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from matplotlib.ticker import PercentFormatter
from scipy import stats

from src import config
from src.quantile_regressions import FEATURES, RESULTS, TARGET

TAU = 0.05                          # default quantile we forecast (left tail)
HORIZON = pd.Timedelta(weeks=4)     # default horizon of the forecast
TRAIN_YEARS = 10                    # first training window (decision locked on 6 Nov 2020)


def load_data():
    """ Weeks where all features are known; targets may be NaN at the very end.
    
    No scaling here: scaling with full-sample statistics would leak the future.
    """

    df = pd.read_parquet(config.DIRECTORY/ "modelling_table.parquet")
    cols = ["fwd_carry_4w","fwd_carry_1w", "rv_20d"] + FEATURES
    return df[cols].dropna(subset=["rv_20d"] + FEATURES)

def forecast_at(df, t, tau=TAU, target=TARGET, horizon=HORIZON):
    """Forecast at the tau-quantile of 'target' for week t using only data known at t."""

    # Embargo: the target of week s is only known at s + horizon 
    train = df[df.index <= t - horizon].dropna(subset=[target])

    # Scale with training statistics only, then apply them to week t
    mu, sd = train[FEATURES].mean(), train[FEATURES].std()
    scaled = train.copy()
    scaled[FEATURES] = (train[FEATURES] - mu) / sd
    x_t = df.loc[[t], FEATURES].sub(mu).div(sd)

    formula = f"{target} ~ " + " + ".join(FEATURES)
    model = smf.quantreg(formula, scaled).fit(q=tau)

    # Benchmark 2: annual volatility scaled to the horizon (5 trading days a week)
    trading_days = horizon.days * 5 / 7
    sigma_h = df.loc[t, "rv_20d"] * np.sqrt(trading_days / 252)

    # ppf = percentage point function = inverse of the CDF, so it gives the quantile of a normal distribution
    return {
        "model": float(model.predict(x_t).iloc[0]),
        "hist": train[target].quantile(tau),
        "normal":train[target].mean() + stats.norm.ppf(tau) * sigma_h
    }

def walk_forward(df, tau=TAU, target=TARGET, horizon=HORIZON):
    """Expanding-window forecasts for every test week whose outcome is known."""

    start = df.index[0] + pd.DateOffset(years=TRAIN_YEARS)
    test_dates = df.loc[start:].dropna(subset=[target]).index
    rows = [
        {"date": t,"realised": df.loc[t,target],
         **forecast_at(df, t, tau, target, horizon)}
        for t in test_dates
    ]
    return pd.DataFrame(rows).set_index("date")

def pinball(y, q, tau=TAU):
    """Average qunantile (pinball) loss: lower is better."""
    diff = y - q
    return np.mean(np.maximum(tau * diff, (tau - 1) * diff))

def kupiec_pvalue(hits, tau=TAU):
    """P-value of the Kupiec test for correct coverage of the tau-quantile.
    Kupiec test p-value: is the breach rate compatible with tau?
    H0: the realised quantile is correct, i.e. the realised hits are Bernoulli(tau).
    H1: the realised quantile is incorrect, i.e. the realised hits are Bernoulli(p) with p != tau.
    """
    n, x = len(hits), int(hits.sum())
    if x in (0,n):
        return np.nan

    p = x/n
    
    lr = -2 * ((n - x) * np.log(1 - tau) + x * np.log(tau)
               - (n - x) * np.log(1 - p) - x * np.log(p))
    return 1 - stats.chi2.cdf(lr, df=1)

# fc = forecast
def score(fc, tau=TAU):
    """Coverage, Kupiec p-value, pinball loss and skill versus the historical quantile."""
    out = {}
    for m in ["model", "hist", "normal"]:
        hits = fc["realised"] < fc[m]
        out[m] = {
            "coverage": hits.mean(),
            "kupiec_p": kupiec_pvalue(hits, tau),
            "pinball": pinball(fc["realised"], fc[m], tau),
        }
    table = pd.DataFrame(out).T
    table["skill_vs_hist"] = 1 - table["pinball"] / table.loc["hist", "pinball"]
    return table

def plot(fc, path, title):
    """Realised returns against the three quantile forecasts, breaches in red."""
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(fc.index, fc["realised"], color="grey", lw=0.8, label="Realised 4-week carry return")
    ax.plot(fc.index, fc["model"], label="Quantile model (5%)")
    ax.plot(fc.index, fc["hist"], ls="--", label="Historical 5% quantile")
    ax.plot(fc.index, fc["normal"], ls=":", label="Vol-scaled normal (5%)")
    hits = fc[fc["realised"] < fc["model"]]
    ax.scatter(hits.index, hits["realised"], color="red", s=12, zorder=3,
               label="Breach of model forecast")
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_ylabel("4-week carry return")
    ax.set_title(title)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run():
    """Main case (4 weeks, 5% tail): save forecasts, scores (CSV) and figures (PNG)."""
    fc = walk_forward(load_data())
    table = pd.concat({
        "all": score(fc),
        "without_2024": score(fc[fc.index.year != 2024]),
    })

    RESULTS.mkdir(exist_ok=True)
    fc.to_csv(RESULTS / "walk_forward_forecasts.csv")
    table.to_csv(RESULTS / "walk_forward_scores.csv")
    plot(fc, RESULTS / "walk_forward.png",
         "Walk-forward forecasts of the 5% quantile, 2012-2026")
    plot(fc.loc["2024-04":"2024-10"], RESULTS / "walk_forward_2024.png",
         "Walk-forward forecasts around the August 2024 unwind")
    return table


if __name__ == "__main__":
    print(run().round(4).to_string())




