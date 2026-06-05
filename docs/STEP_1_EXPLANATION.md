# Step 1 Explanation

## What We Built

Step 1 creates the smallest useful version of the Battery Health Analyzer.

It does four things:

1. Loads sample battery cycling data from a CSV file.
2. Checks that the required columns are present.
3. Calculates battery health metrics.
4. Creates a CSV and HTML report inside the `results` folder.

## Important Concept: SOH

SOH means State of Health.

In this first version:

```text
SOH (%) = current discharge capacity / initial discharge capacity * 100
```

Example:

```text
Initial capacity = 2.50 Ah
Current capacity = 2.338 Ah
SOH = 2.338 / 2.50 * 100 = 93.52%
```

This is a simplified definition. Real battery testing can use more complex methods depending on the cell type, operating conditions, temperature, measurement accuracy, and test protocol.

## What Each File Does

- `data/sample_battery_cycles.csv`: sample battery cycling data.
- `main.py`: runs the Step 1 workflow.
- `src/battery_health/data_loader.py`: loads the CSV and checks columns.
- `src/battery_health/metrics.py`: calculates SOH, capacity fade, and coulombic efficiency.
- `src/battery_health/report.py`: creates the HTML report.
- `results/step1_summary.csv`: output data with calculated metrics.
- `results/step1_report.html`: visual report.

## What You Should Be Able To Explain

- What a CSV file is.
- What Pandas is used for.
- Why discharge capacity can be used to estimate SOH.
- Why SOH normally decreases with cycling.
- Why temperature and internal resistance are useful battery health indicators.
- What the code does when a required column is missing.
