"""Tests for the complete measurement → smooth → linearize pipeline."""

from pathlib import Path

import numpy as np

from hrl.calibration.measurement import average, combine, linearize, remove_outliers, smooth

TEST_DIR = Path(__file__).parent


def test_full_pipeline():
    """Complete workflow from raw measurements through smoothing to linearized LUT.

    Input: 256 intensity measurements with gamma~2.2 nonlinearity and small random noise
    Pipeline: smooth with order=0 (averaging) → linearize at 8-bit resolution
    Validates: Final LUT matches expected values from unit tests
    """
    # Setup
    measurements = np.genfromtxt(TEST_DIR / "measurements_8bit.csv", skip_header=1, delimiter=",")

    # Step 0: combine measurements table(s) into luminance map
    lum_map = combine([measurements])

    # Step 1: remove outliers
    lum_map = remove_outliers(lum_map)

    # Step 2: average
    table = average(lum_map)

    # Step 3: smooth (optional)
    table[:, 1] = smooth(table[:, 1], order=0)

    # Step 4: linearize to create LUT
    result_lut = linearize(table, bit_depth=8)

    # Verify
    expected_lut = np.genfromtxt(TEST_DIR / "lut_8bit.csv", skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result_lut, expected_lut, decimal=10)


def test_pipeline_preserves_luminance_range():
    """Pipeline preserves original luminance range from measurements to final LUT.

    Input: 80 intensity measurements with gamma~2.0 nonlinearity, 2.5-150 cd/m² range
    Pipeline: smooth with 1 kernel iteration → linearize at 8-bit resolution
    Validates: Final LUT matches expected values and preserves min/max luminance within 5%
    """
    # Setup
    lum_min, lum_max = 2.5, 150.0
    measurements = np.genfromtxt(
        TEST_DIR / "measurements_lumrange.csv", skip_header=1, delimiter=","
    )

    # Step 0: combine measurements table(s) into luminance map
    lum_map = combine([measurements])

    # Step 1: remove outliers
    lum_map = remove_outliers(lum_map)

    # Step 2: average
    table = average(lum_map)

    # Step 3: smooth (optional)
    table[:, 1] = smooth(table[:, 1], order=1)

    # Step 4: linearize to create LUT
    result_lut = linearize(table, bit_depth=8)

    # Verify luminance range preserved within 5%
    assert np.isclose(result_lut[0, 2], lum_min, rtol=0.05)
    assert np.isclose(result_lut[-1, 2], lum_max, rtol=0.05)

    # Verify values
    expected_lut = np.genfromtxt(TEST_DIR / "lut_lumrange.csv", skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result_lut, expected_lut, decimal=10)
