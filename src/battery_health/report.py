from pathlib import Path
import math

import pandas as pd


def write_html_report(
    data: pd.DataFrame,
    summary: dict[str, float],
    output_path: str | Path,
    warnings: list[str] | None = None,
    interpretation: str | None = None,
    data_quality: list[str] | None = None,
) -> None:
    """Write a simple standalone HTML report with engineering plots."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    cycles = data["cycle"].tolist()

    def smoothed_or_none(col: str) -> list | None:
        return data[col].tolist() if col in data.columns else None

    charts = [
        (
            "SOH vs Cycle (raw + smoothed)",
            _build_svg_line_chart(
                x_values=cycles,
                y_values=data["soh_percent"].tolist(),
                x_label="Cycle",
                y_label="SOH (%)",
                stroke_color="#0070c0",
                smoothed_y_values=smoothed_or_none("soh_percent_smoothed"),
            ),
        ),
        (
            "Capacity Fade vs Cycle (raw + smoothed)",
            _build_svg_line_chart(
                x_values=cycles,
                y_values=data["capacity_fade_percent"].tolist(),
                x_label="Cycle",
                y_label="Fade (%)",
                stroke_color="#c00000",
                smoothed_y_values=smoothed_or_none("capacity_fade_percent_smoothed"),
            ),
        ),
        (
            "Internal Resistance vs Cycle (raw + smoothed)",
            _build_svg_line_chart(
                x_values=cycles,
                y_values=data["internal_resistance_mohm"].tolist(),
                x_label="Cycle",
                y_label="Resistance (mohm)",
                stroke_color="#6f42c1",
                smoothed_y_values=smoothed_or_none("internal_resistance_mohm_smoothed"),
            ),
        ),
        (
            "Maximum Temperature vs Cycle",
            _build_svg_line_chart(
                x_values=cycles,
                y_values=data["max_temperature_c"].tolist(),
                x_label="Cycle",
                y_label="Temperature (C)",
                stroke_color="#d97706",
            ),
        ),
        (
            "Coulombic Efficiency vs Cycle",
            _build_svg_line_chart(
                x_values=cycles,
                y_values=data["coulombic_efficiency_percent"].tolist(),
                x_label="Cycle",
                y_label="Efficiency (%)",
                stroke_color="#00875a",
            ),
        ),
    ]

    summary_rows = "\n".join(
        f"<tr><th>{key}</th><td>{value:.2f}</td></tr>" for key, value in summary.items()
    )
    warning_items = "\n".join(f"<li>{warning}</li>" for warning in (warnings or []))
    interpretation_text = interpretation or "No interpretation was generated."

    quality_findings = data_quality or ["Data-quality check was not run."]
    quality_clean = quality_findings == ["No data-quality issues detected."]
    quality_class = "quality-clean" if quality_clean else "quality-issues"
    quality_items = "\n".join(f"<li>{finding}</li>" for finding in quality_findings)

    html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>Battery Health Analyzer</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2933; }}
    h1, h2 {{ margin-bottom: 8px; }}
    .chart {{ margin: 24px 0 32px; }}
    .chart h3 {{ margin: 0 0 8px; font-size: 16px; }}
    .interpretation {{ max-width: 820px; line-height: 1.55; background: #f8fafc; border-left: 4px solid #0070c0; padding: 12px 16px; }}
    table {{ border-collapse: collapse; margin-top: 16px; min-width: 420px; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 8px 12px; text-align: left; }}
    th {{ background: #f0f4f8; }}
    .note {{ max-width: 760px; line-height: 1.5; }}
    .quality-clean {{ border-left: 4px solid #00875a; background: #f0fdf4; padding: 8px 16px; }}
    .quality-issues {{ border-left: 4px solid #d97706; background: #fffbeb; padding: 8px 16px; }}
  </style>
</head>
<body>
  <h1>Battery Health Analyzer</h1>
  <p class=\"note\">This report analyzes battery cycling data and calculates state of health using discharge capacity relative to the first available cycle.</p>
  <h2>Engineering Plots</h2>
  {_build_chart_sections(charts)}
  <h2>Summary</h2>
  <table>
    {summary_rows}
  </table>
  <h2>Data Quality</h2>
  <ul class=\"{quality_class}\">
    {quality_items}
  </ul>
  <h2>Engineering Interpretation</h2>
  <p class=\"interpretation\">{interpretation_text}</p>
  <h2>Warnings</h2>
  <ul>
    {warning_items}
  </ul>
</body>
</html>
"""

    path.write_text(html, encoding="utf-8")


def _build_chart_sections(charts: list[tuple[str, str]]) -> str:
    return "\n".join(
        f'<section class="chart"><h3>{title}</h3>{chart_svg}</section>'
        for title, chart_svg in charts
    )


