"""Integration tests for the complete LUT processing pipeline using static test data."""

import shutil
import subprocess
from pathlib import Path

import numpy as np

TEST_DIR = Path(__file__).parent


def test_full_pipeline(tmp_path):
    """Complete workflow from raw measurements through smoothing to linearized LUT.

    Input: 256 intensity measurements with gamma~2.2 nonlinearity and small random noise
    Pipeline: smooth with order=0 (averaging) → linearize at 8-bit resolution
    Validates: Final LUT matches expected values from unit tests
    """
    shutil.copy(TEST_DIR / "measurements_8bit.csv", tmp_path / "measure.csv")

    # Step 1: Smooth
    subprocess.run(["hrl-util", "lut", "smooth", "--order", "0"], check=True, cwd=tmp_path)

    # Step 2: Linearize
    subprocess.run(["hrl-util", "lut", "linearize", "--bit_depth", "8"], check=True, cwd=tmp_path)
    result_lut = np.genfromtxt(tmp_path / "lut.csv", skip_header=1, delimiter=",")

    # Verify
    expected_lut = np.genfromtxt(TEST_DIR / "lut_8bit.csv", skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result_lut, expected_lut, decimal=10)


def test_pipeline_preserves_luminance_range(tmp_path):
    """Pipeline preserves original luminance range from measurements to final LUT.

    Input: 80 intensity measurements with gamma~2.0 nonlinearity, 2.5-150 cd/m² range
    Pipeline: smooth with 1 kernel iteration → linearize at 8-bit resolution
    Validates: Final LUT matches expected values and preserves min/max luminance within 10%
    """
    lum_min, lum_max = 2.5, 150.0
    shutil.copy(TEST_DIR / "measurements_lumrange.csv", tmp_path / "measure.csv")

    # Step 1: Smooth
    subprocess.run(["hrl-util", "lut", "smooth", "--order", "1"], check=True, cwd=tmp_path)

    # Step 2: Linearize
    subprocess.run(["hrl-util", "lut", "linearize", "--bit_depth", "8"], check=True, cwd=tmp_path)
    result_lut = np.genfromtxt(tmp_path / "lut.csv", skip_header=1, delimiter=",")

    # Verify luminance range
    assert np.isclose(result_lut[0, 2], lum_min, rtol=0.1)
    assert np.isclose(result_lut[-1, 2], lum_max, rtol=0.1)

    # Verify values
    expected_lut = np.genfromtxt(TEST_DIR / "lut_lumrange.csv", skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result_lut, expected_lut, decimal=10)
