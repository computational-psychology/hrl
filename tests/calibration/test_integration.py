"""Integration tests for the complete LUT processing pipeline using static test data."""

import os
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

TEST_DIR = Path(__file__).parent


@pytest.fixture
def measure_integration_input():
    """Provide integration test measurement data and clean up output files after test.

    Input file contains 256 intensity measurements with gamma~2.2 nonlinearity
    and small random noise.
    """
    # Setup: copy input file
    shutil.copy(TEST_DIR / "measurements_8bit.csv", "measure.csv")

    yield

    # Cleanup: remove all pipeline files
    for f in ["measure.csv", "smooth.csv", "lut.csv"]:
        if os.path.exists(f):
            os.remove(f)


@pytest.fixture
def measure_lumrange_input():
    """Provide luminance range test measurement data and clean up output files after test.

    Input file contains 80 intensity measurements with gamma~2.0 nonlinearity,
    spanning luminance range 2.5-150 cd/m².
    """
    # Setup: copy input file
    shutil.copy(TEST_DIR / "measurements_lumrange.csv", "measure.csv")

    yield

    # Cleanup: remove all pipeline files
    for f in ["measure.csv", "smooth.csv", "lut.csv"]:
        if os.path.exists(f):
            os.remove(f)


def test_full_pipeline(measure_integration_input):
    """Complete workflow from raw measurements through smoothing to linearized LUT.

    Input: 256 intensity measurements with gamma~2.2 nonlinearity and small random noise
    Pipeline: smooth with order=0 (averaging) → linearize at 8-bit resolution
    Validates: Final LUT matches expected values from unit tests
    """
    # Step 1: Smooth
    subprocess.run(["hrl-util", "lut", "smooth", "--order", "0"], check=True)

    # Step 2: Linearize
    subprocess.run(["hrl-util", "lut", "linearize", "--bit_depth", "8"], check=True)

    # Compare
    result_lut = np.genfromtxt("lut.csv", skip_header=1, delimiter=",")
    expected_lut = np.genfromtxt(TEST_DIR / "lut_8bit.csv", skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result_lut, expected_lut, decimal=10)


def test_pipeline_preserves_luminance_range(measure_lumrange_input):
    """Pipeline preserves original luminance range from measurements to final LUT.

    Input: 80 intensity measurements with gamma~2.0 nonlinearity, 2.5-150 cd/m² range
    Pipeline: smooth with 1 kernel iteration → linearize at 8-bit resolution
    Validates: Final LUT matches expected values and preserves min/max luminance within 10%
    """
    lum_min, lum_max = 2.5, 150.0

    # Step 1: Smooth
    subprocess.run(["hrl-util", "lut", "smooth", "--order", "1"], check=True)

    # Step 2: Linearize
    subprocess.run(["hrl-util", "lut", "linearize", "--bit_depth", "8"], check=True)

    # Verify luminance range
    result_lut = np.genfromtxt("lut.csv", skip_header=1, delimiter=",")
    expected_lut = np.genfromtxt(TEST_DIR / "lut_lumrange.csv", skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result_lut, expected_lut, decimal=10)

    result_lum_min = result_lut[0, 2]
    result_lum_max = result_lut[-1, 2]

    assert np.isclose(result_lum_min, lum_min, rtol=0.1)
    assert np.isclose(result_lum_max, lum_max, rtol=0.1)
