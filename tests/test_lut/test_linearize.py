"""Unit tests for the linearize function using static test data."""

import os
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

TEST_DIR = Path(__file__).parent


@pytest.fixture
def input_8bit():
    """Provide 8-bit measured luminance input data and clean up output files after test.

    Input file contains 256 intensity-luminance measurement pairs from a monitor
    with gamma~2.2 nonlinearity, spanning 1-101 cd/m².
    """
    # Setup: copy input file
    shutil.copy(TEST_DIR / "measurements_8bit.csv", "smooth.csv")

    yield

    # Cleanup: remove both input and output files
    for f in ["smooth.csv", "lut.csv"]:
        if os.path.exists(f):
            os.remove(f)


@pytest.fixture
def input_16bit():
    """Provide 16-bit measured luminance input data and clean up output files after test.

    Input file contains 65536 intensity-luminance measurement pairs from a monitor
    with gamma~2.2 nonlinearity, spanning 1-101 cd/m².
    """
    # Setup: copy input file
    shutil.copy(TEST_DIR / "measurements_16bit.csv", "smooth.csv")

    yield

    # Cleanup: remove both input and output files
    for f in ["smooth.csv", "lut.csv"]:
        if os.path.exists(f):
            os.remove(f)


def test_linearize_output_format(input_16bit):
    """Output CSV file structure and data validity.

    Input: 65536 intensity-luminance measurement pairs (gamma~2.2, 1-101 cd/m²)
    Output: LUT with 3 columns (IntensityIn, IntensityOut, Luminance)
    Validates: Presence of required headers, no NaN values, intensities in [0,1] range
    """
    subprocess.run(["hrl-util", "lut", "linearize", "-r", "10"], check=True)

    with open("lut.csv", "r") as f:
        header = f.readline().strip()

    assert "IntensityIn" in header
    assert "IntensityOut" in header
    assert "Luminance" in header

    result = np.genfromtxt("lut.csv", skip_header=1)
    assert result.shape[1] == 3
    assert not np.any(np.isnan(result))
    assert np.all(result[:, 0] >= 0) and np.all(result[:, 0] <= 1)
    assert np.all(result[:, 1] >= 0) and np.all(result[:, 1] <= 1)


def test_linearize_luminance_linearity(input_16bit):
    """Resulting luminance values increase in approximately uniform steps.

    Input: 65536 intensity-luminance measurement pairs (gamma~2.2, 1-101 cd/m²)
    Output: 16-bit LUT mapping intensities to produce linear luminance progression
    Validates: Monotonic luminance increase with low step-size variability (CV < 1.5)
    """
    subprocess.run(["hrl-util", "lut", "linearize", "-r", "16"], check=True)

    result = np.genfromtxt("lut.csv", skip_header=1)
    luminances = result[:, 2]

    assert np.all(np.diff(luminances) >= 0)  # Monotonic

    lum_diffs = np.diff(luminances)
    non_zero_diffs = lum_diffs[lum_diffs > 1e-6]

    if len(non_zero_diffs) > 10:
        cv = np.std(non_zero_diffs) / np.mean(non_zero_diffs)
        assert cv < 1.5  # Reasonable uniformity


def test_linearize_16bit(input_16bit):
    """16-bit resolution LUT matches pre-computed expected values.

    Input: 65536 intensity-luminance measurement pairs (gamma~2.2, 1-101 cd/m²)
    Output: Up to 2^16 LUT entries mapping intensities for linear luminance progression
    Validates: Numerical accuracy via regression against known-good output
    """
    subprocess.run(["hrl-util", "lut", "linearize", "-r", "16"], check=True)

    result = np.genfromtxt("lut.csv", skip_header=1)
    expected = np.genfromtxt(TEST_DIR / "lut_16bit.csv", skip_header=1)

    np.testing.assert_array_almost_equal(result, expected, decimal=10)


def test_linearize_8bit(input_8bit):
    """8-bit resolution LUT has ≤256 entries and matches expected values.

    Input: 256 intensity-luminance measurement pairs (gamma~2.2, 1-101 cd/m²)
    Output: ≤256 LUT entries mapping intensities for linear luminance progression
    Validates: Numerical accuracy and compliance with 8-bit length constraint
    """
    subprocess.run(["hrl-util", "lut", "linearize", "-r", "8"], check=True)

    result = np.genfromtxt("lut.csv", skip_header=1)
    expected = np.genfromtxt(TEST_DIR / "lut_8bit.csv", skip_header=1)

    np.testing.assert_array_almost_equal(result, expected, decimal=10)

    assert len(result) <= 2**8


def test_linearize_10bit(input_16bit):
    """10-bit resolution LUT has ≤1024 entries and matches expected values.

    Input: 65536 intensity-luminance measurement pairs (gamma~2.2, 1-101 cd/m²)
    Output: ≤1024 LUT entries mapping intensities for linear luminance progression
    Validates: Numerical accuracy and compliance with 10-bit length constraint
    """
    subprocess.run(["hrl-util", "lut", "linearize", "-r", "10"], check=True)

    result = np.genfromtxt("lut.csv", skip_header=1)
    expected = np.genfromtxt(TEST_DIR / "lut_10bit.csv", skip_header=1)

    np.testing.assert_array_almost_equal(result, expected, decimal=10)

    assert len(result) <= 2**10
