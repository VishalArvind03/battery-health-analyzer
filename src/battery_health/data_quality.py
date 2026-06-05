"""Data-quality checks for battery cycle data.

Before trusting any SOH or degradation result, it helps to ask a simple
question: "is the input data sensible?" Real test data can contain typos,
sensor glitches, missing rows, or duplicated cycles. This module scans the
data and reports anything that looks wrong, so the engineer can review it.

These are *sanity* checks, not safety limits. A finding here means "look at this
data", not "the battery is unsafe".
"""

import pandas as pd

# --- Sensible physical bounds for a lithium-ion cell test ---------------------
# A cell on a lab cycler should never read these extremes; values outside this
# range almost always mean a broken sensor or a data error.
MIN_REALISTIC_TEMPERATURE_C = -40.0
MAX_REALISTIC_TEMPERATURE_C = 80.0

# Discharge capacity normally changes only a little from one cycle to the next.
# A jump larger than this fraction (20%) between neighbouring cycles is suspicious.
CAPACITY_JUMP_FRACTION = 0.20

# A trend needs a minimum number of points to mean anything.
MIN_CYCLES_FOR_ANALYSIS = 5

# Columns that must contain real numbers for the analysis to work.
REQUIRED_NUMERIC_COLUMNS = [
    "cycle",
    "discharge_capacity_ah",
    "avg_voltage_v",
    "max_temperature_c",
]


def check_data_quality(
    data: pd.DataFrame,
    *,
    min_temperature_c: float = MIN_REALISTIC_TEMPERATURE_C,
    max_temperature_c: float = MAX_REALISTIC_TEMPERATURE_C,
    capacity_jump_fraction: float = CAPACITY_JUMP_FRACTION,
    min_cycles: int = MIN_CYCLES_FOR_ANALYSIS,
) -> list[str]:
    """Scan cycle data and return a list of human-readable data-quality findings.

    The data should be passed *in its original order* (before sorting), so that
    out-of-order cycles can be detected. If everything looks fine, the list
    contains a single "no issues" message.
    """
    issues: list[str] = []

    issues.extend(_check_insufficient_data(data, min_cycles))
    issues.extend(_check_missing_values(data))
    issues.extend(_check_duplicate_cycles(data))
    issues.extend(_check_invalid_capacity(data))
    issues.extend(_check_unrealistic_temperatures(data, min_temperature_c, max_temperature_c))
    issues.extend(_check_cycle_order(data))
    issues.extend(_check_abnormal_capacity_jumps(data, capacity_jump_fraction))

    if not issues:
        issues.append("No data-quality issues detected.")
    return issues


def _check_insufficient_data(data: pd.DataFrame, min_cycles: int) -> list[str]:
    if len(data) < min_cycles:
        return [
            f"Insufficient data: only {len(data)} cycle(s) found, "
            f"but at least {min_cycles} are recommended for a meaningful trend."
        ]
    return []


def _check_missing_values(data: pd.DataFrame) -> list[str]:
    findings = []
    for column in REQUIRED_NUMERIC_COLUMNS:
        if column not in data.columns:
            continue
        numeric = pd.to_numeric(data[column], errors="coerce")
        missing = int(numeric.isna().sum())
        if missing > 0:
            findings.append(
                f"Missing values: column '{column}' has {missing} missing or "
                "non-numeric value(s)."
            )
    return findings


def _check_duplicate_cycles(data: pd.DataFrame) -> list[str]:
    if "cycle" not in data.columns:
        return []
    duplicate_count = int(data["cycle"].duplicated().sum())
    if duplicate_count > 0:
        return [f"Duplicate cycles: {duplicate_count} repeated cycle number(s) found."]
    return []


def _check_invalid_capacity(data: pd.DataFrame) -> list[str]:
    if "discharge_capacity_ah" not in data.columns:
        return []
    capacity = pd.to_numeric(data["discharge_capacity_ah"], errors="coerce")
    invalid_count = int((capacity <= 0).sum())
    if invalid_count > 0:
        return [
            f"Invalid capacity: {invalid_count} cycle(s) have a discharge "
            "capacity of zero or below, which is physically impossible."
        ]
    return []


def _check_unrealistic_temperatures(
    data: pd.DataFrame, min_temperature_c: float, max_temperature_c: float
) -> list[str]:
    if "max_temperature_c" not in data.columns:
        return []
    temperature = pd.to_numeric(data["max_temperature_c"], errors="coerce")
    out_of_range = ((temperature < min_temperature_c) | (temperature > max_temperature_c)).sum()
    if int(out_of_range) > 0:
        return [
            f"Unrealistic temperatures: {int(out_of_range)} cycle(s) are outside the "
            f"expected {min_temperature_c:.0f} C to {max_temperature_c:.0f} C range."
        ]
    return []


def _check_cycle_order(data: pd.DataFrame) -> list[str]:
    if "cycle" not in data.columns:
        return []
    cycles = pd.to_numeric(data["cycle"], errors="coerce")
    if not cycles.is_monotonic_increasing:
        return [
            "Incorrectly ordered cycles: cycle numbers are not in increasing order "
            "in the source file (they are sorted automatically before analysis)."
        ]
    return []


def _check_abnormal_capacity_jumps(
    data: pd.DataFrame, capacity_jump_fraction: float
) -> list[str]:
    if "discharge_capacity_ah" not in data.columns or "cycle" not in data.columns:
        return []
    # Sort by cycle first so a wrong row order does not create fake "jumps".
    ordered = data.sort_values("cycle")
    capacity = pd.to_numeric(ordered["discharge_capacity_ah"], errors="coerce")
    # fill_method=None keeps missing values as gaps instead of carrying the last
    # value forward, which avoids hiding a real data gap as a fake "no change".
    relative_change = capacity.pct_change(fill_method=None).abs()
    jump_count = int((relative_change > capacity_jump_fraction).sum())
    if jump_count > 0:
        return [
            f"Abnormal jumps: {jump_count} cycle-to-cycle change(s) in discharge "
            f"capacity exceed {capacity_jump_fraction * 100:.0f}%, which may indicate "
            "a measurement glitch."
        ]
    return []
