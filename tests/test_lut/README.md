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
