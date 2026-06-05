import pandas as pd


def generate_health_warnings(
    data: pd.DataFrame,
    limits: dict[str, float],
) -> list[str]:
    """Generate simple engineering warnings from analyzed battery cycle data."""
    warnings = []
    soh_limit_percent = limits["soh_limit_percent"]
    temperature_limit_c = limits["temperature_limit_c"]
    resistance_rise_limit_percent = limits["resistance_rise_limit_percent"]
    coulombic_efficiency_limit_percent = limits["coulombic_efficiency_limit_percent"]

    latest_soh = float(data.iloc[-1]["soh_percent"])
    max_temperature = float(data["max_temperature_c"].max())
    resistance_series = pd.to_numeric(
        data["internal_resistance_mohm"], errors="coerce"
    ).dropna()
    coulombic_efficiency_series = pd.to_numeric(
        data["coulombic_efficiency_percent"], errors="coerce"
    ).dropna()

    if latest_soh < soh_limit_percent:
        warnings.append(
            f"SOH warning: latest SOH is {latest_soh:.2f}%, below the {soh_limit_percent:.2f}% limit."
        )

    if max_temperature > temperature_limit_c:
        warnings.append(
            f"Temperature warning: maximum temperature is {max_temperature:.2f} C, above the {temperature_limit_c:.2f} C limit."
        )

    if len(resistance_series) >= 2:
        initial_resistance = float(resistance_series.iloc[0])
        latest_resistance = float(resistance_series.iloc[-1])
        resistance_rise_percent = (
            (latest_resistance - initial_resistance) / initial_resistance * 100
        )
        if resistance_rise_percent > resistance_rise_limit_percent:
            warnings.append(
                "Resistance warning: internal resistance increased by "
                f"{resistance_rise_percent:.2f}%, above the {resistance_rise_limit_percent:.2f}% limit."
            )

    if not coulombic_efficiency_series.empty:
        min_coulombic_efficiency = float(coulombic_efficiency_series.min())
        if min_coulombic_efficiency < coulombic_efficiency_limit_percent:
            warnings.append(
                "Efficiency warning: minimum coulombic efficiency is "
                f"{min_coulombic_efficiency:.2f}%, below the {coulombic_efficiency_limit_percent:.2f}% limit."
            )

    if not warnings:
        warnings.append("No warnings triggered by the current engineering limits.")

    return warnings
