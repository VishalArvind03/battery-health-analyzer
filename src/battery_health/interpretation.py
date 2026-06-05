import pandas as pd


def build_engineering_interpretation(
    data: pd.DataFrame,
    summary: dict[str, float],
    warnings: list[str],
) -> str:
    """Build a short engineering interpretation from battery health results."""
    resistance_series = pd.to_numeric(
        data["internal_resistance_mohm"], errors="coerce"
    ).dropna()

    latest_soh = summary["latest_soh_percent"]
    capacity_fade = summary["total_capacity_fade_percent"]
    max_temperature = summary["max_temperature_c"]

    if len(resistance_series) >= 2:
        initial_resistance = float(resistance_series.iloc[0])
        latest_resistance = float(resistance_series.iloc[-1])
        resistance_rise_percent = (
            (latest_resistance - initial_resistance) / initial_resistance * 100
        )
        resistance_statement = (
            f"Internal resistance increased from {initial_resistance:.2f} mohms to "
            f"{latest_resistance:.2f} mohms, a rise of {resistance_rise_percent:.2f}%. "
        )
    else:
        resistance_statement = "Internal resistance data was not available for this dataset. "

    slope = summary.get("soh_degradation_slope_per_cycle")
    if slope is not None:
        trend_statement = (
            f"The smoothed SOH trend shows an average degradation of "
            f"{abs(slope):.4f}% SOH per cycle. "
        )
    else:
        trend_statement = ""

    if _has_real_warnings(warnings):
        risk_statement = (
            "The warning checks show that at least one engineering limit was exceeded, "
            "so the data should be reviewed before treating the cell as healthy."
        )
    else:
        risk_statement = (
            "No engineering warning limits were exceeded with the current threshold settings."
        )

    return (
        f"The cell retains {latest_soh:.2f}% SOH after "
        f"{summary['last_cycle']:.0f} cycles, corresponding to {capacity_fade:.2f}% "
        "capacity fade. "
        f"{resistance_statement}"
        f"{trend_statement}"
        f"The maximum recorded temperature was {max_temperature:.2f} C. "
        f"{risk_statement}"
    )


def _has_real_warnings(warnings: list[str]) -> bool:
    return any(not warning.startswith("No warnings") for warning in warnings)
