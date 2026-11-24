"""Assess skewness of the project's one- and four-week carry returns."""

import numpy as np
import pandas as pd
from scipy import stats

from src import config

MODELLING_TABLE = config.DIRECTORY / "modelling_table.parquet"
BLOCK = 12
N_BOOT = 1_000
SEED = 0


def block_bootstrap_skewness(values, block=BLOCK, n_boot=N_BOOT, seed=SEED):
    """Return a percentile confidence interval for skewness using moving blocks."""
    values = np.asarray(values, dtype=float)
    n = len(values)
    if n < block:
        raise ValueError(f"Need at least {block} observations for the block bootstrap")

    rng = np.random.default_rng(seed)
    skews = np.empty(n_boot)
    for i in range(n_boot):
        starts = rng.integers(0, n - block + 1, size=n // block + 1)
        rows = (starts[:, None] + np.arange(block)).ravel()[:n]
        skews[i] = pd.Series(values[rows]).skew()

    return np.percentile(skews, [2.5, 97.5])


def run():
    """Load forward-carry returns and print skewness estimates and inference."""
    if not MODELLING_TABLE.exists():
        raise FileNotFoundError(
            f"{MODELLING_TABLE} not found; build it with "
            "`python -m src.modelling_table` first."
        )

    table = pd.read_parquet(MODELLING_TABLE)
    returns = table[["fwd_carry_1w", "fwd_carry_4w"]]
    r1 = returns["fwd_carry_1w"].dropna()
    r4 = returns["fwd_carry_4w"].dropna()

    skew_1w = r1.skew()
    test_1w = stats.skewtest(r1.to_numpy())
    skew_4w = r4.skew()
    ci_4w = block_bootstrap_skewness(r4.to_numpy())

    print(
        f"1-week carry: n={len(r1)}, skewness={skew_1w:.4f}, "
        f"skewtest statistic={test_1w.statistic:.4f}, p-value={test_1w.pvalue:.4g}"
    )
    print(
        f"4-week carry: n={len(r4)}, skewness={skew_4w:.4f}, "
        f"12-week block-bootstrap 95% CI=[{ci_4w[0]:.4f}, {ci_4w[1]:.4f}]"
    )


if __name__ == "__main__":
    run()
