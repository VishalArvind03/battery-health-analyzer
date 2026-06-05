"""Shared test setup and reusable fixtures.

`conftest.py` is a special file that pytest loads automatically before running
any test. We use it for two jobs:

1. Make the project's source code importable (add the `src` folder to the path).
2. Provide small, reusable sample data ("fixtures") so each test stays short.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

# The project layout keeps the code under `src/battery_health`.
# Adding `src` to sys.path lets the tests do `import battery_health` directly,
# exactly like main.py does.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture
def sample_cycles() -> pd.DataFrame:
    """A tiny, predictable battery dataset used by many tests.

    The numbers are chosen so the expected results are easy to verify by hand:
    discharge capacity falls from 2.0 Ah to 1.5 Ah, so SOH falls from
    100% to 75% and capacity fade rises from 0% to 25%.
    """
    return pd.DataFrame(
        {
            "cycle": [1, 2, 3, 4, 5, 6],
            "discharge_capacity_ah": [2.0, 1.9, 1.8, 1.7, 1.6, 1.5],
            "charge_capacity_ah": [2.04, 1.95, 1.85, 1.75, 1.65, 1.55],
            "avg_voltage_v": [3.70, 3.69, 3.68, 3.67, 3.66, 3.65],
            "max_temperature_c": [30.0, 31.0, 32.0, 33.0, 34.0, 35.0],
            "internal_resistance_mohm": [40.0, 41.0, 42.0, 43.0, 44.0, 45.0],
        }
    )


@pytest.fixture
def nasa_like_cycles() -> pd.DataFrame:
    """Like `sample_cycles` but with no charge-capacity data.

    This mimics the real NASA B0005 dataset, where charge capacity is missing,
    so coulombic efficiency cannot be calculated.
    """
    return pd.DataFrame(
        {
            "cycle": [1, 2, 3, 4, 5, 6],
            "discharge_capacity_ah": [1.85, 1.80, 1.75, 1.70, 1.65, 1.60],
            "charge_capacity_ah": [pd.NA] * 6,
            "avg_voltage_v": [3.52, 3.51, 3.50, 3.49, 3.48, 3.47],
            "max_temperature_c": [38.0, 39.0, 40.0, 40.5, 41.0, 41.5],
            "internal_resistance_mohm": [44.0, 45.0, 47.0, 49.0, 51.0, 50.0],
        }
    )
