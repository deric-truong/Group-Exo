"""Checks on the walk-forward validation (needs data/modelling_table.parquet)."""

import numpy as np
import pandas as pd
import pytest

from src import config
from src import walk_forward as wf

if not (config.DIRECTORY / "modelling_table.parquet").exists():
    pytest.skip("modelling table not built", allow_module_level=True)


def test_pinball_known_values():
    """Above the forecast: tau * gap; below it: (1 - tau) * gap."""
    assert np.isclose(wf.pinball(np.array([0.02]), np.array([0.0])), 0.05 * 0.02)
    assert np.isclose(wf.pinball(np.array([-0.02]), np.array([0.0])), 0.95 * 0.02)


def test_forecast_ignores_future_targets():
    """Changing targets after t - 4 weeks must not change the forecast at t."""
    df = wf.load_data()
    t = df.index[700]
    before = wf.forecast_at(df, t)
    future = df.copy()
    future.loc[future.index > t - wf.HORIZON, wf.TARGET] = 99.0
    assert wf.forecast_at(future, t) == before


def test_first_forecast_after_training_window():
    """Forecasts start only after the first 10-year training window."""
    df = wf.load_data()
    fc = wf.walk_forward(df.loc[: df.index[0] + pd.DateOffset(years=11)])
    assert fc.index[0] >= df.index[0] + pd.DateOffset(years=wf.TRAIN_YEARS)

