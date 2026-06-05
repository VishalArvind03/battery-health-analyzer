"""Tests for battery health metrics: SOH, capacity fade, coulombic efficiency,
smoothing, and the degradation slope."""

import numpy as np
import pandas as pd
import pytest

from battery_health.metrics import (
    add_battery_metrics,
    estimate_soh_degradation_slope,
    summarize_battery_metrics,
)


def test_soh_first_cycle_is_100(sample_cycles):
    """State of health is measured against the first cycle, so it must start at 100%."""
    result = add_battery_metrics(sample_cycles)
    assert result["soh_percent"].iloc[0] == pytest.approx(100.0)


def test_soh_matches_capacity_ratio(sample_cycles):
    """SOH = current discharge capacity / baseline capacity * 100."""
    result = add_battery_metrics(sample_cycles)
    # baseline is 2.0 Ah, last cycle is 1.5 Ah -> 75%
    assert result["soh_percent"].iloc[-1] == pytest.approx(75.0)


def test_capacity_fade_is_100_minus_soh(sample_cycles):
    """Capacity fade and SOH must always add up to 100%."""
    result = add_battery_metrics(sample_cycles)
    total = result["soh_percent"] + result["capacity_fade_percent"]
    assert total.round(6).eq(100.0).all()


def test_nominal_capacity_override(sample_cycles):
    """If a nominal capacity is given, SOH is measured against it instead of cycle 1."""
    result = add_battery_metrics(sample_cycles, nominal_capacity_ah=4.0)
    # first discharge capacity is 2.0 Ah measured against 4.0 Ah nominal -> 50%
    assert result["soh_percent"].iloc[0] == pytest.approx(50.0)


def test_zero_baseline_raises(sample_cycles):
    """A baseline capacity of zero is physically impossible and must be rejected."""
    with pytest.raises(ValueError):
        add_battery_metrics(sample_cycles, nominal_capacity_ah=0.0)


def test_coulombic_efficiency_calculated_when_charge_available(sample_cycles):
    """When charge capacity exists, efficiency = discharge / charge * 100."""
    result = add_battery_metrics(sample_cycles)
    expected = 2.0 / 2.04 * 100
    assert result["coulombic_efficiency_percent"].iloc[0] == pytest.approx(expected)


def test_coulombic_efficiency_missing_for_nasa_like_data(nasa_like_cycles):
    """NASA B0005 has no charge capacity, so efficiency must stay empty (not faked)."""
    result = add_battery_metrics(nasa_like_cycles)
    assert result["coulombic_efficiency_percent"].isna().all()


def test_smoothed_columns_are_added(sample_cycles):
    """Smoothing must produce the three rolling-average columns."""
    result = add_battery_metrics(sample_cycles)
    for column in (
        "soh_percent_smoothed",
        "capacity_fade_percent_smoothed",
        "internal_resistance_mohm_smoothed",
    ):
        assert column in result.columns
        assert result[column].notna().any()


def test_smoothing_reduces_a_single_spike(sample_cycles):
    """A rolling average should pull a one-cycle spike back toward its neighbours."""
    spiky = sample_cycles.copy()
    spiky.loc[3, "discharge_capacity_ah"] = 5.0  # an obviously wrong spike
    result = add_battery_metrics(spiky)
    raw_spike = result["soh_percent"].iloc[3]
    smoothed_spike = result["soh_percent_smoothed"].iloc[3]
    assert smoothed_spike < raw_spike


def test_degradation_slope_is_negative_for_aging_cell(sample_cycles):
    """A cell that loses capacity should have a negative SOH-per-cycle slope."""
    result = add_battery_metrics(sample_cycles)
    slope = estimate_soh_degradation_slope(result)
    assert slope is not None
    assert slope < 0


def test_degradation_slope_none_with_too_few_points():
    """With fewer than 3 cycles there is not enough data to fit a trend line."""
    tiny = pd.DataFrame({"cycle": [1, 2], "soh_percent_smoothed": [100.0, 99.0]})
    assert estimate_soh_degradation_slope(tiny) is None


def test_summary_contains_expected_keys(sample_cycles):
    """The summary dictionary feeds the report, so its key fields must exist."""
    result = add_battery_metrics(sample_cycles)
    summary = summarize_battery_metrics(result)
    for key in (
        "latest_soh_percent",
        "total_capacity_fade_percent",
        "max_temperature_c",
        "initial_capacity_ah",
        "latest_capacity_ah",
    ):
        assert key in summary
    assert summary["latest_soh_percent"] == pytest.approx(75.0)
    assert summary["max_temperature_c"] == pytest.approx(35.0)


def test_missing_capacity_value_becomes_nan(sample_cycles):
    """A non-numeric / missing capacity must turn into NaN, not crash the pipeline."""
    dirty = sample_cycles.copy()
    dirty["discharge_capacity_ah"] = dirty["discharge_capacity_ah"].astype(object)
    dirty.loc[2, "discharge_capacity_ah"] = "not_a_number"
    result = add_battery_metrics(dirty)
    assert np.isnan(result["soh_percent"].iloc[2])
