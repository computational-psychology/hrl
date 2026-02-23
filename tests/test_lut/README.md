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

