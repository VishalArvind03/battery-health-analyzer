from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "cycle",
    "discharge_capacity_ah",
    "avg_voltage_v",
    "max_temperature_c",
}

OPTIONAL_COLUMNS = {
    "charge_capacity_ah",
    "internal_resistance_mohm",
}


def load_cycle_data(csv_path: str | Path, sort: bool = True) -> pd.DataFrame:
    """Load battery cycle data and check that the expected columns exist.

    By default the rows are sorted by cycle, which is what the analysis needs.
    Pass ``sort=False`` to keep the original file order — the data-quality check
    uses this so it can detect cycles that were stored out of order.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Could not find data file: {path}")

    data = pd.read_csv(path)
    missing_columns = REQUIRED_COLUMNS.difference(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing}")

    for column in OPTIONAL_COLUMNS.difference(data.columns):
        data[column] = pd.NA

    if sort:
        data = data.sort_values("cycle").reset_index(drop=True)
    return data
