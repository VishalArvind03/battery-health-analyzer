# Step 10: NASA Multi-Cell Comparison (Stage 3)

## What this step adds

Until now the tool analyzed one cell at a time. This step analyzes **four** NASA
cells (B0005, B0006, B0007, B0018) with the same pipeline and puts their
headline results side by side. It produces:

- `results/nasa_comparison.csv` — the comparison table (open in Excel)
- `results/nasa_comparison.html` — the same table plus an overlaid SOH-vs-cycle
  chart showing all four cells on one set of axes

## How to run it

```bash
# 1. convert all four .mat files to CSV (one-time, needs the .mat files)
python scripts/convert_nasa_dataset.py

# 2. build the comparison
python scripts/compare_nasa_cells.py
```

## What is compared

For each cell the comparison reports:

| Metric | Meaning |
|---|---|
| Cycles | How many discharge cycles were analyzed |
| Initial / Final capacity | Discharge capacity at the first and last cycle |
| Final SOH (%) | State of health at the last cycle |
| Fade (%) | Total capacity fade (100 − final SOH) |
| Slope (%/cycle) | Average SOH lost per cycle (from the smoothed trend) |
| Max T (C) | Hottest recorded temperature |
| R rise (%) | Internal-resistance increase from first to last reading |
| Cycles to 80% SOH | Cycles before the cell first dropped to 80% SOH |

"Cycles to 80% SOH" is a common end-of-life marker for lithium-ion cells. If a
cell never drops that low, the report shows "not reached".

## Example result (real NASA data)

| Cell | Cycles | Final SOH | Fade | Slope | Max T | R rise | Cycles to 80% |
|---|---|---|---|---|---|---|---|
| B0005 | 168 | 71.38% | 28.62% | −0.2082 | 41.45 | 12.02% | 101 |
| B0006 | 168 | 58.25% | 41.75% | −0.2498 | 42.01 | 20.18% | 61 |
| B0007 | 168 | 75.75% | 24.25% | −0.1729 | 42.33 | 75.91% | 124 |
| B0018 | 132 | 72.29% | 27.71% | −0.2114 | 38.88 | 1.40% | 75 |

What this tells us: **B0006 aged fastest** (steepest slope, reached 80% SOH after
only 61 cycles), while **B0007 aged slowest** but showed the largest resistance
rise. This is exactly the kind of comparison an engineer makes when screening
cells — and it shows the analysis pipeline is reusable across datasets.

## How the code is organised

- `src/battery_health/comparison.py` — `analyze_cell()` runs the existing
  metrics on one CSV and returns a row of results; `compare_cells()` builds a
  table from several cells; two writer functions save the CSV and HTML.
- `scripts/compare_nasa_cells.py` — the command you run; it finds the processed
  CSVs, builds the comparison, and also collects each cell's SOH curve for the
  overlay chart.

The comparison module **reuses** the Stage 1 metric functions
(`add_battery_metrics`, `summarize_battery_metrics`,
`estimate_soh_degradation_slope`). Nothing is recalculated by hand, so the
single-cell and multi-cell results are guaranteed to agree.

## How it was verified

- 6 new tests in `tests/test_comparison.py` cover the metric keys, the
  "cycles to 80% SOH" logic (both reached and not-reached), the resistance-rise
  calculation, and that one row is produced per cell.
- The real run produces sensible, physically reasonable numbers and a chart with
  all four SOH curves.

## Interview soundbite

> "I extended the pipeline to compare four NASA cells side by side — final SOH,
> capacity fade, degradation slope, peak temperature, resistance rise, and cycles
> to 80% SOH — and produced a CSV plus an HTML report with all four SOH curves
> overlaid. B0006 aged fastest and B0007 slowest. The comparison reuses the same
> metric functions as the single-cell analysis, so the results stay consistent."
