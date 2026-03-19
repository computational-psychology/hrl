"""Tests for the smooth pipeline (combine → remove_outliers → average → smooth)."""

from pathlib import Path

import numpy as np

from hrl.calibration.measurement import average, combine, remove_outliers, smooth

TEST_DIR = Path(__file__).parent


def test_smooth_order_zero_unchanged():
    """No smoothing (order=0) returns the input unchanged."""
    # Setup
    measurements = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

    # Run
    result = smooth(measurements, order=0)

    # Verify
    np.testing.assert_array_equal(result, measurements)


def test_smooth_constant_array_unchanged():
    """Smoothing a constant array leaves it unchanged."""
    # Setup
    measurements = np.ones(20)

    # Run
    result = smooth(measurements, order=3)

    # Verify
    np.testing.assert_array_almost_equal(result, measurements)


def test_smooth_length_preserved():
    """Output has the same length as the input."""
    # Setup
    measurements = np.linspace(0.0, 1.0, 50)

    # Run
    result = smooth(measurements, order=2)

    # Verify
    assert len(result) == len(measurements)


def test_smooth_with_kernel():
    """Order=2 kernel smoothing matches pre-computed expected values.

    Input: 256 intensity measurements with gamma~2.2 nonlinearity and small noise
    Output: Smoothed data with 2 iterations of kernel smoothing applied
    Validates: Numerical accuracy via regression against known-good output
    """
    # Setup
    measurements = np.genfromtxt(TEST_DIR / "measurements_8bit.csv", skip_header=1, delimiter=",")
    lum_map = combine([measurements])
    lum_map = remove_outliers(lum_map)
    table = average(lum_map)

    # Run
    result = smooth(table[:, 1], order=2)

    # Verify
    expected = np.genfromtxt(
        TEST_DIR / "smoothed_measurements_kernel.csv", skip_header=1, delimiter=","
    )[:, 1]
    np.testing.assert_array_almost_equal(result, expected, decimal=10)
