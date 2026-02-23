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
