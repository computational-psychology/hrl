"""Tests for the linearize function using hrl.calibration.measurement."""

from pathlib import Path

import numpy as np

from hrl.calibration.measurement import linearize

TEST_DIR = Path(__file__).parent


### UNIT TESTS
def test_linearize_output_has_three_columns():
    """Output table has three columns (intensity_in, intensity_out, luminance)."""
    measurements = np.column_stack([np.linspace(0, 1, 100), np.linspace(1.0, 100.0, 100)])
    assert linearize(measurements, bit_depth=4).shape[1] == 3


def test_linearize_length_bounded_by_bit_depth():
    """Number of output rows never exceeds 2**bit_depth."""
    measurements = np.column_stack([np.linspace(0, 1, 100), np.linspace(1.0, 100.0, 100)])
    assert len(linearize(measurements, bit_depth=4)) <= 2**4


def test_linearize_intensities_in_unit_range():
    """Both intensity columns stay within [0, 1]."""
    measurements = np.genfromtxt(TEST_DIR / "measurements_8bit.csv", skip_header=1, delimiter=",")
    result = linearize(measurements, bit_depth=8)
    assert np.all(result[:, 0] >= 0) and np.all(result[:, 0] <= 1)
    assert np.all(result[:, 1] >= 0) and np.all(result[:, 1] <= 1)


def test_linearize_output_columns_monotonic():
    """Both intensity_out and luminance columns in the output are non-decreasing."""
    # Setup
    measurements = np.column_stack([np.linspace(0, 1, 100), np.linspace(1.0, 100.0, 100)])

    # Run
    result = linearize(measurements, bit_depth=8)

    # Verify
    assert np.all(np.diff(result[:, 1]) >= 0)  # intensity_out
    assert np.all(np.diff(result[:, 2]) >= 0)  # luminance


### REGRESSION TESTS ###
def test_linearize_luminance_linearity():
    """Resulting luminance values increase in approximately uniform steps.

    Input: 65536 intensity-luminance measurement pairs (gamma~2.2, 1-101 cd/m²)
    Output: 16-bit LUT mapping intensities to produce linear luminance progression
    Validates: Monotonic luminance increase with low step-size variability (CV < 1.5)
    """
    # Setup
    measurements = np.genfromtxt(TEST_DIR / "measurements_16bit.csv", skip_header=1, delimiter=",")

    # Run
    result = linearize(measurements, bit_depth=16)
    luminances = result[:, 2]

    # Verify monotonicity
    assert np.all(np.diff(luminances) >= 0)

    # Verify step size reasonable uniformity
    lum_diffs = np.diff(luminances)
    non_zero_diffs = lum_diffs[lum_diffs > 1e-6]
    if len(non_zero_diffs) > 10:
        cv = np.std(non_zero_diffs) / np.mean(non_zero_diffs)
        assert cv < 1.5


def test_linearize_16bit():
    """16-bit resolution LUT matches pre-computed expected values.

    Input: 65536 intensity-luminance measurement pairs (gamma~2.2, 1-101 cd/m²)
    Output: Up to 2^16 LUT entries mapping intensities for linear luminance progression
    Validates: Numerical accuracy via regression against known-good output
    """
    # Setup
    measurements = np.genfromtxt(TEST_DIR / "measurements_16bit.csv", skip_header=1, delimiter=",")

    # Run
    result = linearize(measurements, bit_depth=16)

    # Verify
    expected = np.genfromtxt(TEST_DIR / "lut_16bit.csv", skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result, expected, decimal=10)


def test_linearize_8bit():
    """8-bit resolution LUT has ≤256 entries and matches expected values.

    Input: 256 intensity-luminance measurement pairs (gamma~2.2, 1-101 cd/m²)
    Output: ≤256 LUT entries mapping intensities for linear luminance progression
    Validates: Numerical accuracy and compliance with 8-bit length constraint
    """
    # Setup
    measurements = np.genfromtxt(TEST_DIR / "measurements_8bit.csv", skip_header=1, delimiter=",")

    # Run
    result = linearize(measurements, bit_depth=8)

    # Verify
    assert len(result) <= 2**8
    expected = np.genfromtxt(TEST_DIR / "lut_8bit.csv", skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result, expected, decimal=10)


def test_linearize_10bit():
    """10-bit resolution LUT has ≤1024 entries and matches expected values.

    Input: 65536 intensity-luminance measurement pairs (gamma~2.2, 1-101 cd/m²)
    Output: ≤1024 LUT entries mapping intensities for linear luminance progression
    Validates: Numerical accuracy and compliance with 10-bit length constraint
    """
    # Setup
    measurements = np.genfromtxt(TEST_DIR / "measurements_16bit.csv", skip_header=1, delimiter=",")

    # Run
    result = linearize(measurements, bit_depth=10)

    # Verify
    assert len(result) <= 2**10
    expected = np.genfromtxt(TEST_DIR / "lut_10bit.csv", skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result, expected, decimal=10)
