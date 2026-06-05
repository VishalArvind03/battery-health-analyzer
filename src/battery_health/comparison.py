"""Multi-cell comparison for the NASA battery dataset.

Stage 1 and 2 analyze one cell at a time. This module analyzes several cells
(B0005, B0006, B0007, B0018) and puts their headline results side by side, so we
can see which cell aged fastest, ran hottest, or lost the most capacity.

It produces two outputs:
- a comparison CSV (easy to open in Excel)
- a comparison HTML report (a table plus an overlaid SOH-vs-cycle chart)
"""

from pathlib import Path

import pandas as pd

from battery_health.data_loader import load_cycle_data
from battery_health.metrics import (
    add_battery_metrics,
    estimate_soh_degradation_slope,
    summarize_battery_metrics,
)

# SOH level used to measure "how long did the cell last?"
END_OF_LIFE_SOH_PERCENT = 80.0


def analyze_cell(csv_path: str | Path) -> dict[str, object]:
    """Load one cell's CSV and return its headline comparison metrics."""
    raw_data = load_cycle_data(csv_path)
    analyzed = add_battery_metrics(raw_data)
    summary = summarize_battery_metrics(analyzed)

    battery_id = _battery_id_from_data(analyzed, csv_path)
    slope = estimate_soh_degradation_slope(analyzed)

    return {
        "battery_id": battery_id,
        "cycles_analyzed": int(len(analyzed)),
        "initial_capacity_ah": round(summary["initial_capacity_ah"], 3),
        "final_capacity_ah": round(summary["latest_capacity_ah"], 3),
        "final_soh_percent": round(summary["latest_soh_percent"], 2),
        "capacity_fade_percent": round(summary["total_capacity_fade_percent"], 2),
        "degradation_slope_per_cycle": round(slope, 4) if slope is not None else None,
        "max_temperature_c": round(summary["max_temperature_c"], 2),
        "resistance_rise_percent": _resistance_rise_percent(analyzed),
        "cycles_to_80_percent_soh": _cycles_to_threshold(analyzed, END_OF_LIFE_SOH_PERCENT),
    }


def compare_cells(csv_paths: list[str | Path]) -> pd.DataFrame:
    """Analyze several cells and return one row of metrics per cell."""
    rows = [analyze_cell(path) for path in csv_paths]
    return pd.DataFrame(rows)


