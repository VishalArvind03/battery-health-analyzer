# Step 8: Automated Testing (Stage 1)

## What this step adds

A set of automated tests that check the math and logic of the project. Instead
of running `main.py` and reading the numbers by eye, we now have small programs
(tests) that run the functions with known inputs and confirm the outputs are
correct. They all run with a single command:

```bash
pytest
```

## Why testing matters (the simple idea)

Imagine you change one line in `metrics.py` to "improve" it. How do you know you
did not accidentally break the SOH calculation? You could re-run everything and
check by hand every time, but that is slow and easy to get wrong. A test is a
small, permanent check that says "given this input, the answer must be this."
Run `pytest` and in one second you know whether everything still works.

Analogy: tests are like a multimeter for your code. Before trusting a circuit,
you probe known points and confirm the readings. Tests probe known points in the
code and confirm the readings.

## How the tests are organised

All tests live in the `tests/` folder. Each file targets one source module:

| Test file | What it checks |
|---|---|
| `test_metrics.py` | SOH, capacity fade, coulombic efficiency, smoothing, degradation slope, missing data |
| `test_config.py` | Loading `limits.json`, default fall-back, invalid values |
| `test_validation.py` | Each engineering warning (SOH, temperature, resistance, efficiency) |
| `test_data_loader.py` | Required columns, optional columns, sorting, missing files |
| `test_nasa_importer.py` | Impedance matching helper and the real B0005 conversion |

Two support files make this possible:

- `pytest.ini` — tells pytest where the tests are and defines the `nasa` marker.
- `tests/conftest.py` — adds the `src` folder to the import path and provides
  reusable sample data (called *fixtures*) so each test stays short.

## Key testing ideas used here

**Fixture** — reusable test data. `sample_cycles` is a tiny 6-cycle battery
dataset where the numbers are chosen so the answers are obvious: discharge
capacity falls from 2.0 Ah to 1.5 Ah, so SOH falls from 100% to 75%. Any test
can ask for it just by naming it as an argument.

**`pytest.approx`** — compares floating-point numbers safely. `2.0/2.04*100` is
98.0392..., and computers cannot store that exactly, so we check "approximately
equal" instead of "exactly equal".

**`pytest.raises`** — confirms that bad input *fails on purpose*. For example, a
baseline capacity of zero must raise an error, because dividing by zero is
meaningless. The test passes when the error is correctly raised.

**`tmp_path`** — a temporary folder pytest creates for each test. We use it to
write throw-away config and CSV files so the tests never touch the real project
files.

**`skipif` marker** — the real NASA conversion test needs `B0005.mat`, which is
a large file not stored on GitHub. The test is skipped automatically if the file
is missing, so `pytest` still passes on a fresh clone.

## What is actually verified

- SOH starts at 100% and equals discharge capacity ÷ baseline × 100.
- SOH and capacity fade always add up to 100%.
- Coulombic efficiency is calculated only when charge capacity exists, and stays
  empty for NASA data (we never fake it).
- A nominal-capacity override works, and a zero baseline is rejected.
- Smoothing adds the three rolling-average columns and reduces a single spike.
- The degradation slope is negative for an aging cell, and is `None` when there
  are too few cycles to fit a line.
- Config loading reads values, fills missing keys with defaults, and rejects
  negative or non-numeric limits.
- Each warning (SOH, temperature, resistance, efficiency) triggers when its
  limit is crossed, and a "no warnings" message appears when data is clean.
- The data loader enforces required columns, adds optional ones, sorts by cycle,
  and errors clearly on a missing file.
- The NASA converter produces 168 correctly numbered cycles with the expected
  starting capacity (~1.856 Ah).

## How to run

```bash
# one-time: install the test tool
python -m pip install -r requirements-dev.txt

# run every test
pytest

# run with more detail (one line per test)
pytest -v
```

A passing run ends with a green line like `32 passed`.

## Interview soundbite

> "I added a pytest suite that checks the core calculations — SOH, capacity
> fade, coulombic efficiency, smoothing, the degradation slope, config loading,
> the warning thresholds, and the NASA data conversion. It also tests how the
> code handles missing or invalid data. The whole suite runs with one command,
> so I can refactor safely and prove the analysis is correct."
