"""Tests for loading cycle CSV data and checking required columns."""

import pandas as pd
import pytest

from battery_health.data_loader import load_cycle_data


def _write_csv(folder, frame: pd.DataFrame) -> str:
    path = folder / "cycles.csv"
    frame.to_csv(path, index=False)
    return str(path)


def test_loads_a_valid_csv(tmp_path):
    """A CSV with all required columns should load into a DataFrame."""
    frame = pd.DataFrame(
        {
            "cycle": [1, 2],
            "discharge_capacity_ah": [2.0, 1.9],
            "avg_voltage_v": [3.7, 3.7],
            "max_temperature_c": [30.0, 31.0],
        }
    )
    data = load_cycle_data(_write_csv(tmp_path, frame))
    assert len(data) == 2


def test_missing_required_column_raises(tmp_path):
    """Dropping a required column (max_temperature_c) must raise a clear error."""
    frame = pd.DataFrame(
        {
            "cycle": [1, 2],
            "discharge_capacity_ah": [2.0, 1.9],
            "avg_voltage_v": [3.7, 3.7],
        }
    )
    with pytest.raises(ValueError):
        load_cycle_data(_write_csv(tmp_path, frame))


def test_optional_columns_filled_when_absent(tmp_path):
    """Optional columns should be added (as empty) so the rest of the code is safe."""
    frame = pd.DataFrame(
        {
            "cycle": [1, 2],
            "discharge_capacity_ah": [2.0, 1.9],
            "avg_voltage_v": [3.7, 3.7],
            "max_temperature_c": [30.0, 31.0],
        }
    )
    data = load_cycle_data(_write_csv(tmp_path, frame))
    assert "charge_capacity_ah" in data.columns
    assert "internal_resistance_mohm" in data.columns


def test_rows_are_sorted_by_cycle(tmp_path):
    """Out-of-order cycles must be sorted so trend calculations are correct."""
    frame = pd.DataFrame(
        {
            "cycle": [3, 1, 2],
            "discharge_capacity_ah": [1.8, 2.0, 1.9],
            "avg_voltage_v": [3.6, 3.7, 3.7],
            "max_temperature_c": [32.0, 30.0, 31.0],
        }
    )
    data = load_cycle_data(_write_csv(tmp_path, frame))
    assert data["cycle"].tolist() == [1, 2, 3]


def test_missing_file_raises(tmp_path):
    """A path that does not point to a real file must raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_cycle_data(tmp_path / "nope.csv")
