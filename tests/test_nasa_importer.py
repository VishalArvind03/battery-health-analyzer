"""Tests for the NASA .mat to cycle-CSV converter.

Two kinds of tests live here:
1. Fast unit tests for the impedance-matching helper (always run).
2. A slower integration test that converts the real B0005.mat file. That test
   is skipped automatically if the .mat file is not present (for example on a
   fresh GitHub clone, where the large .mat files are not committed).
"""

from pathlib import Path

import pytest

from battery_health.nasa_importer import (
    _nearest_impedance_value,
    convert_nasa_mat_to_cycle_csv,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
B0005_MAT = PROJECT_ROOT / "data" / "raw" / "nasa" / "B0005.mat"

EXPECTED_COLUMNS = {
    "battery_id",
    "cycle",
    "discharge_capacity_ah",
    "avg_voltage_v",
    "max_temperature_c",
    "internal_resistance_mohm",
}


def test_nearest_impedance_picks_closest_cycle():
    """The helper should return the resistance whose source cycle is closest."""
    points = [(10, 44.0), (50, 50.0), (90, 60.0)]
    # source cycle 12 is closest to point at index 10 -> 44.0
    assert _nearest_impedance_value(12, points) == 44.0
    # source cycle 85 is closest to point at index 90 -> 60.0
    assert _nearest_impedance_value(85, points) == 60.0


def test_nearest_impedance_returns_none_when_empty():
    """With no impedance measurements there is nothing to match."""
    assert _nearest_impedance_value(5, []) is None


@pytest.mark.nasa
@pytest.mark.skipif(not B0005_MAT.exists(), reason="B0005.mat not available")
def test_convert_b0005_produces_expected_shape(tmp_path):
    """Converting the real B0005 file should yield ~168 discharge cycles."""
    output = tmp_path / "b0005.csv"
    frame = convert_nasa_mat_to_cycle_csv(B0005_MAT, output, battery_id="B0005")

    assert output.exists()
    assert EXPECTED_COLUMNS.issubset(frame.columns)
    # NASA B0005 has 168 discharge cycles.
    assert len(frame) == 168
    # Cycles must be numbered 1, 2, 3, ... in order.
    assert frame["cycle"].tolist() == list(range(1, len(frame) + 1))
    # First measured discharge capacity is about 1.856 Ah.
    assert frame["discharge_capacity_ah"].iloc[0] == pytest.approx(1.856, abs=0.01)
