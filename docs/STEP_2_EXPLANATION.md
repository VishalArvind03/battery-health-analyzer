# Step 2 Explanation

## What We Added

Step 2 adds basic engineering warning checks.

The project now checks:

- latest SOH
- maximum temperature
- internal resistance rise
- minimum coulombic efficiency

The warning logic is inside:

```text
src/battery_health/validation.py
```

## Why This Matters

Battery data analysis is not only about calculating numbers. In industry, you also need to check whether the numbers cross important limits.

This is common in:

- battery validation
- BMS testing
- end-of-line testing
- lifetime testing
- engineering reports

## Warning Rules In This Project

The current limits are:

```text
SOH limit = 80%
temperature limit = 45 C
internal resistance rise limit = 20%
coulombic efficiency limit = 98%
```

These are simple learning limits, not official standards.

## Important Concept: Internal Resistance Rise

As a battery ages, internal resistance usually increases.

In this project:

```text
resistance rise (%) = (latest resistance - initial resistance) / initial resistance * 100
```

If resistance rises too much, the cell can show:

- higher heat generation
- lower power capability
- worse efficiency
- stronger aging behavior

## Output Files

After running:

```bash
python main.py
```

check:

- `results/step1_summary.csv`
- `results/step1_report.html`
- `results/step2_warnings.txt`

## What You Should Be Able To Explain

- Why SOH below 80% is often treated as an important battery health threshold.
- Why high temperature is risky for lithium-ion cells.
- Why rising internal resistance matters.
- Why coulombic efficiency should usually stay close to 100%.
