# LUT Calibration Tests

This directory contains tests for LUT (Look-Up Table) processing functions
used for monitor calibration and gamma correction.

## Overview

The LUT processing pipeline transforms raw monitor luminance measurements
into linearized look-up tables for gamma correction:

0. **Input**: Raw measurements of intensity vs. luminance (from photometer)
1. **Combine**: Merge multiple measurement sessions into a single dataset, transforming into an intensity-to-luminance map
2. **Outlier Removal**: Identify and remove outliers from the luminance map
3. **Averaging**: Average measurements at each intensity level to get a single value
4. **Smoothing**: Smooth the (average) measurements to reduce noise and create a more stable curve
5. **Linearization**: Convert smoothed data into a LUT that produces linear luminance progression

Tests use static input files and compare against pre-computed expected outputs
to ensure numerical accuracy and correct behavior across different resolutions and edge cases.
The tests cover both individual steps (smoothing and linearization) and the full pipeline integration.

## File Formats

The output LUT files (`lut_*.csv`) adhere to the format defined in `hrl.luts`:

```
intensity_in,intensity_out,luminance
```

where:
- `intensity_in`: Input intensity values (0-1 range)
- `intensity_out`: Gamma-corrected output intensity values (0-1 range)
- `luminance`: Corresponding luminance values (cd/m²)


The input measurement files (`measurements_*.csv`),
averaged measurements (`averaged_*.csv`),
and kernel-smoothed measurements (`smoothed_*.csv`)
contain intensity-luminance pairs in a version of this format:

```
intensity_in,luminance
```

## Linearization Tests (`test_linearize.py`)

The linearization routine (`hrl.calibration.measurement.linearize`)
takes measured intensity-luminance pairs from a monitor
and creates a LUT that maps input intensities to output intensities,
such that the resulting luminance progression is approximately linear.
The linearization can produce LUTs of different output resolutions,
even from the same input measurements.

### Unit tests
Using small in-memory arrays to validate basic properties of the linearization function:

- **Three-column output** (`test_linearize_output_has_three_columns`): output has columns intensity_in, intensity_out, luminance
- **Length bound** (`test_linearize_length_bounded_by_bit_depth`): number of output rows never exceeds 2**bit_depth
- **Intensity range** (`test_linearize_intensities_in_unit_range`): both intensity columns stay within [0, 1]
- **Monotonic output** (`test_linearize_output_columns_monotonic`): both intensity_out and luminance columns are non-decreasing

### Regression tests
Against pre-computed CSV files generated from known input measurements, validating:

- **Luminance linearity** (`test_linearize_luminance_linearity`): 16-bit input → monotonically increasing luminance with uniform step sizes (CV < 1.5)
- **8-bit resolution** (`test_linearize_8bit`): 8-bit measurements → 8-bit LUT (≤256 entries) matches `lut_8bit.csv`
- **16-bit resolution** (`test_linearize_16bit`): 16-bit measurements → 16-bit LUT (≤65536 entries) matches `lut_16bit.csv`
- **10-bit resolution** (`test_linearize_10bit`): 16-bit measurements → 10-bit LUT (≤1024 entries) matches `lut_10bit.csv`


## Processing measurements (`test_process_measurements.py`)

Before linearization, we often first combine several sets of raw measurements (from different measurement sessions),
remove outliers, and average them to create a cleaner dataset for linearization.
These functions are in `hrl.calibration.measurement`.

### Unit tests
Testing combine, remove_outliers, and average in isolation with small in-memory arrays:

1. **Combining sessions** (`test_combine_*`): Multiple measurement tables are merged into
   a single intensity-to-luminance map; NaN readings are dropped.
2. **Outlier removal** (`test_remove_outliers_*`): Measurements that deviate strongly from
   the median at an intensity level are excluded;
   a single measurement per intensity is always kept unchanged.
3. **Averaging** (`test_average_*`): The remaining measurements at each intensity level
   are averaged to produce a clean intensity–luminance table.

### Regression tests
Against pre-computed CSV files, validating the full combine → remove_outliers → average sequence:

