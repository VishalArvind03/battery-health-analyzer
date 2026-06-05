# Step 3 Explanation

## What We Added

Step 3 improves the HTML report by adding multiple engineering plots.

The report now shows:

- SOH vs cycle
- capacity fade vs cycle
- internal resistance vs cycle
- maximum temperature vs cycle
- coulombic efficiency vs cycle

## Why This Matters

Battery engineers do not look at only one number. They look at trends.

For example:

- SOH shows how usable capacity changes.
- capacity fade shows degradation directly.
- internal resistance shows power and heat-related aging.
- temperature shows thermal stress.
- coulombic efficiency shows charge/discharge efficiency.

Looking at all of these together gives a better view of battery health.

## Important Concept: Trends

A single value can be misleading.

Example:

```text
Latest SOH = 93.52%
```

This is useful, but the trend tells more:

- Did SOH decrease slowly or suddenly?
- Did resistance rise at the same time?
- Did temperature increase during later cycles?
- Did coulombic efficiency become unstable?

In real validation work, engineers care strongly about these patterns.

## What You Should Be Able To Explain

- Why SOH and capacity fade move in opposite directions.
- Why resistance increase is a negative sign.
- Why higher temperature can accelerate degradation.
- Why coulombic efficiency should remain close to 100%.
- Why trend plots are more useful than only final numbers.
