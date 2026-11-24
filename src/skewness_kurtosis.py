"""Assess skewness and excess kurtosis of the project's carry returns."""

import numpy as np
import pandas as pd
from scipy import stats

from src import config

MODELLING_TABLE = config.DIRECTORY / "modelling_table.parquet"
BLOCK = 12
N_BOOT = 1_000
SEED = 0


def block_bootstrap_moments(values, block=BLOCK, n_boot=N_BOOT, seed=SEED):
    """Return percentile confidence intervals for skew and excess kurtosis."""
    values = np.asarray(values, dtype=float)
    n = len(values)
    if n < block:
        raise ValueError(f"Need at least {block} observations for the block bootstrap")

    rng = np.random.default_rng(seed)
    moments = np.empty((n_boot, 2))
    for i in range(n_boot):
        starts = rng.integers(0, n - block + 1, size=n // block + 1)
        rows = (starts[:, None] + np.arange(block)).ravel()[:n]
        sample = pd.Series(values[rows])
        moments[i] = sample.skew(), sample.kurt()

    return np.percentile(moments, [2.5, 97.5], axis=0)


def run():
    """Load carry returns and report skewness and kurtosis assessments."""
    if not MODELLING_TABLE.exists():
        raise FileNotFoundError(
            f"{MODELLING_TABLE} not found; build it with "
            "`python -m src.modelling_table` first."
        )

    table = pd.read_parquet(MODELLING_TABLE)
    required = ["fwd_carry_1w", "fwd_carry_4w"]
    missing = [column for column in required if column not in table.columns]
    if missing:
        raise ValueError(f"Modelling table is missing columns: {missing}")

    r1 = table["fwd_carry_1w"].dropna()
    r4 = table["fwd_carry_4w"].dropna()

    print(f"1-week carry (n={len(r1)}):")
    print(f"  skewness: {r1.skew():.4f}; skewtest: {stats.skewtest(r1.to_numpy())}")
    print(f"  excess kurtosis: {r1.kurt():.4f}")
    print(f"  kurtosis test: {stats.kurtosistest(r1.to_numpy())}")
    print(f"  Jarque-Bera test: {stats.jarque_bera(r1.to_numpy())}")

    ci_4w = block_bootstrap_moments(r4.to_numpy())
    print(f"4-week carry (n={len(r4)}; {BLOCK}-week block bootstrap):")
    print(
        f"  skewness: {r4.skew():.4f}; 95% CI="
        f"[{ci_4w[0, 0]:.4f}, {ci_4w[1, 0]:.4f}]"
    )
    print(
        f"  excess kurtosis: {r4.kurt():.4f}; 95% CI="
        f"[{ci_4w[0, 1]:.4f}, {ci_4w[1, 1]:.4f}]"
    )


if __name__ == "__main__":
    run()
