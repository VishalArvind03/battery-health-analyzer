"""Tests for the data-quality checks in data_quality.py."""

import pandas as pd

from battery_health.data_quality import check_data_quality


def _good_data() -> pd.DataFrame:
    """A clean 6-cycle dataset that should pass every check."""
    return pd.DataFrame(
        {
            "cycle": [1, 2, 3, 4, 5, 6],
            "discharge_capacity_ah": [2.0, 1.98, 1.96, 1.94, 1.92, 1.90],
            "avg_voltage_v": [3.70, 3.69, 3.68, 3.67, 3.66, 3.65],
            "max_temperature_c": [30.0, 31.0, 32.0, 33.0, 34.0, 35.0],
        }
    )


def _has(findings, keyword: str) -> bool:
    return any(keyword.lower() in f.lower() for f in findings)


def test_clean_data_reports_no_issues():
    findings = check_data_quality(_good_data())
    assert findings == ["No data-quality issues detected."]


def test_detects_insufficient_data():
    tiny = _good_data().head(2)
    findings = check_data_quality(tiny)
    assert _has(findings, "Insufficient data")


def test_detects_missing_values():
    data = _good_data()
    data.loc[2, "discharge_capacity_ah"] = None
    findings = check_data_quality(data)
    assert _has(findings, "Missing values")


def test_detects_duplicate_cycles():
    data = _good_data()
    data.loc[3, "cycle"] = 3  # cycle 3 now appears twice
    findings = check_data_quality(data)
    assert _has(findings, "Duplicate cycles")


def test_detects_invalid_capacity():
    data = _good_data()
    data.loc[4, "discharge_capacity_ah"] = 0.0
    findings = check_data_quality(data)
    assert _has(findings, "Invalid capacity")


def test_detects_unrealistic_temperature():
    data = _good_data()
    data.loc[1, "max_temperature_c"] = 500.0  # broken sensor
    findings = check_data_quality(data)
    assert _has(findings, "Unrealistic temperatures")


def test_detects_out_of_order_cycles():
    data = _good_data()
    # swap the order of the first two rows without sorting
    reordered = data.iloc[[1, 0, 2, 3, 4, 5]].reset_index(drop=True)
    findings = check_data_quality(reordered)
    assert _has(findings, "Incorrectly ordered")


def test_detects_abnormal_capacity_jump():
    data = _good_data()
    data.loc[3, "discharge_capacity_ah"] = 5.0  # huge unrealistic jump
    findings = check_data_quality(data)
    assert _has(findings, "Abnormal jumps")


def test_thresholds_can_be_customised():
    """A stricter temperature ceiling should flag otherwise-normal data."""
    findings = check_data_quality(_good_data(), max_temperature_c=32.0)
    assert _has(findings, "Unrealistic temperatures")
