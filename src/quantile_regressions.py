"""Phase 3: in-sample quantile regressions of the 4-week forward carry return.

Compare the effect of each feature on the left tail (5%), the median and the
right tail (95%) with its effect on the mean (OLS).
Run with ``python -m src.quantile_regressions``; results go to ``results/``.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from src import config

TARGET = "fwd_carry_4w"
FEATURES = ["spec_net_z", "carry_to_vol", "vix", "credit_yoy"]
FORMULA = f"{TARGET} ~ " + " + ".join(FEATURES)
QUANTILES = [0.05, 0.5, 0.95]

# 4-week targets overlap and the features are persistent, so bootstrap blocks
# of 12 consecutive weeks (one quarter) instead of single weeks
BLOCK = 12
N_BOOT = 500
RESULTS = config.ROOT / "results"


def load_data(target=TARGET):
    """Return complete weeks for the target with features scaled to mean 0, std 1."""
    df = pd.read_parquet(config.DIRECTORY / "modelling_table.parquet")
    df = df[[target] + FEATURES].dropna()
    # In-sample scaling: each coefficient is the effect of +1 std of the feature
    df[FEATURES] = (df[FEATURES] - df[FEATURES].mean()) / df[FEATURES].std()
    return df


def fit(data, q, formula=FORMULA):
    """Return the coefficients of OLS (q=None) or of the quantile regression at q."""
    if q is None:
        return smf.ols(formula, data).fit().params
    return smf.quantreg(formula, data).fit(q=q).params


def block_bootstrap(df, q, seed=0, formula=FORMULA):
    """95% confidence interval of each coefficient (moving block bootstrap)."""
    rng = np.random.default_rng(seed)
    n = len(df)
    coefs = []
    for _ in range(N_BOOT):
        starts = rng.integers(0, n - BLOCK + 1, size=n // BLOCK + 1)
        rows = (starts[:, None] + np.arange(BLOCK)).ravel()[:n]
        coefs.append(fit(df.iloc[rows], q, formula=formula))
    return pd.DataFrame(coefs).quantile([0.025, 0.975])


def run():
    """Fit every model, save the coefficient table (CSV) and the figure (PNG)."""
    df = load_data()
    tables = []
    for q in QUANTILES + [None]:
        ci = block_bootstrap(df, q)
        tables.append(pd.DataFrame({
            "model": "OLS" if q is None else f"q{q:.2f}",
            "coef": fit(df, q),
            "ci_low": ci.loc[0.025],
            "ci_high": ci.loc[0.975],
        }))
    table = pd.concat(tables).rename_axis("variable").reset_index()

    RESULTS.mkdir(exist_ok=True)
    table.to_csv(RESULTS / "quantile_coefs.csv", index=False)

    # One panel per feature: coefficient and 95% interval for each model
    fig, axes = plt.subplots(1, len(FEATURES), figsize=(14, 3.5), sharey=True)
    for ax, var in zip(axes, FEATURES):
        d = table[table["variable"] == var]
        ax.errorbar(d["model"], d["coef"], yerr=[d["coef"] - d["ci_low"],
                    d["ci_high"] - d["coef"]], fmt="o", capsize=4)
        ax.axhline(0, color="grey", lw=0.8)
        ax.set_title(var)
    axes[0].set_ylabel("Effect of +1 std on 4-week carry return")
    fig.tight_layout()
    fig.savefig(RESULTS / "quantile_coefs.png", dpi=150)
    return table


if __name__ == "__main__":
    print(run().round(4).to_string(index=False))
