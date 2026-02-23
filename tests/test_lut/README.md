# LUT Processing Tests

This directory contains tests for LUT (Look-Up Table) processing functions
used for monitor calibration and gamma correction.

## Overview

The LUT processing pipeline transforms raw monitor luminance measurements into linearized look-up tables for gamma correction:

1. **Smoothing**: Process raw measurements to remove noise and handle duplicates/outliers
2. **Linearization**: Convert smoothed data into a LUT that produces linear luminance progression

Tests use static input files and compare against pre-computed expected outputs
to ensure numerical accuracy and correct behavior across different resolutions and edge cases.
The tests cover both individual steps (smoothing and linearization) and the full pipeline integration.

## File Formats

The output LUT files (`lut_*.csv`) adhere to the format defined in `hrl.luts`:

```
IntensityIn,IntensityOut,Luminance
<intensity_in>,<intensity_out>,<luminance>
...
```

where:
- `IntensityIn`: Input intensity values (0-1 range)
- `IntensityOut`: Gamma-corrected output intensity values (0-1 range)
- `Luminance`: Corresponding luminance values (cd/m²)


The input measurement files (`measurements_*.csv`)
as well as the smoothed measurements (`smoothed_*.csv`)
contain raw intensity-luminance measurement pairs
in a version of this format as well:

```
IntensityIn,Luminance
<intensity_value>,<luminance_value>
...
```



## Linearization Tests (`test_linearize.py`)

The `hrl-util lut linearize` command takes measured intensity-luminance pairs from a monitor
and creates a LUT that maps input intensities to output intensities,
such that the resulting luminance progression is approximately linear.
The linearization can produce LUTs of different output resolutions,
even from the same input measurements.

### Test Cases

1. **Output format** (`test_linearize_output_format`): Validates CSV structure with required headers (IntensityIn, IntensityOut, Luminance), valid data ranges (0-1 for intensities)
2. **Luminance linearity** (`test_linearize_luminance_linearity`): Verifies output produces approximately uniform luminance increments (CV < 1.5)
3. **8-bit resolution** (`test_linearize_8bit`): Tests 8-bit measurements linearized to an 8-bit (≤256 entries) LUT. Tests against known `lut_8bit.csv`.
4. **16-bit resolution** (`test_linearize_16bit`): Tests 16-bit measurements linearized to an 16-bit (≤65536 entries) LUT. Tests against known `lut_16bit.csv`.
5. **10-bit resolution** (`test_linearize_10bit`): Tests 16-bit measurements linearized to a 10-bit (≤1024 entries) LUT. Tests against known `lut_10bit.csv`.



## Smoothing tests (`test_smooth.py`)

Before linearization, we often first combine several sets of raw measurements,
remove outliers, and smooth the data
to create a cleaner dataset for LUT generation.
The `hrl-util lut smooth` command processes raw monitor luminance measurements to remove noise,
average duplicate measurements, filter outliers, and optionally apply kernel smoothing.

### Test Cases

This test suite validates:

1. **Output format** (`test_smooth_output_format`): Validates CSV structure with required headers (Input, Luminance), no NaN values, non-negative values
2. **Basic averaging (no smoothing)** (`test_smooth_basic_no_smoothing`): Tests basic averaging, without smoothing
    `measurements_8bit.csv` → `smoothed_measurements_8bit.csv`
4. **Duplicate averaging** (`test_smooth_averages_duplicates`): Verifies multiple measurements at same intensity are correctly averaged.
   `measurements_duplicates.csv` (20 unique intensities × 3 measurements each)
    → `smoothed_measurements_duplicates.csv`
5. **Outlier filtering** (`test_smooth_filters_outliers`): Confirms outlier measurements are correctly excluded
    measurements_outliers.csv` (50 intensities with 2-3 measurements, some 30% outliers)
    → `smoothed_measurements_outliers.csv`
3. **Order=2 kernel smoothing** (`test_smooth_with_kernel`): Tests kernel smoothing iterations 
    `measurements_8bit.csv` with `order=2`
    → `smoothed_measurements_kernel.csv`



## Core tests of whole pipeline (`test_integration.py`)

**Full pipeline** (`test_full_pipeline`):
Full pipeline tests that verify the complete workflow from raw measurements to final LUT.

**8-bit pipeline** (256 measurement points, gamma~2.2, 1-101 cd/m²):
```
measurements_8bit.csv → smoothed_measurements_8bit.csv → lut_8bit.csv (8-bit resolution)
```

**16-bit pipeline** (65536 measurement points, gamma~2.2, 1-101 cd/m²):
```
measurements_16bit.csv → smoothed_measurements_16bit.csv → lut_10bit.csv (10-bit resolution)
                                                          → lut_16bit.csv (16-bit resolution)
```

**Luminance range preservation** (`test_pipeline_preserves_luminance_range`):
Additionally, we test the pipeline with a measurements in a different luminance range,
to ensure that the pipeline correctly handles different input ranges
and produces LUTs that preserve the original luminance range.
- `measurements_lumrange.csv` (2.5-150 cd/m²) → smooth (order=1) → linearize (8-bit) → `lut_lumrange.csv`
- Confirms final LUT min/max luminance within 10% of original range
