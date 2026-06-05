# Step 9: Data-Quality Validation (Stage 2)

## What this step adds

A new module, `src/battery_health/data_quality.py`, that inspects the input data
*before* it is trusted and reports anything that looks wrong. The findings are
printed to the terminal, saved to `results/step9_data_quality.txt`, and shown in
a new **Data Quality** section at the top of the HTML report (green when clean,
amber when issues are found).

## Why this matters

SOH and degradation numbers are only as good as the data behind them. Real test
data can have typos, sensor glitches, missing rows, or duplicated cycles. If a
single capacity value is wrong, the whole SOH curve can look misleading. This
step is a quick "is the data sane?" gate.

Important: these are **sanity checks, not safety limits**. A finding means "look
at this data", not "the battery is unsafe". (The safety-style engineering
warnings are a separate feature in `validation.py`.)

## The seven checks

| Check | What it looks for | Why it matters |
|---|---|---|
| Insufficient data | Fewer than 5 cycles | A trend needs enough points to mean anything |
| Missing values | NaN / non-numeric in key columns | Missing readings break the math |
| Duplicate cycles | The same cycle number twice | Usually a logging or merge error |
| Invalid capacity | Discharge capacity ≤ 0 | Physically impossible |
| Unrealistic temperatures | Outside −40 °C to 80 °C | Almost always a broken sensor |
| Incorrectly ordered cycles | Cycle numbers not increasing in the file | Signals a data-export problem |
| Abnormal jumps | >20% capacity change between neighbours | Likely a measurement glitch |

If none of these fire, the report shows a single green line:
"No data-quality issues detected."

## A design detail worth understanding

The data loader normally **sorts** the rows by cycle, because the analysis needs
them in order. But sorting would hide the "incorrectly ordered cycles" problem.
So the loader now accepts `sort=False`, and `main.py` loads the data twice in
spirit: it reads it once in the original order for the quality check, then sorts
a copy for the analysis.

```python
as_provided = load_cycle_data(data_path, sort=False)   # original order
data_quality = check_data_quality(as_provided)          # can see ordering
raw_data = as_provided.sort_values("cycle").reset_index(drop=True)  # for analysis
```

## Configurable thresholds

The temperature range, the jump fraction, and the minimum-cycle count are all
function arguments with sensible defaults, so the check can be tightened without
editing the logic:

```python
check_data_quality(data, max_temperature_c=32.0)  # stricter ceiling
```

## How it was verified

- 9 new tests in `tests/test_data_quality.py` — one clean-data test plus one test
  per check, confirming each problem is detected.
- Both real datasets (NASA B0005 and the sample file) run end-to-end and report
  **no** data-quality issues, confirming there are no false alarms on good data.

## Interview soundbite

> "Before calculating SOH, the tool runs a data-quality gate that flags missing
> values, duplicate or out-of-order cycles, impossible capacity or temperature
> readings, and abnormal cycle-to-cycle jumps. The result is shown at the top of
> the report. I kept it separate from the engineering warnings because one checks
> *data integrity* and the other checks *battery health*."
