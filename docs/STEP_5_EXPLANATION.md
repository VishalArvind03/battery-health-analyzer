# Step 5 Explanation

## What We Added

Step 5 moves engineering warning limits into a JSON configuration file.

The config file is:

```text
config/limits.json
```

It contains:

```json
{
  "soh_limit_percent": 80.0,
  "temperature_limit_c": 45.0,
  "resistance_rise_limit_percent": 20.0,
  "coulombic_efficiency_limit_percent": 98.0
}
```

## Why This Matters

Before Step 5, the warning limits were inside Python code.

That works, but it is not ideal. In real engineering teams, limits may change depending on:

- test plan
- cell chemistry
- customer requirement
- safety rule
- company validation standard
- project phase

A config file lets engineers change limits without editing the code logic.

## Important Concept: Configuration

Configuration means values that control how the program behaves.

Code should describe the logic.

Config should describe adjustable project settings.

In this project:

- Python code calculates and checks battery metrics.
- `limits.json` stores the warning thresholds.

## What You Should Be Able To Explain

- What a JSON file is.
- Why limits are better in a config file than hard-coded in a function.
- How changing `limits.json` changes the warning output.
- Why config files are common in company software projects.
