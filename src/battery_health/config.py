import json
from pathlib import Path


DEFAULT_LIMITS = {
    "soh_limit_percent": 80.0,
    "temperature_limit_c": 45.0,
    "resistance_rise_limit_percent": 20.0,
    "coulombic_efficiency_limit_percent": 98.0,
}


def load_limits(config_path: str | Path) -> dict[str, float]:
    """Load engineering warning limits from a JSON config file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Could not find config file: {path}")

    with path.open("r", encoding="utf-8") as file:
        loaded_limits = json.load(file)

    limits = DEFAULT_LIMITS.copy()
    limits.update(loaded_limits)
    _validate_limits(limits)
    return limits


def _validate_limits(limits: dict[str, float]) -> None:
    for key, value in limits.items():
        if not isinstance(value, int | float):
            raise TypeError(f"Limit '{key}' must be a number.")
        if value <= 0:
            raise ValueError(f"Limit '{key}' must be greater than zero.")
