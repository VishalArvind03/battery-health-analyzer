import numpy as np
import pandas as pd

SMOOTHING_WINDOW = 5


def add_battery_metrics(data: pd.DataFrame, nominal_capacity_ah: float | None = None) -> pd.DataFrame:
    """Add SOH, capacity fade, coulombic efficiency, and smoothed trend columns."""
    result = data.copy()
    result["discharge_capacity_ah"] = pd.to_numeric(
        result["discharge_capacity_ah"], errors="coerce"
    )
    result["charge_capacity_ah"] = pd.to_numeric(
        result["charge_capacity_ah"], errors="coerce"
    )

    if nominal_capacity_ah is None:
        baseline_capacity = float(result.loc[0, "discharge_capacity_ah"])
    else:
        baseline_capacity = float(nominal_capacity_ah)

    if baseline_capacity <= 0:
        raise ValueError("Baseline capacity must be greater than zero.")

    result["soh_percent"] = result["discharge_capacity_ah"] / baseline_capacity * 100
    result["capacity_fade_percent"] = 100 - result["soh_percent"]
    result["coulombic_efficiency_percent"] = pd.NA

    valid_charge_capacity = result["charge_capacity_ah"] > 0
    result.loc[valid_charge_capacity, "coulombic_efficiency_percent"] = (
        result.loc[valid_charge_capacity, "discharge_capacity_ah"]
        / result.loc[valid_charge_capacity, "charge_capacity_ah"]
        * 100
    )

    result = _add_smoothed_columns(result)
    return result


def _add_smoothed_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Add rolling-average smoothed columns for SOH, capacity fade, and resistance."""
    w = SMOOTHING_WINDOW
    data["soh_percent_smoothed"] = (
        data["soh_percent"].rolling(window=w, min_periods=1, center=True).mean()
    )
    data["capacity_fade_percent_smoothed"] = (
        data["capacity_fade_percent"].rolling(window=w, min_periods=1, center=True).mean()
    )
    resistance = pd.to_numeric(data["internal_resistance_mohm"], errors="coerce")
    data["internal_resistance_mohm_smoothed"] = (
        resistance.rolling(window=w, min_periods=1, center=True).mean()
    )
    return data


def estimate_soh_degradation_slope(data: pd.DataFrame) -> float | None:
    """Estimate SOH degradation rate as % SOH lost per cycle using linear regression."""
    clean = data[["cycle", "soh_percent_smoothed"]].dropna()
    if len(clean) < 3:
        return None
    cycles = clean["cycle"].to_numpy(dtype=float)
    soh = clean["soh_percent_smoothed"].to_numpy(dtype=float)
    slope = float(np.polyfit(cycles, soh, 1)[0])
    return slope


def summarize_battery_metrics(data: pd.DataFrame) -> dict[str, float]:
    """Create a compact summary of the battery health trend."""
    first_row = data.iloc[0]
    last_row = data.iloc[-1]

    slope = estimate_soh_degradation_slope(data)

    summary: dict[str, float] = {
        "first_cycle": float(first_row["cycle"]),
        "last_cycle": float(last_row["cycle"]),
        "initial_capacity_ah": float(first_row["discharge_capacity_ah"]),
        "latest_capacity_ah": float(last_row["discharge_capacity_ah"]),
        "latest_soh_percent": float(last_row["soh_percent"]),
        "total_capacity_fade_percent": float(last_row["capacity_fade_percent"]),
        "max_temperature_c": float(data["max_temperature_c"].max()),
        "latest_internal_resistance_mohm": _safe_float(
            last_row["internal_resistance_mohm"]
        ),
    }
    if slope is not None:
        summary["soh_degradation_slope_per_cycle"] = slope
    return summary


def _safe_float(value: object) -> float:
    if pd.isna(value):
        return float("nan")
    return float(value)