def write_comparison_csv(comparison: pd.DataFrame, output_path: str | Path) -> None:
    """Save the comparison table as a CSV file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(path, index=False)


def write_comparison_html(
    comparison: pd.DataFrame,
    output_path: str | Path,
    soh_curves: dict[str, tuple[list[float], list[float]]] | None = None,
) -> None:
    """Save the comparison as an HTML report (table + optional SOH overlay chart)."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    table_html = _build_comparison_table(comparison)
    chart_html = _build_soh_overlay_chart(soh_curves) if soh_curves else ""

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>NASA Multi-Cell Comparison</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2933; }}
    h1, h2 {{ margin-bottom: 8px; }}
    table {{ border-collapse: collapse; margin-top: 16px; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 8px 12px; text-align: right; }}
    th {{ background: #f0f4f8; text-align: center; }}
    td:first-child, th:first-child {{ text-align: left; }}
    .note {{ max-width: 820px; line-height: 1.5; }}
    .chart {{ margin: 24px 0; }}
  </style>
</head>
<body>
  <h1>NASA Multi-Cell Comparison</h1>
  <p class="note">Headline ageing results for several NASA lithium-ion cells, analyzed with the same pipeline. "Cycles to 80% SOH" is the number of cycles before the cell first dropped to 80% state of health; "not reached" means it stayed above 80% for the whole test.</p>
  <h2>SOH vs Cycle</h2>
  <div class="chart">{chart_html}</div>
  <h2>Comparison Table</h2>
  {table_html}
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


# --- helpers -----------------------------------------------------------------


def _battery_id_from_data(data: pd.DataFrame, csv_path: str | Path) -> str:
    if "battery_id" in data.columns and data["battery_id"].notna().any():
        return str(data["battery_id"].iloc[0])
    return Path(csv_path).stem


def _cycles_to_threshold(data: pd.DataFrame, threshold_percent: float) -> object:
    """First cycle number at or below the SOH threshold, or 'not reached'."""
    below = data[data["soh_percent"] <= threshold_percent]
    if below.empty:
        return "not reached"
    return int(below["cycle"].iloc[0])


def _resistance_rise_percent(data: pd.DataFrame) -> object:
    """Percent rise from first to last internal-resistance reading, if available."""
    resistance = pd.to_numeric(data["internal_resistance_mohm"], errors="coerce").dropna()
    if len(resistance) < 2:
        return None
    first = float(resistance.iloc[0])
    last = float(resistance.iloc[-1])
    if first == 0:
        return None
    return round((last - first) / first * 100, 2)


def _build_comparison_table(comparison: pd.DataFrame) -> str:
    # Friendly column headings for the report.
    headings = {
        "battery_id": "Cell",
        "cycles_analyzed": "Cycles",
        "initial_capacity_ah": "Initial (Ah)",
        "final_capacity_ah": "Final (Ah)",
        "final_soh_percent": "Final SOH (%)",
        "capacity_fade_percent": "Fade (%)",
        "degradation_slope_per_cycle": "Slope (%/cycle)",
        "max_temperature_c": "Max T (C)",
        "resistance_rise_percent": "R rise (%)",
        "cycles_to_80_percent_soh": "Cycles to 80% SOH",
    }
    header = "".join(f"<th>{headings.get(col, col)}</th>" for col in comparison.columns)
    body_rows = []
    for _, row in comparison.iterrows():
        cells = "".join(f"<td>{_format_cell(value)}</td>" for value in row)
        body_rows.append(f"<tr>{cells}</tr>")
    return f"<table><tr>{header}</tr>{''.join(body_rows)}</table>"


def _format_cell(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "n/a"
    return str(value)


def _build_soh_overlay_chart(
    soh_curves: dict[str, tuple[list[float], list[float]]],
) -> str:
    """Draw every cell's SOH curve on one set of axes as a simple SVG."""
    colors = ["#0070c0", "#c00000", "#00875a", "#d97706", "#6f42c1"]

    all_x = [x for cycles, _ in soh_curves.values() for x in cycles]
    all_y = [y for _, soh in soh_curves.values() for y in soh]
    if len(all_x) < 2:
        return "<p>Not enough data to draw the comparison chart.</p>"

    width, height = 820, 380
    pad_left, pad_right, pad_top, pad_bottom = 64, 140, 24, 48
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y) - 2, max(all_y) + 2
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    def sx(v: float) -> float:
        return pad_left if max_x == min_x else pad_left + (v - min_x) / (max_x - min_x) * plot_w

    def sy(v: float) -> float:
        return pad_top if max_y == min_y else pad_top + (max_y - v) / (max_y - min_y) * plot_h

    lines = []
    legend = []
    for index, (battery_id, (cycles, soh)) in enumerate(soh_curves.items()):
        color = colors[index % len(colors)]
        points = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in zip(cycles, soh))
        lines.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2" />')
        legend_y = pad_top + 8 + index * 18
        legend.append(
            f'<line x1="{width - pad_right + 8}" y1="{legend_y}" x2="{width - pad_right + 28}" y2="{legend_y}" stroke="{color}" stroke-width="2.5" />'
            f'<text x="{width - pad_right + 32}" y="{legend_y + 4}" font-size="12" fill="#52616b">{battery_id}</text>'
        )

    return f"""
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="SOH comparison">
  <rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff" />
  <line x1="{pad_left}" y1="{height - pad_bottom}" x2="{width - pad_right}" y2="{height - pad_bottom}" stroke="#52616b" />
  <line x1="{pad_left}" y1="{pad_top}" x2="{pad_left}" y2="{height - pad_bottom}" stroke="#52616b" />
  {''.join(lines)}
  {''.join(legend)}
  <text x="{(pad_left + width - pad_right) / 2:.0f}" y="{height - 12}" text-anchor="middle" font-size="13">Cycle</text>
  <text x="18" y="{height / 2:.0f}" text-anchor="middle" font-size="13" transform="rotate(-90 18 {height / 2:.0f})">SOH (%)</text>
  <text x="{pad_left - 8}" y="{sy(max_y):.1f}" text-anchor="end" font-size="11">{max_y:.0f}</text>
  <text x="{pad_left - 8}" y="{sy(min_y):.1f}" text-anchor="end" font-size="11">{min_y:.0f}</text>
  <text x="{pad_left}" y="{height - pad_bottom + 18}" text-anchor="middle" font-size="11">{min_x:.0f}</text>
  <text x="{width - pad_right}" y="{height - pad_bottom + 18}" text-anchor="middle" font-size="11">{max_x:.0f}</text>
</svg>
"""
