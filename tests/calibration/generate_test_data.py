#!/usr/bin/env python
"""Generate test data files for LUT processing tests.

All data is derived from hrl.luts.create_lut + MockPhotometer, so every fixture
is fully reproducible (seeded where noise is involved).

This script creates data files for testing the LUT processing pipeline, in order:

1. Ground-truth LUTs   - lut_8bit.csv, lut_16bit.csv: linearized LUTs with 256
                         and 65 536 points respectively, luminance range
                         1-101 cd/m². Saved directly from create_lut (i.e. they
                         ARE the create_lut output, not derived from a pipeline).
2. Measurement files   - noiseless mock measurements of those two LUTs.
3. Measurement variants- measurements with duplicates and with outliers, both
                         based on the 8-bit LUT, to test averaging/outlier logic.
4. Derived outputs     - fixtures produced by actually running the
                         combine/remove_outliers/average/smooth/linearize
                         pipeline: smoothed_measurements_kernel.csv and
                         lut_10bit.csv (compressed from the 16-bit measurements).
5. Different luminance range - lut_lumrange.csv: same create_lut relationship
                         as above, but a wider luminance range (2.5-150 cd/m²),
                         run through the full pipeline (incl. smoothing) rather
                         than saved directly.
"""

import types
from pathlib import Path

import numpy as np

from hrl.calibration.measurement import (
    average,
    combine,
    linearize,
    measure_lut,
    remove_outliers,
    smooth,
)
from hrl.luts import create_lut
from hrl.photometer.mock import MockPhotometer

TEST_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ihrl(lut, noise=0.0, rng=None):
    """Minimal mock HRL stand-in with a MockPhotometer."""
    ihrl = types.SimpleNamespace()
    ihrl.photometer = MockPhotometer(luminance_mapping=lut, noise=noise, rng=rng)
    ihrl.inputs = None
    return ihrl


def _draw(ihrl, intensity):
    """Stimulus "draw" stand-in: just records the intensity for the mock photometer."""
    ihrl.photometer.current_intensity = intensity


# ---------------------------------------------------------------------------
# 1. Ground-truth LUTs (saved directly from create_lut)
# ---------------------------------------------------------------------------

LUT_8BIT = create_lut(n=256, gamma=2.2, k=100.0, dark=1.0)
LUT_16BIT = create_lut(n=65536, gamma=2.2, k=100.0, dark=1.0)

print("Saving ground-truth LUTs ...")
np.savetxt(
    TEST_DIR / "lut_8bit.csv",
    LUT_8BIT,
    header="intensity_in,intensity_out,luminance",
    delimiter=",",
    comments="",
    fmt="%.18e",
)
np.savetxt(
    TEST_DIR / "lut_16bit.csv",
    LUT_16BIT,
    header="intensity_in,intensity_out,luminance",
    delimiter=",",
    comments="",
    fmt="%.18e",
)

# ---------------------------------------------------------------------------
# 2. Measurement files (noiseless mock measurements of the ground-truth LUTs)
# ---------------------------------------------------------------------------

# measurements_8bit.csv: single noiseless sample per intensity, measured at LUT_8BIT's
# intensity_out values (256 points). Noiseless so linearize() reproduces lut_8bit.csv exactly.
print("Generating measurements_8bit.csv ...")
ihrl = _make_ihrl(LUT_8BIT, noise=0.0)
measurements_8bit = measure_lut(
    ihrl, intensities=LUT_8BIT[:, 1], stim_draw_func=_draw, n_samples=1
)
np.savetxt(
    TEST_DIR / "measurements_8bit.csv",
    measurements_8bit,
    header="intensity,luminance0",
    delimiter=",",
    comments="",
    fmt="%.18e",
)

# measurements_16bit.csv: same idea as measurements_8bit.csv, but for LUT_16BIT (65 536 points).
print("Generating measurements_16bit.csv ...")
ihrl = _make_ihrl(LUT_16BIT, noise=0.0)
measurements_16bit = measure_lut(
    ihrl, intensities=LUT_16BIT[:, 1], stim_draw_func=_draw, n_samples=1
)
np.savetxt(
    TEST_DIR / "measurements_16bit.csv",
    measurements_16bit,
    header="intensity,luminance0",
    delimiter=",",
    comments="",
    fmt="%.18e",
)

# ---------------------------------------------------------------------------
# 3. Measurement variants: duplicates and outliers (both based on LUT_8BIT)
# ---------------------------------------------------------------------------
# These feed test_process_measurements.py's averaging / outlier-removal tests.

# measurements_duplicates.csv: 256 intensities x 3 samples each, noise=0.01 cd/m²
# (below abs_tol=0.075), so every sample survives remove_outliers — this file
# exercises pure averaging logic.
print("Generating measurements with duplicates ...")
ihrl = _make_ihrl(LUT_8BIT, noise=0.01, rng=42)
measurements_duplicates = measure_lut(
    ihrl, intensities=LUT_8BIT[:, 1], stim_draw_func=_draw, n_samples=3
)
np.savetxt(
    TEST_DIR / "measurements_duplicates.csv",
    measurements_duplicates,
    header="intensity,luminance0,luminance1,luminance2",
    delimiter=",",
    comments="",
    fmt="%.18e",
)

