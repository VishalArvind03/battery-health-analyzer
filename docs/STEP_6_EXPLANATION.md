# Step 6 Explanation

## What We Added

Step 6 adds support for a real public NASA battery aging dataset.

The raw NASA files are MATLAB `.mat` files, so the project now includes a converter:

```text
scripts/convert_nasa_dataset.py
```

The converter reads:

```text
data/raw/nasa/B0005.mat
```

and creates:

```text
data/processed/nasa_B0005_cycles.csv
```

## Dataset Source

The dataset is from the NASA Prognostics Center of Excellence data repository.

NASA gives the battery dataset citation as:

```text
B. Saha and K. Goebel (2007). "Battery Data Set", NASA Prognostics Data Repository, NASA Ames Research Center, Moffett Field, CA
```

## Why This Matters

Before Step 6, the project used simple sample data.

Sample data is useful for learning, but it is not strong enough for a portfolio project.

Using real NASA data makes the project more credible because the analysis is based on actual battery cycling measurements.

## Important Dataset Limitation

The NASA discharge cycles provide discharge capacity directly. Charge capacity is not stored in the same simple cycle-level way, so this Step 6 converter leaves `charge_capacity_ah` empty for NASA data.

That means coulombic efficiency is available for the original sample data, but not for the converted NASA B0005 cycle-level data.

This is not a failure. It is a realistic data-engineering issue: real datasets do not always contain every column you want.

## How To Run

First convert the NASA data:

```bash
python scripts/convert_nasa_dataset.py
```

Then run the main analysis:

```bash
python main.py
```

After the NASA CSV exists, `main.py` automatically uses it by default.

To force the original sample data:

```bash
python main.py --data data/sample_battery_cycles.csv
```

## What You Should Be Able To Explain

- Why real data is more valuable than sample data.
- Why `.mat` files need a converter before normal CSV analysis.
- Why missing charge capacity prevents coulombic efficiency calculation.
- Why keeping raw data separate from processed data is a professional workflow.
