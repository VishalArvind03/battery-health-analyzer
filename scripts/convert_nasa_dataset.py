from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from battery_health.nasa_importer import convert_nasa_mat_to_cycle_csv

# The four NASA cells used in the multi-cell comparison (Stage 3).
NASA_BATTERY_IDS = ["B0005", "B0006", "B0007", "B0018"]


def main() -> None:
    raw_dir = PROJECT_ROOT / "data" / "raw" / "nasa"
    processed_dir = PROJECT_ROOT / "data" / "processed"

    converted_any = False
    for battery_id in NASA_BATTERY_IDS:
        mat_path = raw_dir / f"{battery_id}.mat"
        output_csv_path = processed_dir / f"nasa_{battery_id}_cycles.csv"

        if not mat_path.exists():
            print(f"Skipping {battery_id}: {mat_path} not found.")
            continue

        converted_data = convert_nasa_mat_to_cycle_csv(
            mat_path=mat_path,
            output_csv_path=output_csv_path,
            battery_id=battery_id,
        )
        converted_any = True

        print(f"Converted {battery_id}: {len(converted_data)} discharge cycles -> {output_csv_path.name}")
        print(
            f"  Initial capacity: {converted_data.iloc[0]['discharge_capacity_ah']:.3f} Ah, "
            f"Final capacity: {converted_data.iloc[-1]['discharge_capacity_ah']:.3f} Ah"
        )

    if not converted_any:
        print(
            "No NASA .mat files were found. Download the dataset into "
            "data/raw/nasa/ and run this script again."
        )


if __name__ == "__main__":
    main()
