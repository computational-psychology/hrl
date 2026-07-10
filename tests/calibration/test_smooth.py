"""Tests for the smooth pipeline (combine → remove_outliers → average → smooth)."""

from pathlib import Path

import numpy as np

from hrl.calibration.measurement import smooth

TEST_DIR = Path(__file__).parent


def test_smooth_order_zero_unchanged():
    """No smoothing (order=0) returns the input unchanged."""
    # Setup
    measurements = np.genfromtxt(TEST_DIR / "measurements_8bit.csv", skip_header=1, delimiter=",")

    # Run
    result = smooth(measurements, order=0)

    # Verify
    np.testing.assert_array_equal(result, measurements)


def test_smooth_constant_luminance_unchanged():
    """Smoothing a measurement table with constant luminance leaves it unchanged."""
    # Setup: uniform luminance (50 cd/m²) across the full intensity range
    intensities = np.linspace(0.0, 1.0, 50)
    measurements = np.column_stack([intensities, np.full(50, 50.0)])

    # Run
    result = smooth(measurements, order=3)

    # Verify
    np.testing.assert_array_almost_equal(result, measurements)


def test_smooth_shape_preserved():
    """Output has the same shape as the input."""
    # Setup
    measurements = np.genfromtxt(TEST_DIR / "measurements_8bit.csv", skip_header=1, delimiter=",")

    # Run
    result = smooth(measurements, order=2)

    # Verify
    assert result.shape == measurements.shape


def test_smooth_reduces_noise():
    """Smoothing (order=1) reduces point-to-point variance in the luminance column."""
    # Setup: realistic measurements with added noise
    measurements = np.genfromtxt(TEST_DIR / "measurements_8bit.csv", skip_header=1, delimiter=",")
    rng = np.random.default_rng(42)
    noisy = measurements.copy()
    noisy[:, 1] += rng.normal(0, 0.5, size=len(measurements))

    # Run
    result = smooth(noisy, order=1)

    # Verify
    assert np.std(np.diff(result[:, 1])) < np.std(np.diff(noisy[:, 1]))


def test_smooth_with_kernel():
    """Order=2 kernel smoothing matches pre-computed expected values.

    Input: 256 intensity measurements with gamma~2.2 nonlinearity and small noise
    Output: Smoothed data with 2 iterations of kernel smoothing applied
    Validates: Numerical accuracy via regression against known-good output
    """
    # Setup
    measurements = np.genfromtxt(TEST_DIR / "measurements_8bit.csv", skip_header=1, delimiter=",")

    # Run
    result = smooth(measurements, order=2)

    # Verify
    expected = np.genfromtxt(
        TEST_DIR / "smoothed_measurements_kernel.csv", skip_header=1, delimiter=","
    )
    np.testing.assert_array_almost_equal(result, expected, decimal=10)