- **Duplicate averaging** (`test_averaging_duplicates`): `measurements_duplicates.csv` (20 unique intensities × 3 measurements each) → combine → remove_outliers → average matches `averaged_measurements_duplicates.csv`
- **Outlier filtering** (`test_averaging_filters_outliers`): `measurements_outliers.csv` (50 intensities with ~30% outliers) → combine → remove_outliers → average matches `averaged_measurements_outliers.csv`


## Smoothing tests (`test_smooth.py`)

If the measurements are noisy, we often first smooth the data
to create a cleaner dataset for LUT generation.
This is done using the `smooth` function in `hrl.calibration.measurement`,
which applies a simple moving average kernel to the measurements,
reducing luminance differences between neighboring intensity steps.

### Unit tests
Using small in-memory arrays to validate basic properties of the smoothing function:

- **No smoothing** (`test_smooth_order_zero_unchanged`): `order=0` returns the input unchanged
- **Constant array** (`test_smooth_constant_array_unchanged`): smoothing a constant array leaves it unchanged
- **Length preserved** (`test_smooth_length_preserved`): output has the same length as the input

### Regression test
Against a pre-computed CSV file generated from known input measurements:

- **Order=2 kernel smoothing** (`test_smooth_with_kernel`): `measurements_8bit.csv` → combine → remove_outliers → average → smooth(order=2) matches `smoothed_measurements_kernel.csv`



## Regression tests of whole pipeline (`test_integration.py`)

Since the full LUT generation pipeline involves multiple steps that interact, we have integrated tests that run the entire workflow from raw measurements to final LUT,
validating the end-to-end behavior and ensuring that the final output matches expected results for known inputs.

**Full pipeline** (`test_full_pipeline`) — 8-bit (256 measurement points, gamma~2.2, 1-101 cd/m²):
```
measurements_8bit.csv → combine → remove_outliers → average → smooth(order=0) → linearize → lut_8bit.csv
```

**Luminance range preservation** (`test_pipeline_preserves_luminance_range`):
Tests the pipeline with measurements in a different luminance range
to confirm that the LUT preserves the original range.
- `measurements_lumrange.csv` (2.5–150 cd/m²) → full pipeline (8-bit) → confirms min/max within 5% of original range


## CLI tests (`test_cli.py`)

To run the LUT calibration pipeline,
the `hrl-util lut` provides corresponding commands:
- `hrl-util lut measure` to run the measurement process and generate raw measurement files,
- `hrl-util lut smooth` to combine, remove outliers, average, and smooth the measurements,
- `hrl-util lut linearize` to linearize the smoothed measurements into a LUT.

Here we test the CLI commands for smoothing and linearization, ensuring that they produce the expected output files when run with known input measurement files.
These mirror the integration tests but validate the command-line interface and file I/O.

- **Full pipeline** (`test_full_pipeline`, parametrized): smooth → linearize at 8-bit, 10-bit, and 16-bit output resolution
- **Luminance range preservation** (`test_pipeline_preserves_luminance_range`): luminance range preserved end-to-end
- **Smoothing output format** (`test_smooth_output_format`): correct CSV headers, no NaN values, non-negative luminances
- **Averaging** (`test_averaging`): `order=0` output matches averaged measurements
- **Kernel smoothing** (`test_smooth_with_kernel`): `order=2` output matches `smoothed_measurements_kernel.csv`
- **Linearization output format** (`test_linearize_output_format`): correct headers and valid intensity/luminance ranges
- **Linearization bit depths** (`test_linearize_different_bitdepths`, parametrized): 8-bit, 10-bit, 16-bit outputs match expected LUT files
- **Missing smooth input** (`test_smooth_fails_on_missing_input`): smooth command exits non-zero when `measure.csv` is absent
- **Missing linearize input** (`test_linearize_fails_on_missing_input`): linearize command exits non-zero when `smooth.csv` is absent

## Regenerating Test Data

Run `generate_test_data.py` to regenerate all test data files:
```bash
cd tests/calibration
uv run python generate_test_data.py
```

This will create all measurement files,
run the smooth and linearize commands,
and generate all expected output files.
