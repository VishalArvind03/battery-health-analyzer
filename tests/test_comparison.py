"""Tests for the multi-cell comparison module."""

import pandas as pd

from battery_health.comparison import (
    analyze_cell,
    compare_cells,
    _cycles_to_threshold,
    _resistance_rise_percent,
)
from battery_health.metrics import add_battery_metrics


def _write_cell_csv(folder, name: str, capacities, resistances=None) -> str:
    """Write a small valid cell CSV and return its path."""
    n = len(capacities)
    frame = pd.DataFrame(
        {
            "battery_id": [name] * n,
            "cycle": list(range(1, n + 1)),
            "discharge_capacity_ah": capacities,
            "avg_voltage_v": [3.6] * n,
            "max_temperature_c": [30.0 + i for i in range(n)],
            "internal_resistance_mohm": resistances if resistances is not None else [pd.NA] * n,
        }
    )
    path = folder / f"nasa_{name}_cycles.csv"
    frame.to_csv(path, index=False)
    return str(path)


def test_analyze_cell_returns_expected_keys(tmp_path):
    path = _write_cell_csv(tmp_path, "B0005", [2.0, 1.9, 1.8, 1.7, 1.6, 1.5])
    result = analyze_cell(path)
    for key in (
        "battery_id",
        "cycles_analyzed",
        "final_soh_percent",
        "capacity_fade_percent",
        "degradation_slope_per_cycle",
        "max_temperature_c",
        "cycles_to_80_percent_soh",
    ):
        assert key in result
    assert result["battery_id"] == "B0005"
    assert result["cycles_analyzed"] == 6
    assert result["final_soh_percent"] == 75.0


def test_cycles_to_threshold_found():
    """SOH falls 100% -> 75%, crossing 80% at cycle 5 (capacity 1.6 of 2.0)."""
    data = add_battery_metrics(
        pd.DataFrame(
            {
                "cycle": [1, 2, 3, 4, 5, 6],
                "discharge_capacity_ah": [2.0, 1.9, 1.8, 1.7, 1.6, 1.5],
                "charge_capacity_ah": [pd.NA] * 6,
                "avg_voltage_v": [3.6] * 6,
                "max_temperature_c": [30.0] * 6,
                "internal_resistance_mohm": [pd.NA] * 6,
            }
        )
    )
    assert _cycles_to_threshold(data, 80.0) == 5


def test_cycles_to_threshold_not_reached():
    """A healthy cell that stays above 80% should report 'not reached'."""
    data = add_battery_metrics(
        pd.DataFrame(
            {
                "cycle": [1, 2, 3, 4],
                "discharge_capacity_ah": [2.0, 1.99, 1.98, 1.97],
                "charge_capacity_ah": [pd.NA] * 4,
                "avg_voltage_v": [3.6] * 4,
                "max_temperature_c": [30.0] * 4,
                "internal_resistance_mohm": [pd.NA] * 4,
            }
        )
    )
    assert _cycles_to_threshold(data, 80.0) == "not reached"


def test_resistance_rise_calculated():
    data = pd.DataFrame({"internal_resistance_mohm": [40.0, 42.0, 44.0, 48.0]})
    # 40 -> 48 is a 20% rise
    assert _resistance_rise_percent(data) == 20.0


def test_resistance_rise_none_when_missing():
    data = pd.DataFrame({"internal_resistance_mohm": [pd.NA, pd.NA]})
    assert _resistance_rise_percent(data) is None


def test_compare_cells_one_row_per_cell(tmp_path):
    path_a = _write_cell_csv(tmp_path, "B0005", [2.0, 1.8, 1.6, 1.4, 1.2, 1.0])
    path_b = _write_cell_csv(tmp_path, "B0006", [2.1, 2.0, 1.9, 1.8, 1.7, 1.6])
    comparison = compare_cells([path_a, path_b])
    assert len(comparison) == 2
    assert set(comparison["battery_id"]) == {"B0005", "B0006"}
