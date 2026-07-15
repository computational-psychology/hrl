"""Testing the `hrl-util lut` commands

Using subprocess to run the CLI commands,
and validating outputs against expected results in files.
"""

import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

TEST_DIR = Path(__file__).parent


### INTEGRATED LUT PROCESSING PIPELINE
@pytest.mark.parametrize("input_bitdepth, bit_depth", [(16, 16), (8, 8), (16, 10)])
def test_full_pipeline(tmp_path, input_bitdepth, bit_depth):
    """Complete workflow from raw measurements through smoothing to linearized LUT.

    Input: intensity-luminance measurements from measurements_{input_bitdepth}bit.csv
    Pipeline: smooth(order=0) → linearize at {bit_depth}-bit resolution
    Validates: Final LUT matches lut_{bit_depth}bit.csv
    """
    shutil.copy(TEST_DIR / f"measurements_{input_bitdepth}bit.csv", tmp_path / "measure.csv")

    # Step 1: Smooth
    subprocess.run(["hrl-util", "lut", "smooth", "--order", "0"], check=True, cwd=tmp_path)

    # Step 2: Linearize
    subprocess.run(
        ["hrl-util", "lut", "linearize", "--bit_depth", str(bit_depth)], check=True, cwd=tmp_path
    )
    result_lut = np.genfromtxt(tmp_path / "lut.csv", skip_header=1, delimiter=",")

    # Verify
    expected_lut = np.genfromtxt(
        TEST_DIR / f"lut_{bit_depth}bit.csv", skip_header=1, delimiter=","
    )
    np.testing.assert_array_almost_equal(result_lut, expected_lut, decimal=10)


def test_pipeline_preserves_luminance_range(tmp_path):
    """Pipeline preserves original luminance range from measurements to final LUT.

    Input: 80 intensity measurements with gamma~2.0 nonlinearity, 2.5-150 cd/m² range
    Pipeline: smooth with 1 kernel iteration → linearize at 8-bit resolution
    Validates: Final LUT matches expected values and preserves min/max luminance within 5%
    """
    lum_min, lum_max = 2.5, 150.0
    shutil.copy(TEST_DIR / "measurements_lumrange.csv", tmp_path / "measure.csv")

    # Step 1: Smooth
    subprocess.run(["hrl-util", "lut", "smooth", "--order", "1"], check=True, cwd=tmp_path)

    # Step 2: Linearize
    subprocess.run(["hrl-util", "lut", "linearize", "--bit_depth", "8"], check=True, cwd=tmp_path)
    result_lut = np.genfromtxt(tmp_path / "lut.csv", skip_header=1, delimiter=",")

    # Verify luminance range
    assert np.isclose(result_lut[0, 2], lum_min, rtol=0.05)
    assert np.isclose(result_lut[-1, 2], lum_max, rtol=0.05)

    # Verify values
    expected_lut = np.genfromtxt(TEST_DIR / "lut_lumrange.csv", skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result_lut, expected_lut, decimal=10)


### STEP 1: PROCESSING MEASUREMENTS ###
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


def test_averaging(tmp_path):
    """Average only (no smoothing, order=0) matches pre-computed expected values.

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

    Input: 256 intensity measurements with gamma~2.2 nonlinearity and small noise
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


### STEP 2: LINEARIZE ###
def test_linearize_output_format(tmp_path):
    """Output CSV file structure and data validity.

    Input: 256 intensity-luminance measurement pairs (gamma~2.2, 1-101 cd/m²)
    Output: LUT with 3 columns (intensity_in, intensity_out, luminance)
    Validates: Presence of required headers, no NaN values, intensities in [0,1] range
    """
    # Setup
    shutil.copy(TEST_DIR / "measurements_8bit.csv", tmp_path / "smooth.csv")

    # Run
    subprocess.run(["hrl-util", "lut", "linearize"], check=True, cwd=tmp_path)
    header = (tmp_path / "lut.csv").read_text().splitlines()[0]
    result = np.genfromtxt(tmp_path / "lut.csv", skip_header=1, delimiter=",")

    # Verify format
    assert "intensity_in" in header
    assert "intensity_out" in header
    assert "luminance" in header
    assert result.shape[1] == 3

    # Verify values
    assert not np.any(np.isnan(result))
    assert np.all(result[:, 0] >= 0) and np.all(result[:, 0] <= 1)
    assert np.all(result[:, 1] >= 0) and np.all(result[:, 1] <= 1)


@pytest.mark.parametrize("input_bitdepth, bit_depth", [(16, 16), (8, 8), (16, 10)])
def test_linearize_different_bitdepths(tmp_path, input_bitdepth, bit_depth):
    """Linearize with different target bit depths produces expected LUT output.

    Input: intensity-luminance measurements from measurements_{input_bitdepth}bit.csv
    Output: ≤2**{bit_depth} LUT entries mapping intensities for linear luminance progression
    Validates: Output length within bounds and numerical accuracy vs lut_{bit_depth}bit.csv
    """
    # Setup
    shutil.copy(TEST_DIR / f"measurements_{input_bitdepth}bit.csv", tmp_path / "smooth.csv")

    # Run
    subprocess.run(
        ["hrl-util", "lut", "linearize", "--bit_depth", str(bit_depth)], check=True, cwd=tmp_path
    )
    result = np.genfromtxt(tmp_path / "lut.csv", skip_header=1, delimiter=",")

    # Verify
    assert len(result) <= 2**bit_depth
    expected = np.genfromtxt(TEST_DIR / f"lut_{bit_depth}bit.csv", skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result, expected, decimal=10)


### ERROR HANDLING ###
def test_smooth_fails_on_missing_input(tmp_path):
    """Smooth command exits with non-zero status when input file (measure.csv) is missing."""
    result = subprocess.run(
        ["hrl-util", "lut", "smooth", "--order", "0"], cwd=tmp_path, capture_output=True
    )
    assert result.returncode != 0


def test_linearize_fails_on_missing_input(tmp_path):
    """Linearize command exits with non-zero status when input file (smooth.csv) is missing."""
    result = subprocess.run(["hrl-util", "lut", "linearize"], cwd=tmp_path, capture_output=True)
    assert result.returncode != 0
