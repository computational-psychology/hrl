"""Tests for processing photometric measurements

Combining multiple measurement tables,
removing outliers,
averaging measurements.
"""

from pathlib import Path

import numpy as np
import pytest

from hrl.calibration.measurement import average, remove_outliers

TEST_DIR = Path(__file__).parent


### REMOVE OUTLIERS ###
@pytest.mark.parametrize("measurements_file", ["measurements_8bit.csv", "measurements_16bit.csv"])
def test_remove_outliers_flags_obvious_outlier(measurements_file):
    """Outliers that deviate by more than 30% from the others are flagged as NaN."""
    # Setup
    measurements = np.genfromtxt(TEST_DIR / measurements_file, skip_header=1, delimiter=",")

    # Add a close duplicate + a 30% outlier for every 10th intensity.
    # The two close measurements protect each other; the spike exceeds both abs_tol and rel_tol.
    close_rows = measurements[::10].copy()
    close_rows[:, 1] += 0.001  # well within abs_tol=0.075

    outlier_rows = measurements[::10].copy()
    outlier_rows[:, 1] *= 1.30  # 30% spike → exceeds both thresholds

    measurements_with_outliers = np.vstack([measurements, close_rows, outlier_rows])

    # Run
    result = remove_outliers(measurements_with_outliers)

    # Verify: exactly the outlier rows are NaN, everything else is intact
    assert np.sum(np.isnan(result[:, 1])) == len(outlier_rows)
    assert np.sum(~np.isnan(result[:, 1])) == len(measurements) + len(close_rows)


@pytest.mark.parametrize(
    "measurements_file",
    ["measurements_8bit.csv", "measurements_16bit.csv", "measurements_duplicates.csv"],
)
def test_remove_outliers_keeps_close_measurements(measurements_file):
    """Measurements within tolerance of each other are not flagged as outliers."""
    # Setup
    measurements = np.genfromtxt(TEST_DIR / measurements_file, skip_header=1, delimiter=",")

    # Add a close duplicate for every 10th intensity (diff=0.001 < abs_tol=0.075 → safe)
    close_rows = measurements[::10].copy()
    close_rows[:, 1] += 0.001

    measurements_with_close = np.vstack([measurements, close_rows])

    # Run
    result = remove_outliers(measurements_with_close)

    # Verify: no measurement was flagged as an outlier
    assert not np.any(np.isnan(result[:, 1]))


@pytest.mark.parametrize("measurements_file", ["measurements_8bit.csv", "measurements_16bit.csv"])
def test_remove_outliers_no_ops(measurements_file):
    """Remove outliers of single measurement per intensity, is  unchanged."""
    # Setup
    measurements = np.genfromtxt(TEST_DIR / measurements_file, skip_header=1, delimiter=",")

    # Run
    result = remove_outliers(measurements)

    # Verify
    np.testing.assert_array_equal(result, measurements)


### AVERAGE ###
@pytest.mark.parametrize("measurements_file", ["measurements_8bit.csv", "measurements_16bit.csv"])
def test_average(measurements_file):
    """Average computes the mean of measurements at each intensity."""
    # Setup
    measurements = np.genfromtxt(TEST_DIR / measurements_file, skip_header=1, delimiter=",")

    # Duplicate measurements with noise to simulate multiple measurements per intensity
    measurements_wide = np.column_stack([measurements[:, 1]] * 3)
    measurements_wide[:, 1] += np.random.normal(0, 0.1, measurements.shape[0])
    measurements_wide[:, 2] += np.random.normal(0, 0.1, measurements.shape[0])

    # Convert to long format for averaging
    measurements_long = measurements_wide.flatten()
    measurements_long = np.column_stack((np.repeat(measurements[:, 0], 3), measurements_long))

    # Run
    result = average(measurements_long)

    # Verify
    expected = np.mean(measurements_wide, axis=1)
    expected = np.column_stack((measurements[:, 0], expected))
    np.testing.assert_array_almost_equal(result, expected, decimal=10)


@pytest.mark.parametrize("measurements_file", ["measurements_8bit.csv", "measurements_16bit.csv"])
def test_average_no_ops(measurements_file):
    """Average of a single measurement per intensity level, is unchanged."""
    # Setup
    measurements = np.genfromtxt(TEST_DIR / measurements_file, skip_header=1, delimiter=",")

    # Run
    result = average(measurements)

    # Verify
    np.testing.assert_array_equal(result, measurements)


@pytest.mark.parametrize("measurements_file", ["measurements_8bit.csv", "measurements_16bit.csv"])
def test_average_ignores_nan(measurements_file):
    """NaN measurements are ignored when computing the average."""
    # Setup
    measurements = np.genfromtxt(TEST_DIR / measurements_file, skip_header=1, delimiter=",")

    # Add additional NaN measurements for some intensities
    measurements_with_nan = measurements.copy()
    measurements_with_nan[::10, 1] = np.nan  # Every 10th measurement is NaN
    measurements_with_nan = np.vstack(
        [measurements, measurements_with_nan[::10]]
    )  # Duplicate some rows with NaN

    # Run
    result = average(measurements_with_nan)

    # Verify
    np.testing.assert_array_equal(result, measurements)


def test_averaging_duplicates():
    """Multiple measurements at same intensity are correctly averaged.

    Input: 256 unique intensities, each measured 3 times with slight variations
    Output: 256 unique intensity points with averaged luminance values
    Validates: Correct duplicate averaging and numerical accuracy
    """
    # Setup
    measurements = np.genfromtxt(
        TEST_DIR / "measurements_duplicates.csv", skip_header=1, delimiter=","
    )

    # Run
    result = average(measurements)

    # Verify
    assert len(result) == 256
    expected = np.genfromtxt(
        TEST_DIR / "averaged_measurements_duplicates.csv", skip_header=1, delimiter=","
    )
    np.testing.assert_array_almost_equal(result, expected, decimal=10)


def test_averaging_filters_outliers():
    """Outlier measurements are correctly filtered out.

    Input: 256 intensities with 3 measurements each, every 5th has a 30% outlier
    Output: Averaged data with outliers removed from averaging
    Validates: Correct outlier filtering and numerical accuracy
    """
    # Setup
    measurements = np.genfromtxt(
        TEST_DIR / "measurements_outliers.csv", skip_header=1, delimiter=","
    )

    # Run
    measurements = remove_outliers(measurements)
    result = average(measurements)

    # Verify
    expected = np.genfromtxt(
        TEST_DIR / "averaged_measurements_outliers.csv", skip_header=1, delimiter=","
    )
    np.testing.assert_array_almost_equal(result, expected, decimal=10)