# averaged_measurements_duplicates.csv: expected output of combine → remove_outliers → average.
map_duplicates = combine([measurements_duplicates])
map_duplicates = remove_outliers(map_duplicates)
map_duplicates = average(map_duplicates)
np.savetxt(
    TEST_DIR / "averaged_measurements_duplicates.csv",
    map_duplicates,
    header="intensity,luminance",
    delimiter=",",
    comments="",
    fmt="%.18e",
)

# measurements_outliers.csv: 256 intensities x 3 samples each; every 5th intensity
# has one sample bumped by 30 %. Baseline noise=0.005 cd/m² stays below abs_tol=0.075
# (never flagged), while the 30 % spike exceeds both abs_tol and rel_tol=0.0075.
print("Generating measurements with outliers ...")
ihrl = _make_ihrl(LUT_8BIT, noise=0.005, rng=42)
measurements_outliers = measure_lut(
    ihrl, intensities=LUT_8BIT[:, 1], stim_draw_func=_draw, n_samples=3
)
for i in range(0, len(measurements_outliers), 5):
    measurements_outliers[i, 1] *= 1.30
np.savetxt(
    TEST_DIR / "measurements_outliers.csv",
    measurements_outliers,
    header="intensity,luminance0,luminance1,luminance2",
    delimiter=",",
    comments="",
    fmt="%.18e",
)

# averaged_measurements_outliers.csv: expected output of combine → remove_outliers → average.
map_outliers = combine([measurements_outliers])
map_outliers = remove_outliers(map_outliers)
map_outliers = average(map_outliers)
np.savetxt(
    TEST_DIR / "averaged_measurements_outliers.csv",
    map_outliers,
    header="intensity,luminance",
    delimiter=",",
    comments="",
    fmt="%.18e",
)

# ---------------------------------------------------------------------------
# 4. Derived outputs (produced by actually running the processing pipeline)
# ---------------------------------------------------------------------------

# smoothed_measurements_kernel.csv: expected output of
# combine → remove_outliers → average → smooth(order=2), starting from measurements_8bit.csv.
map_8bit = combine([measurements_8bit])
map_8bit = remove_outliers(map_8bit)
table = average(map_8bit)
table[:, 1] = smooth(table[:, 1], order=2)
np.savetxt(
    TEST_DIR / "smoothed_measurements_kernel.csv",
    table,
    header="intensity,luminance",
    delimiter=",",
    comments="",
    fmt="%.18e",
)

# lut_10bit.csv: measurements_16bit.csv (65 536 points) linearized down to 10-bit
# resolution (≤ 1024 entries). Not a direct create_lut output — the entries are
# selected from the 65 536-point grid, same as the real calibration workflow would do.
map_16bit = combine([measurements_16bit])
map_16bit = remove_outliers(map_16bit)
map_16bit = average(map_16bit)
lut_10bit = linearize(map_16bit, bit_depth=10)
np.savetxt(
    TEST_DIR / "lut_10bit.csv",
    lut_10bit,
    header="intensity_in,intensity_out,luminance",
    delimiter=",",
    comments="",
    fmt="%.18e",
)


# ---------------------------------------------------------------------------
# 5. Different luminance range (lut_lumrange.csv)
# ---------------------------------------------------------------------------
# Same create_lut relationship as LUT_8BIT/LUT_16BIT, just a wider luminance range
# (2.5-150 cd/m² instead of 1-101 cd/m²), run through the full pipeline including
# smoothing — this is what test_pipeline_preserves_luminance_range exercises.
#
# create_lut's luminance column is always linear in index (needed for the exact
# 8/16-bit round-trip via linearize). Since average() sorts by intensity, and any
# valid gamma curve is monotonic in index, smooth(order=1)'s edge deviation only
# depends on k/(n-1), regardless of which column is treated as "intensity".
# test_pipeline_preserves_luminance_range requires that deviation stay under 5%
# of lum_min=2.5; at n=256 it would be ~14%, so a denser grid (n=1024) is used
# here to keep it under ~3.5%.
LUT_LUMRANGE = create_lut(n=1024, gamma=2.0, k=147.5, dark=2.5)

# measurements_lumrange.csv: single noiseless sample per intensity, measured at
# LUT_LUMRANGE's intensity_out values (1024 points).
print("Generating measurements_lumrange.csv ...")
ihrl = _make_ihrl(LUT_LUMRANGE, noise=0.0)
measurements_lumrange = measure_lut(
    ihrl, intensities=LUT_LUMRANGE[:, 1], stim_draw_func=_draw, n_samples=1
)
np.savetxt(
    TEST_DIR / "measurements_lumrange.csv",
    measurements_lumrange,
    header="intensity,luminance0",
    delimiter=",",
    comments="",
    fmt="%.18e",
)

# lut_lumrange.csv: expected output of
# combine → remove_outliers → average → smooth(order=1) → linearize(bit_depth=8).
map_lumrange = combine([measurements_lumrange])
map_lumrange = remove_outliers(map_lumrange)
lut_lumrange = average(map_lumrange)
lut_lumrange[:, 1] = smooth(lut_lumrange[:, 1], order=1)
lut_lumrange = linearize(lut_lumrange, bit_depth=8)
np.savetxt(
    TEST_DIR / "lut_lumrange.csv",
    lut_lumrange,
    header="intensity_in,intensity_out,luminance",
    delimiter=",",
    comments="",
    fmt="%.18e",
)
