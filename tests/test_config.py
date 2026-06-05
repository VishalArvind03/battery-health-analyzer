"""Tests for loading the engineering warning limits from config/limits.json."""

import json

import pytest

from battery_health.config import DEFAULT_LIMITS, load_limits


def _write_config(folder, contents: dict) -> str:
    """Helper: write a small JSON config into a temporary folder and return its path."""
    path = folder / "limits.json"
    path.write_text(json.dumps(contents), encoding="utf-8")
    return str(path)


def test_loads_all_values_from_file(tmp_path):
    """Values written in the file must be read back exactly."""
    config_path = _write_config(
        tmp_path,
        {
            "soh_limit_percent": 70.0,
            "temperature_limit_c": 50.0,
            "resistance_rise_limit_percent": 25.0,
            "coulombic_efficiency_limit_percent": 95.0,
        },
    )
    limits = load_limits(config_path)
    assert limits["soh_limit_percent"] == 70.0
    assert limits["temperature_limit_c"] == 50.0


def test_missing_keys_fall_back_to_defaults(tmp_path):
    """A partial config should still work, using built-in defaults for the rest."""
    config_path = _write_config(tmp_path, {"soh_limit_percent": 60.0})
    limits = load_limits(config_path)
    assert limits["soh_limit_percent"] == 60.0  # from the file
    # these were not in the file, so the defaults must be used
    assert limits["temperature_limit_c"] == DEFAULT_LIMITS["temperature_limit_c"]


def test_missing_file_raises(tmp_path):
    """A config path that does not exist must raise a clear error."""
    with pytest.raises(FileNotFoundError):
        load_limits(tmp_path / "does_not_exist.json")


def test_negative_limit_is_rejected(tmp_path):
    """Warning limits must be positive numbers; a negative value is invalid."""
    config_path = _write_config(tmp_path, {"soh_limit_percent": -5.0})
    with pytest.raises(ValueError):
        load_limits(config_path)


def test_non_numeric_limit_is_rejected(tmp_path):
    """A limit written as text instead of a number must be rejected."""
    config_path = _write_config(tmp_path, {"soh_limit_percent": "eighty"})
    with pytest.raises(TypeError):
        load_limits(config_path)
