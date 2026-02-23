"""Unit tests for the smooth function using static test data."""

import os
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

TEST_DIR = Path(__file__).parent


@pytest.fixture
def measure_simple_input():
    """Provide simple measurement input data and clean up output files after test.

    Input file contains 256 intensity points following gamma=2.2 curve with small
    random noise.
    """
    # Setup: copy input file
    shutil.copy(TEST_DIR / "measurements_8bit.csv", "measure.csv")

    yield

    # Cleanup: remove both input and output files
    for f in ["measure.csv", "smooth.csv"]:
        if os.path.exists(f):
            os.remove(f)


@pytest.fixture
def measure_duplicates_input():
    """Provide duplicate measurement input data and clean up output files after test.

    Input file contains 20 unique intensities, each measured 3 times with slight
    variations.
    """
    # Setup: copy input file
    shutil.copy(TEST_DIR / "measurements_duplicates.csv", "measure.csv")

    yield

    # Cleanup: remove both input and output files
    for f in ["measure.csv", "smooth.csv"]:
        if os.path.exists(f):
            os.remove(f)


@pytest.fixture
def measure_outliers_input():
    """Provide outlier measurement input data and clean up output files after test.

    Input file contains 50 intensities with 2-3 measurements each, including outliers
    at 30% deviation.
    """
    # Setup: copy input file
    shutil.copy(TEST_DIR / "measurements_outliers.csv", "measure.csv")

    yield

    # Cleanup: remove both input and output files
    for f in ["measure.csv", "smooth.csv"]:
        if os.path.exists(f):
            os.remove(f)


def test_smooth_output_format(measure_simple_input):
    """Output CSV file structure and data validity.

    Input: 256 intensity measurements with gamma~2.2 nonlinearity and small noise
    Output: Smoothed data with 2 columns (Input, Luminance)
    Validates: Presence of required headers, no NaN values, non-negative values
    """
    subprocess.run(["hrl-util", "lut", "smooth", "-o", "0"], check=True)

    # Verify format
    with open("smooth.csv", "r") as f:
        header = f.readline().strip()

    assert "Input" in header and "Luminance" in header

    result = np.genfromtxt("smooth.csv", skip_header=1)
    assert result.shape[1] == 2
    assert not np.any(np.isnan(result))
    assert np.all(result >= 0)


def test_smooth_basic_no_smoothing(measure_simple_input):
    """Order=0 (averaging only) matches pre-computed expected values.

    Input: 256 intensity measurements with gamma~2.2 nonlinearity and small noise
    Output: Averaged measurements without kernel smoothing
    Validates: Numerical accuracy via regression against known-good output
    """
    subprocess.run(["hrl-util", "lut", "smooth", "-o", "0"], check=True)

    result = np.genfromtxt("smooth.csv", skip_header=1)
    expected = np.genfromtxt(TEST_DIR / "measurements_8bit.csv", skip_header=1)

    np.testing.assert_array_almost_equal(result, expected, decimal=10)


def test_smooth_with_kernel(measure_simple_input):
    """Order=2 kernel smoothing matches pre-computed expected values.

    Input: 100 intensity measurements with gamma~2.2 nonlinearity and small noise
    Output: Smoothed data with 2 iterations of kernel smoothing applied
    Validates: Numerical accuracy via regression against known-good output
    """
    subprocess.run(["hrl-util", "lut", "smooth", "-o", "2"], check=True)

    result = np.genfromtxt("smooth.csv", skip_header=1)
    expected = np.genfromtxt(TEST_DIR / "smoothed_measurements_kernel.csv", skip_header=1)

    np.testing.assert_array_almost_equal(result, expected, decimal=10)


def test_smooth_averages_duplicates(measure_duplicates_input):
    """Multiple measurements at same intensity are correctly averaged.

    Input: 20 unique intensities, each measured 3 times with slight variations
    Output: 20 unique intensity points with averaged luminance values
    Validates: Correct duplicate averaging and numerical accuracy
    """
    subprocess.run(["hrl-util", "lut", "smooth", "-o", "0"], check=True)

    result = np.genfromtxt("smooth.csv", skip_header=1)
    expected = np.genfromtxt(TEST_DIR / "smoothed_measurements_duplicates.csv", skip_header=1)

    np.testing.assert_array_almost_equal(result, expected, decimal=10)

    # Should have exactly 20 unique intensity points
    assert len(result) == 20


def test_smooth_filters_outliers(measure_outliers_input):
    """Outlier measurements are correctly filtered out.

    Input: 50 intensities with 2-3 measurements each, some outliers at 30% deviation
    Output: Smoothed data with outliers removed from averaging
    Validates: Correct outlier filtering and numerical accuracy
    """
    subprocess.run(["hrl-util", "lut", "smooth", "-o", "0"], check=True)

    result = np.genfromtxt("smooth.csv", skip_header=1)
    expected = np.genfromtxt(TEST_DIR / "smoothed_measurements_outliers.csv", skip_header=1)

    np.testing.assert_array_almost_equal(result, expected, decimal=10)
