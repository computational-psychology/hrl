# CLUT Calibration Tests

This directory contains tests for CLUT (Color Look-Up Table) processing
functions used for display color calibration and RGB-to-XYZ correction.

## Overview

Tests in this folder cover the CLUT calibration workflow end-to-end:

1. RGB triplet measurement-like input handling
2. Measurement processing (outlier removal, averaging)
3. CLUT linearization

The suite includes both unit tests and regression tests against static CSV fixtures.

## File Formats

The output CLUT files (`clut_*.csv`) adhere to the format used by `hrl.cluts`
(see `hrl.cluts`):

```
intensity_in,R_out,G_out,B_out,R_X,R_Y,R_Z,G_X,G_Y,G_Z,B_X,B_Y,B_Z
```

where:
- `intensity_in`: Input intensity values (0-1 range)
- `R_out,G_out,B_out`: Gamma-corrected output values (0-1 range)
- `R_X...B_Z`: the XYZ with only that channel on, at that input; the first row holds
  the black screen for all three channels

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