def _build_svg_line_chart(
    x_values: list[float],
    y_values: list[float],
    x_label: str,
    y_label: str,
    stroke_color: str,
    smoothed_y_values: list | None = None,
) -> str:
    clean_points = [
        (float(x), float(y))
        for x, y in zip(x_values, y_values)
        if pd.notna(x) and pd.notna(y) and math.isfinite(float(y))
    ]
    if len(clean_points) < 2:
        return "<p>Not enough numeric data available for this plot.</p>"

    x_vals = [p[0] for p in clean_points]
    y_vals = [p[1] for p in clean_points]

    smoothed_points: list[tuple[float, float]] = []
    if smoothed_y_values is not None:
        smoothed_points = [
            (float(x), float(y))
            for x, y in zip(x_values, smoothed_y_values)
            if pd.notna(x) and pd.notna(y) and math.isfinite(float(y))
        ]

    all_y = y_vals + [p[1] for p in smoothed_points]

    width = 820
    height = 360
    pad_left = 72
    pad_right = 24
    pad_top = 24
    pad_bottom = 56

    min_x = min(x_vals)
    max_x = max(x_vals)
    min_y = min(all_y) - 1
    max_y = max(all_y) + 1

    plot_width = width - pad_left - pad_right
    plot_height = height - pad_top - pad_bottom

    def scale_x(value: float) -> float:
        if max_x == min_x:
            return pad_left
        return pad_left + (value - min_x) / (max_x - min_x) * plot_width

    def scale_y(value: float) -> float:
        if max_y == min_y:
            return pad_top
        return pad_top + (max_y - value) / (max_y - min_y) * plot_height

    raw_polyline = " ".join(
        f"{scale_x(x):.1f},{scale_y(y):.1f}" for x, y in zip(x_vals, y_vals)
    )

    first_x = scale_x(x_vals[0])
    first_y = scale_y(y_vals[0])
    last_x = scale_x(x_vals[-1])
    last_y = scale_y(y_vals[-1])

    smoothed_layer = ""
    legend = ""
    if smoothed_points:
        sm_polyline = " ".join(
            f"{scale_x(x):.1f},{scale_y(y):.1f}" for x, y in smoothed_points
        )
        smoothed_layer = (
            f'<polyline points="{sm_polyline}" fill="none" stroke="{stroke_color}" '
            f'stroke-width="2.5" />'
        )
        legend_x = pad_left + 8
        legend_y = pad_top + 12
        legend = (
            f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 20}" y2="{legend_y}" '
            f'stroke="{stroke_color}" stroke-width="1" stroke-dasharray="4 3" opacity="0.5" />'
            f'<text x="{legend_x + 24}" y="{legend_y + 4}" font-size="11" fill="#52616b">raw</text>'
            f'<line x1="{legend_x + 60}" y1="{legend_y}" x2="{legend_x + 80}" y2="{legend_y}" '
            f'stroke="{stroke_color}" stroke-width="2.5" />'
            f'<text x="{legend_x + 84}" y="{legend_y + 4}" font-size="11" fill="#52616b">smoothed</text>'
        )

    raw_style = 'stroke-dasharray="4 3" opacity="0.45"' if smoothed_points else ""

    return f"""
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{y_label} curve">
  <rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff" />
  <line x1="{pad_left}" y1="{height - pad_bottom}" x2="{width - pad_right}" y2="{height - pad_bottom}" stroke="#52616b" />
  <line x1="{pad_left}" y1="{pad_top}" x2="{pad_left}" y2="{height - pad_bottom}" stroke="#52616b" />
  <polyline points="{raw_polyline}" fill="none" stroke="{stroke_color}" stroke-width="1.5" {raw_style} />
  {smoothed_layer}
  {legend}
  <circle cx="{first_x:.1f}" cy="{first_y:.1f}" r="4" fill="{stroke_color}" />
  <circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="4" fill="#c00000" />
  <text x="{width / 2:.1f}" y="{height - 14}" text-anchor="middle" font-size="14">{x_label}</text>
  <text x="18" y="{height / 2:.1f}" text-anchor="middle" font-size="14" transform="rotate(-90 18 {height / 2:.1f})">{y_label}</text>
  <text x="{pad_left}" y="{height - pad_bottom + 22}" text-anchor="middle" font-size="12">{min_x:.0f}</text>
  <text x="{width - pad_right}" y="{height - pad_bottom + 22}" text-anchor="middle" font-size="12">{max_x:.0f}</text>
  <text x="{pad_left - 10}" y="{scale_y(max_y):.1f}" text-anchor="end" font-size="12">{max_y:.1f}</text>
  <text x="{pad_left - 10}" y="{scale_y(min_y):.1f}" text-anchor="end" font-size="12">{min_y:.1f}</text>
</svg>
"""
