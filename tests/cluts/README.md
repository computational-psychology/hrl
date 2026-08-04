# CLUT Calibration Tests

This directory contains tests for CLUT (Color Look-Up Table) processing
functions used for display color calibration and RGB-to-XYZ correction.

## Overview

Tests in this folder cover the CLUT calibration workflow end-to-end:

1. RGB triplet measurement-like input handling
2. Measurement processing (outlier removal, averaging)
3. CLUT linearization
4. Integration behavior and fixture drift guard

The suite includes both unit tests and regression tests against static CSV fixtures.

## File Formats

The output CLUT files (`clut_*.csv`) adhere to the format used by `hrl.cluts`:

```
intensity_in,R_out,G_out,B_out,X_R,X_G,X_B,Y_R,Y_G,Y_B,Z_R,Z_G,Z_B
```

where:
- `intensity_in`: Input intensity values (0-1 range)
- `R_out,G_out,B_out`: Gamma-corrected output values (0-1 range)
- `X_R...Z_B`: Flattened 3x3 color matrix columns for RGB->XYZ conversion

Measurement and processed fixtures (`measurements_*.csv`, `averaged_*.csv`) use:

```
R,G,B,X,Y,Z
```

where:
- `R,G,B`: Channel-isolated measured input triplets
- `X,Y,Z`: Corresponding CIE tristimulus values

## Fixture Files

The key fixture groups are:

- `measurements_*.csv`: raw/simulated measurement inputs
- `averaged_*.csv`: expected intermediate processing outputs
- `clut_*.csv`: expected CLUT outputs at different resolutions

Coverage includes core `hrl.cluts` operations, CSV fixture-based regressions,
end-to-end pipeline checks, and fixture drift checks.

CLUT calibration CLI tests are not included yet.

## Fixture Maintenance

Use `tests/cluts/generate_test_data.py` to regenerate all CLUT fixture files.

Use the `--check` option of `tests/cluts/generate_test_data.py` to verify that
committed fixture files are up to date without rewriting files.

This exits non-zero when any fixture differs from generated output.
