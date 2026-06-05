# Step 7: Smoothing and Trend Analysis

## What was added in this step

Step 7 adds rolling-average smoothing to the battery health curves and estimates how fast the cell is degrading over its lifetime.

---

## Why smoothing is needed

Real battery test data is noisy. The NASA B0005 dataset was measured in a lab under controlled conditions, but small variations in temperature, measurement equipment, and cell chemistry cause the capacity to fluctuate slightly from cycle to cycle. This makes the raw SOH curve look jagged even though the real degradation trend is smooth.

A rolling average (also called a moving average) is a simple way to reduce this noise. The idea is:

> Instead of plotting the raw SOH value at cycle 50, plot the average SOH of cycles 48, 49, 50, 51, and 52.

This smooths out the short-term noise and makes the long-term degradation trend much easier to see. The window size used here is **5 cycles**, meaning each smoothed point is the average of 5 nearby raw points.

---

## What was changed

### `src/battery_health/metrics.py`

A new internal function called `_add_smoothed_columns` was added. It uses Pandas `.rolling()` to calculate the rolling average for three signals:

- `soh_percent_smoothed`
- `capacity_fade_percent_smoothed`
- `internal_resistance_mohm_smoothed`

The `center=True` option means the window is centered on each data point rather than only looking backward. This avoids lagging the smoothed curve behind the raw curve.

A second new function called `estimate_soh_degradation_slope` was added. It fits a straight line through the smoothed SOH curve using `numpy.polyfit` and returns the slope of that line. The slope tells you how many percent of SOH the cell loses per cycle on average.

The `summarize_battery_metrics` function now includes the slope in the summary dictionary under the key `soh_degradation_slope_per_cycle`.

---

### `src/battery_health/report.py`

The three main charts (SOH, Capacity Fade, Internal Resistance) now show **two lines**:

- A **dashed, faint line** for the raw noisy data
- A **solid, darker line** for the smoothed trend

This way you can always see both — the smoothed line tells the story while the raw line shows the actual measurement scatter.

A small inline legend is included in each chart to label which line is raw and which is smoothed.

---

### `src/battery_health/interpretation.py`

The written interpretation text now includes a sentence about the smoothed degradation slope:

```
The smoothed SOH trend shows an average degradation of 0.2082% SOH per cycle.
```

This is a useful number for comparing cells or estimating remaining useful life.

---

## What the results mean

For the NASA B0005 cell:

- The smoothed SOH curve clearly shows steady degradation from about 100% down to 71% over 168 cycles
- The degradation slope is approximately **−0.21% SOH per cycle**
- This means the cell loses just over one-fifth of a percent of its health with every charge-discharge cycle

---

## Interview explanation

> "Real battery test data is noisy, so I added a 5-cycle rolling average to smooth the SOH and resistance curves. The smoothed curve makes the degradation trend much clearer. I also fitted a straight line through the smoothed SOH data using NumPy to estimate the average degradation rate, which came out to about 0.21% SOH lost per cycle for the NASA B0005 cell. Both raw and smoothed curves are shown in the report so the original data is always visible."

---

## Key Python functions used

| Function | What it does |
|---|---|
| `pandas.Series.rolling(window=5, center=True).mean()` | Calculates the rolling average over 5 cycles, centered on each point |
| `numpy.polyfit(x, y, 1)` | Fits a first-degree polynomial (a straight line) and returns the slope and intercept |

---

## What NOT to say in an interview

- Do not say this is a real BMS or production system.
- Do not say the smoothing removes all noise — it reduces it.
- Do not say the slope can predict exact remaining useful life without more data.
