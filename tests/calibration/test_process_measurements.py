"""Tests for processing photometric measurements

Combining multiple measurement tables,
removing outliers,
averaging measurements.
"""

from pathlib import Path

import numpy as np
import pytest

from hrl.calibration.measurement import average, combine, remove_outliers

TEST_DIR = Path(__file__).parent


### COMBINE ###
def test_combine_single_table():
    """Single table combined should return a map matching that table."""
    # Setup
    table = np.array([[0.0, 1.0, 1.1], [0.5, 5.0, 5.1], [1.0, 10.0, 10.1]])

    # Run
    result = combine([table])

    # Verify
    np.testing.assert_array_equal(result[0.0], [1.0, 1.1])
    np.testing.assert_array_equal(result[0.5], [5.0, 5.1])
    np.testing.assert_array_equal(result[1.0], [10.0, 10.1])


def test_combine_merges_multiple_tables():
    """Multiple tables combined should merge measurements at same intensity."""
    # Setup
    table1 = np.array([[0.0, 1.0], [0.5, 5.0]])
    table2 = np.array([[0.0, 1.1], [0.5, 5.1]])
    # Run
    result = combine([table1, table2])

    # Verify
    np.testing.assert_array_equal(result[0.0], [1.0, 1.1])
    np.testing.assert_array_equal(result[0.5], [5.0, 5.1])


def test_combine_strips_nan_measurements():
    """NaN measurements are ignored and not included in the combined map."""
    # Setup
    table = np.array([[0.5, 5.0, np.nan, 5.1]])

    # Run
    result = combine([table])

    # Verify
    assert not np.any(np.isnan(result[0.5]))
    assert len(result[0.5]) == 2


def test_combine_raises_when_all_nan():
    """If all measurements for an intensity are NaN, raise an error."""
    # Setup
    table = np.array([[0.5, np.nan]])

    # Run and Verify
    with pytest.raises(RuntimeError):
        combine([table])


### REMOVE OUTLIERS ###
def test_remove_outliers_flags_obvious_outlier():
    """Outliers that deviate by more than 20% from the median are flagged as NaN."""
    # Setup
    # 5.0 and 5.0001 are within abs_tol (0.075 cd/m²); 50.0 is far enough to be flagged
    lum_map = {0.5: np.array([5.0, 5.0001, 50.0], dtype=float)}

    # Run
    result = remove_outliers(lum_map)
    valid = result[0.5][~np.isnan(result[0.5])]

    # Verify
    assert np.all(valid < 10.0)


def test_remove_outliers_keeps_close_measurements():
    """Measurements that are close to each other are not flagged as outliers."""
    # Setup
    lum_map = {0.5: np.array([5.0, 5.05, 5.1], dtype=float)}

    # Run
    result = remove_outliers(lum_map)

    # Verify
    assert np.sum(~np.isnan(result[0.5])) == 3


def test_remove_outliers_single_measurement_per_intensity():
    """A single measurement per intensity is kept unchanged."""
    # Setup
    lum_map = {0.0: np.array([1.0]), 0.5: np.array([5.0]), 1.0: np.array([10.0])}

    # Run
    result = remove_outliers(lum_map)

    # Verify: no outliers can be flagged with only one measurement
    assert result[0.0][0] == 1.0
    assert result[0.5][0] == 5.0
    assert result[1.0][0] == 10.0


def test_remove_outliers_raises_when_all_removed():
    """If all measurements for an intensity are flagged as outliers, raise an error."""
    # Setup
    # Two measurements far apart → each is flagged as an outlier relative to the other
    lum_map = {0.5: np.array([1.0, 100.0], dtype=float)}

    # Run and Verify
    with pytest.raises(RuntimeError):
        remove_outliers(lum_map)


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
