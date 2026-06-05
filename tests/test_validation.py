"""Tests for the engineering warning logic in validation.py."""

from battery_health.metrics import add_battery_metrics
from battery_health.validation import generate_health_warnings

# A standard set of limits used across the warning tests.
LIMITS = {
    "soh_limit_percent": 80.0,
    "temperature_limit_c": 45.0,
    "resistance_rise_limit_percent": 20.0,
    "coulombic_efficiency_limit_percent": 98.0,
}


def _has(warnings, keyword: str) -> bool:
    """True if any warning message mentions the given keyword."""
    return any(keyword.lower() in w.lower() for w in warnings)


def test_soh_warning_triggers_when_below_limit(sample_cycles):
    """Last cycle is 75% SOH, which is below the 80% limit -> SOH warning."""
    analyzed = add_battery_metrics(sample_cycles)
    warnings = generate_health_warnings(analyzed, LIMITS)
    assert _has(warnings, "SOH")


def test_no_soh_warning_when_healthy(sample_cycles):
    """If the SOH limit is relaxed below the current SOH, no SOH warning appears."""
    analyzed = add_battery_metrics(sample_cycles)
    relaxed = {**LIMITS, "soh_limit_percent": 50.0}
    warnings = generate_health_warnings(analyzed, relaxed)
    assert not _has(warnings, "SOH")


def test_temperature_warning_triggers(sample_cycles):
    """Max temperature is 35 C; lowering the limit to 30 C must trigger a warning."""
    analyzed = add_battery_metrics(sample_cycles)
    strict = {**LIMITS, "temperature_limit_c": 30.0}
    warnings = generate_health_warnings(analyzed, strict)
    assert _has(warnings, "Temperature")


def test_resistance_warning_triggers(sample_cycles):
    """Resistance rises 40 -> 45 mohm (12.5%); a 5% limit must trigger a warning."""
    analyzed = add_battery_metrics(sample_cycles)
    strict = {**LIMITS, "resistance_rise_limit_percent": 5.0}
    warnings = generate_health_warnings(analyzed, strict)
    assert _has(warnings, "Resistance")


def test_coulombic_efficiency_warning_triggers(sample_cycles):
    """Efficiency near 98% should trip a 99.5% limit."""
    analyzed = add_battery_metrics(sample_cycles)
    strict = {**LIMITS, "coulombic_efficiency_limit_percent": 99.5}
    warnings = generate_health_warnings(analyzed, strict)
    assert _has(warnings, "Efficiency")


def test_clean_data_reports_no_warnings(sample_cycles):
    """With very relaxed limits, a 'no warnings' message must be returned."""
    analyzed = add_battery_metrics(sample_cycles)
    relaxed = {
        "soh_limit_percent": 10.0,
        "temperature_limit_c": 100.0,
        "resistance_rise_limit_percent": 100.0,
        "coulombic_efficiency_limit_percent": 1.0,
    }
    warnings = generate_health_warnings(analyzed, relaxed)
    assert _has(warnings, "No warnings")
