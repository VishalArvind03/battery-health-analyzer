import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from battery_health.config import load_limits
from battery_health.data_loader import load_cycle_data
from battery_health.data_quality import check_data_quality
from battery_health.interpretation import build_engineering_interpretation
from battery_health.metrics import add_battery_metrics, summarize_battery_metrics
from battery_health.report import write_html_report
from battery_health.validation import generate_health_warnings


def parse_args() -> argparse.Namespace:
    default_real_data = PROJECT_ROOT / "data" / "processed" / "nasa_B0005_cycles.csv"
    default_sample_data = PROJECT_ROOT / "data" / "sample_battery_cycles.csv"

    if default_real_data.exists():
        default_data_path = default_real_data
    else:
        default_data_path = default_sample_data

    parser = argparse.ArgumentParser(description="Analyze battery cycle health data.")
    parser.add_argument(
        "--data",
        default=str(default_data_path),
        help="Path to the battery cycle CSV file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_path = Path(args.data)
    config_path = PROJECT_ROOT / "config" / "limits.json"
    results_dir = PROJECT_ROOT / "results"

    limits = load_limits(config_path)
    # Load once in the original file order so the quality check can spot
    # out-of-order cycles, then sort a copy for the analysis itself.
    as_provided = load_cycle_data(data_path, sort=False)
    data_quality = check_data_quality(as_provided)
    raw_data = as_provided.sort_values("cycle").reset_index(drop=True)
    analyzed_data = add_battery_metrics(raw_data)
    summary = summarize_battery_metrics(analyzed_data)
    warnings = generate_health_warnings(analyzed_data, limits)
    interpretation = build_engineering_interpretation(analyzed_data, summary, warnings)

    results_dir.mkdir(exist_ok=True)
    summary_path = results_dir / "step1_summary.csv"
    report_path = results_dir / "step1_report.html"
    warnings_path = results_dir / "step2_warnings.txt"
    interpretation_path = results_dir / "step4_interpretation.txt"
    data_quality_path = results_dir / "step9_data_quality.txt"

    analyzed_data.to_csv(summary_path, index=False)
    warnings_path.write_text("\n".join(warnings), encoding="utf-8")
    interpretation_path.write_text(interpretation, encoding="utf-8")
    data_quality_path.write_text("\n".join(data_quality), encoding="utf-8")
    write_html_report(
        analyzed_data, summary, report_path, warnings, interpretation, data_quality
    )

    print("Battery health analysis complete.")
    print(f"Input data: {data_path}")
    print(f"Config file: {config_path}")
    print(f"Summary CSV: {summary_path}")
    print(f"HTML report: {report_path}")
    print(f"Warnings file: {warnings_path}")
    print(f"Interpretation file: {interpretation_path}")
    print(f"Data-quality file: {data_quality_path}")
    print(f"Latest SOH: {summary['latest_soh_percent']:.2f}%")
    print(f"Capacity fade: {summary['total_capacity_fade_percent']:.2f}%")
    print("Data quality:")
    for finding in data_quality:
        print(f"- {finding}")
    print("Warnings:")
    for warning in warnings:
        print(f"- {warning}")
    print("Interpretation:")
    print(interpretation)


if __name__ == "__main__":
    main()
