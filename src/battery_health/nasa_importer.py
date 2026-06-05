from pathlib import Path

import numpy as np
import pandas as pd


def convert_nasa_mat_to_cycle_csv(
    mat_path: str | Path,
    output_csv_path: str | Path,
    battery_id: str | None = None,
) -> pd.DataFrame:
    """Convert one NASA battery .mat file into the project's cycle-level CSV format."""
    try:
        from scipy.io import loadmat
    except ImportError as exc:
        raise ImportError(
            "SciPy is required to read NASA .mat files. Run: python -m pip install -r requirements.txt"
        ) from exc

    mat_path = Path(mat_path)
    output_csv_path = Path(output_csv_path)
    battery_id = battery_id or mat_path.stem

    mat_data = loadmat(mat_path, squeeze_me=True, struct_as_record=False)
    battery = mat_data[battery_id]
    cycles = battery.cycle

    impedance_points: list[tuple[int, float]] = []
    discharge_rows: list[dict[str, float | int | str | None]] = []

    for source_cycle_index, cycle in enumerate(cycles):
        cycle_type = str(cycle.type)

        if cycle_type == "impedance":
            re_value = getattr(cycle.data, "Re", None)
            if re_value is not None:
                impedance_points.append((source_cycle_index, float(np.real(re_value)) * 1000))
            continue

        if cycle_type != "discharge":
            continue

        voltage = np.asarray(cycle.data.Voltage_measured, dtype=float)
        current = np.asarray(cycle.data.Current_measured, dtype=float)
        temperature = np.asarray(cycle.data.Temperature_measured, dtype=float)
        time_s = np.asarray(cycle.data.Time, dtype=float)

        discharge_rows.append(
            {
                "battery_id": battery_id,
                "source_cycle_index": source_cycle_index,
                "cycle": len(discharge_rows) + 1,
                "discharge_capacity_ah": float(cycle.data.Capacity),
                "charge_capacity_ah": None,
                "avg_voltage_v": float(np.mean(voltage)),
                "max_temperature_c": float(np.max(temperature)),
                "internal_resistance_mohm": None,
                "ambient_temperature_c": float(cycle.ambient_temperature),
                "avg_discharge_current_a": float(abs(np.mean(current))),
                "discharge_duration_s": float(time_s[-1] - time_s[0]),
            }
        )

    for row in discharge_rows:
        row["internal_resistance_mohm"] = _nearest_impedance_value(
            source_cycle_index=int(row["source_cycle_index"]),
            impedance_points=impedance_points,
        )

    converted_data = pd.DataFrame(discharge_rows)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    converted_data.to_csv(output_csv_path, index=False)
    return converted_data


def _nearest_impedance_value(
    source_cycle_index: int,
    impedance_points: list[tuple[int, float]],
) -> float | None:
    if not impedance_points:
        return None

    _, resistance_mohm = min(
        impedance_points,
        key=lambda point: abs(point[0] - source_cycle_index),
    )
    return resistance_mohm
