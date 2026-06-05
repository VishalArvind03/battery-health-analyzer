from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

import pandas as pd

from battery_health.comparison import (
    analyze_cell,
    write_comparison_csv,
    write_comparison_html,
)
from battery_health.data_loader import load_cycle_data
from battery_health.metrics import add_battery_metrics

NASA_BATTERY_IDS = ["B0005", "B0006", "B0007", "B0018"]


def main() -> None:
    processed_dir = PROJECT_ROOT / "data" / "processed"
    results_dir = PROJECT_ROOT / "results"
    results_dir.mkdir(exist_ok=True)

    rows = []
    soh_curves: dict[str, tuple[list[float], list[float]]] = {}

    for battery_id in NASA_BATTERY_IDS:
        csv_path = processed_dir / f"nasa_{battery_id}_cycles.csv"
        if not csv_path.exists():
            print(f"Skipping {battery_id}: {csv_path.name} not found. Run convert_nasa_dataset.py first.")
            continue

        rows.append(analyze_cell(csv_path))

        # Collect the SOH curve so the report can overlay all cells on one chart.
        analyzed = add_battery_metrics(load_cycle_data(csv_path))
        soh_curves[battery_id] = (
            analyzed["cycle"].tolist(),
            analyzed["soh_percent"].tolist(),
        )

    if not rows:
        print("No processed NASA cell data found. Run scripts/convert_nasa_dataset.py first.")
        return

    comparison = pd.DataFrame(rows)
    csv_path = results_dir / "nasa_comparison.csv"
    html_path = results_dir / "nasa_comparison.html"

    write_comparison_csv(comparison, csv_path)
    write_comparison_html(comparison, html_path, soh_curves)

    print("NASA multi-cell comparison complete.")
    print(f"Cells compared: {', '.join(comparison['battery_id'])}")
    print(f"Comparison CSV: {csv_path}")
    print(f"Comparison HTML: {html_path}")
    print()
    print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()
