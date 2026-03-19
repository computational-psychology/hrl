"""Unit tests for the smooth function using static test data."""

import shutil
import subprocess
from pathlib import Path

import numpy as np

TEST_DIR = Path(__file__).parent


def test_smooth_output_format(tmp_path):
    """Output CSV file structure and data validity.

    Input: 256 intensity measurements with gamma~2.2 nonlinearity and small noise
    Output: Smoothed data with 2 columns (intensity_in, luminance)
    Validates: Presence of required headers, no NaN values, non-negative values
    """
    # Setup
    shutil.copy(TEST_DIR / "measurements_8bit.csv", tmp_path / "measure.csv")

    # Run
    subprocess.run(["hrl-util", "lut", "smooth", "--order", "0"], check=True, cwd=tmp_path)
    header = (tmp_path / "smooth.csv").read_text().splitlines()[0]
    result = np.genfromtxt(tmp_path / "smooth.csv", skip_header=1, delimiter=",")

    # Verify format
    assert "intensity_in" in header and "luminance" in header
    assert result.shape[1] == 2

    # Verify values
    assert not np.any(np.isnan(result))
    assert np.all(result >= 0)


def test_smooth_basic_no_smoothing(tmp_path):
    """Order=0 (averaging only) matches pre-computed expected values.

    Input: 256 intensity measurements with gamma~2.2 nonlinearity and small noise
    Output: Averaged measurements without kernel smoothing
    Validates: Numerical accuracy via regression against known-good output
    """
    # Setup
    shutil.copy(TEST_DIR / "measurements_8bit.csv", tmp_path / "measure.csv")

    # Run
    subprocess.run(["hrl-util", "lut", "smooth", "--order", "0"], check=True, cwd=tmp_path)
    result = np.genfromtxt(tmp_path / "smooth.csv", skip_header=1, delimiter=",")

    # Verify
    expected = np.genfromtxt(TEST_DIR / "measurements_8bit.csv", skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result, expected, decimal=10)


def test_smooth_with_kernel(tmp_path):
    """Order=2 kernel smoothing matches pre-computed expected values.

    Input: 100 intensity measurements with gamma~2.2 nonlinearity and small noise
    Output: Smoothed data with 2 iterations of kernel smoothing applied
    Validates: Numerical accuracy via regression against known-good output
    """
    # Setup
    shutil.copy(TEST_DIR / "measurements_8bit.csv", tmp_path / "measure.csv")

    # Run
    subprocess.run(["hrl-util", "lut", "smooth", "--order", "2"], check=True, cwd=tmp_path)
    result = np.genfromtxt(tmp_path / "smooth.csv", skip_header=1, delimiter=",")

    # Verify
    expected = np.genfromtxt(
        TEST_DIR / "smoothed_measurements_kernel.csv", skip_header=1, delimiter=","
    )
    np.testing.assert_array_almost_equal(result, expected, decimal=10)


def test_smooth_averages_duplicates(tmp_path):
    """Multiple measurements at same intensity are correctly averaged.

    Input: 20 unique intensities, each measured 3 times with slight variations
    Output: 20 unique intensity points with averaged luminance values
    Validates: Correct duplicate averaging and numerical accuracy
    """
    # Setup
    shutil.copy(TEST_DIR / "measurements_duplicates.csv", tmp_path / "measure.csv")

    # Run
    subprocess.run(["hrl-util", "lut", "smooth", "--order", "0"], check=True, cwd=tmp_path)
    result = np.genfromtxt(tmp_path / "smooth.csv", skip_header=1, delimiter=",")

    # Verify exactly 20 unique intensity points
    assert len(result) == 20

    # Verify values
    expected = np.genfromtxt(
        TEST_DIR / "smoothed_measurements_duplicates.csv", skip_header=1, delimiter=","
    )
    np.testing.assert_array_almost_equal(result, expected, decimal=10)


def test_smooth_filters_outliers(tmp_path):
    """Outlier measurements are correctly filtered out.

    Input: 50 intensities with 2-3 measurements each, some outliers at 30% deviation
    Output: Smoothed data with outliers removed from averaging
    Validates: Correct outlier filtering and numerical accuracy
    """
    # Setup
    shutil.copy(TEST_DIR / "measurements_outliers.csv", tmp_path / "measure.csv")

    # Run
    subprocess.run(["hrl-util", "lut", "smooth", "--order", "0"], check=True, cwd=tmp_path)
    result = np.genfromtxt(tmp_path / "smooth.csv", skip_header=1, delimiter=",")

    # Verify
    expected = np.genfromtxt(
        TEST_DIR / "smoothed_measurements_outliers.csv", skip_header=1, delimiter=","
    )
    np.testing.assert_array_almost_equal(result, expected, decimal=10)
