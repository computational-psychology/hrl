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
def test_average_returns_two_column_table():
    """Output is a 2-column table of intensity and mean luminance."""
    # Setup
    lum_map = {0.0: np.array([1.0, 1.2]), 1.0: np.array([10.0, 10.4])}

    # Run
    result = average(lum_map)

    # Verify
    assert result.shape == (2, 2)


def test_average_computes_mean():
    """Average computes the mean of measurements at each intensity."""
    # Setup
    lum_map = {0.5: np.array([10.0, 20.0])}

    # Run
    result = average(lum_map)

    # Verify
    np.testing.assert_almost_equal(result[0, 1], 15.0)


def test_average_sorts_by_intensity():
    """Output table is sorted by intensity in ascending order."""
    # Setup
    lum_map = {0.5: np.array([5.0]), 0.0: np.array([1.0]), 1.0: np.array([10.0])}

    # Run
    result = average(lum_map)

    # Verify
    np.testing.assert_array_equal(result[:, 0], np.sort(result[:, 0]))


def test_average_ignores_nan():
    """NaN measurements are ignored when computing the average."""
    # Setup
    lum_map = {0.5: np.array([5.0, np.nan, 5.2])}

    # Run
    result = average(lum_map)

    # Verify
    np.testing.assert_almost_equal(result[0, 1], 5.1)


### INTEGRATED REGRESSION TESTS ###
def test_averaging_duplicates():
    """Multiple measurements at same intensity are correctly averaged.

    Input: 20 unique intensities, each measured 3 times with slight variations
    Output: 20 unique intensity points with averaged luminance values
    Validates: Correct duplicate averaging and numerical accuracy
    """
    # Setup
    measurements = np.genfromtxt(
        TEST_DIR / "measurements_duplicates.csv", skip_header=1, delimiter=","
    )
    lum_map = combine([measurements])
    lum_map = remove_outliers(lum_map)

    # Run
    result = average(lum_map)

    # Verify
    assert len(result) == 20
    expected = np.genfromtxt(
        TEST_DIR / "averaged_measurements_duplicates.csv", skip_header=1, delimiter=","
    )
    np.testing.assert_array_almost_equal(result, expected, decimal=10)


def test_averaging_filters_outliers():
    """Outlier measurements are correctly filtered out.

    Input: 50 intensities with 2-3 measurements each, some outliers at 30% deviation
    Output: Averaged data with outliers removed from averaging
    Validates: Correct outlier filtering and numerical accuracy
    """
    # Setup
    measurements = np.genfromtxt(
        TEST_DIR / "measurements_outliers.csv", skip_header=1, delimiter=","
    )
    lum_map = combine([measurements])

    # Run
    lum_map = remove_outliers(lum_map)
    result = average(lum_map)

    # Verify
    expected = np.genfromtxt(
        TEST_DIR / "averaged_measurements_outliers.csv", skip_header=1, delimiter=","
    )
    np.testing.assert_array_almost_equal(result, expected, decimal=10)
