"""Testing the `hrl-util lut` commands

Using subprocess to run the CLI commands,
and validating outputs against expected results in files.
"""

import subprocess
import types
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from hrl.photometer.photometer import MockPhotometer

TEST_DIR = Path(__file__).parent


def _mock_draw(ihrl, intensity, patch_size=None):
    """Draw stub: records intensity on the mock photometer."""
    intensity_out = ihrl.graphics.gamma_correct(intensity)
    ihrl.photometer.current_intensity = intensity_out


### INTEGRATED LUT PROCESSING PIPELINE
@pytest.mark.parametrize(
    "input_bit_depth, output_bit_depth",
    [
        pytest.param(8, 8, id="8bit"),
        pytest.param(16, 16, id="16bit"),
        pytest.param(16, 10, id="10bit-from-16bit"),
    ],
)
def test_full_pipeline(tmp_path, input_bit_depth, output_bit_depth):
    """Complete CLI workflow: measure → smooth → linearize.

    Input: intensity-luminance measurements from measurements_{input_bitdepth}bit.csv
    Pipeline: smooth(order=0) → linearize at {bit_depth}-bit resolution
    Validates: Final LUT matches lut_{bit_depth}bit.csv
    """
    measure_file = TEST_DIR / f"measurements_{input_bit_depth}bit.csv"
    smooth_file = tmp_path / "smooth.csv"
    lut_file = f"lut_{output_bit_depth}bit.csv"

    # Step 1: Smooth
    subprocess.run(
        [
            "hrl-util",
            "lut",
            "smooth",
            "--in_file",
            str(measure_file),
            "--out_file",
            str(smooth_file),
            "--order",
            "0",
        ],
        check=True,
    )

    # Step 2: Linearize
    subprocess.run(
        [
            "hrl-util",
            "lut",
            "linearize",
            "--in_file",
            str(smooth_file),
            "--out_file",
            str(tmp_path / lut_file),
            "--bit_depth",
            str(output_bit_depth),
        ],
        check=True,
    )
    result_lut = np.genfromtxt(tmp_path / lut_file, skip_header=1, delimiter=",")

    expected_lut = np.genfromtxt(TEST_DIR / lut_file, skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result_lut, expected_lut, decimal=10)


def test_pipeline_preserves_luminance_range(tmp_path):
    """Pipeline preserves original luminance range from measurements to final LUT.

    Input: 80 intensity measurements with gamma~2.0 nonlinearity, 2.5-150 cd/m² range
    Pipeline: smooth with 1 kernel iteration → linearize at 8-bit resolution
    Validates: Final LUT matches expected values and preserves min/max luminance within 5%
    """
    lum_min, lum_max = 2.5, 150.0
    smooth_file = tmp_path / "smooth.csv"
    lut_file = tmp_path / "lut.csv"

    # Step 1: Smooth
    subprocess.run(
        [
            "hrl-util",
            "lut",
            "smooth",
            "--in_file",
            str(TEST_DIR / "measurements_lumrange.csv"),
            "--out_file",
            str(smooth_file),
            "--order",
            "1",
        ],
        check=True,
    )

    # Step 2: Linearize
    subprocess.run(
        [
            "hrl-util",
            "lut",
            "linearize",
            "--in_file",
            str(smooth_file),
            "--out_file",
            str(lut_file),
            "--bit_depth",
            "8",
        ],
        check=True,
    )
    result_lut = np.genfromtxt(lut_file, skip_header=1, delimiter=",")

    # Verify luminance range
    assert np.isclose(result_lut[0, 2], lum_min, rtol=0.05)
    assert np.isclose(result_lut[-1, 2], lum_max, rtol=0.05)

    # Verify values
    expected_lut = np.genfromtxt(TEST_DIR / "lut_lumrange.csv", skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result_lut, expected_lut, decimal=10)


### STEP 0: MEASURE LUMINANCE VALUES ###
def test_measure(tmp_path):
    """measure command runs end-to-end with mocked HRL and writes correct measurements.

    HRL (which opens a display and connects to a photometer) is replaced by a minimal
    stand-in so the test runs without any hardware. draw_uniform_square is wrapped to
    update photometer.current_intensity so MockPhotometer returns the correct luminance
    for each drawn intensity.
    """
    from hrl.util.lut.measure import command, parser

    lut = np.genfromtxt(TEST_DIR / "lut_8bit.csv", delimiter=",", skip_header=1)
    out_file = tmp_path / "measure.csv"
    bit_depth = 4  # 2**4 = 16 intensity steps
    n_samples = 2

    args = parser.parse_args(
        [
            "--bit_depth",
            str(bit_depth),
            "--out_file",
            str(out_file),
            "--n_samples",
            str(n_samples),
        ]
    )

    mock_ihrl = types.SimpleNamespace(
        photometer=MockPhotometer(luminance_mapping=lut),
        graphics=types.SimpleNamespace(gamma_correct=lambda x: x),
        inputs=None,
        close=lambda: None,
    )

    with patch("hrl.util.lut.measure.HRL", return_value=mock_ihrl):
        with patch("hrl.util.lut.measure.draw_uniform_square", _mock_draw):
            command(args)

    measurements = np.genfromtxt(out_file, delimiter=",", skip_header=1)
    assert measurements.shape == (2**bit_depth, n_samples + 1)

    expected_intensities = np.linspace(0.0, 1.0, 2**bit_depth)
    np.testing.assert_array_equal(measurements[:, 0], expected_intensities)

    expected_luminances = np.interp(expected_intensities, lut[:, 1], lut[:, -1])
    for i in range(n_samples):
        np.testing.assert_allclose(measurements[:, i + 1], expected_luminances, rtol=1e-6)


### STEP 1: PROCESSING MEASUREMENTS ###
def test_smooth_output_format(tmp_path):
    """Output CSV file structure and data validity.

    Input: 256 intensity measurements with gamma~2.2 nonlinearity and small noise
    Output: Smoothed data with 2 columns (intensity_in, luminance)
    Validates: Presence of required headers, no NaN values, non-negative values
    """
    out_file = tmp_path / "smooth.csv"

    # Run
    subprocess.run(
        [
            "hrl-util",
            "lut",
            "smooth",
            "--in_file",
            str(TEST_DIR / "measurements_8bit.csv"),
            "--out_file",
            str(out_file),
            "--order",
            "0",
        ],
        check=True,
    )
    header = out_file.read_text().splitlines()[0]
    result = np.genfromtxt(out_file, skip_header=1, delimiter=",")

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
    out_file = tmp_path / "smooth.csv"

    # Run
    subprocess.run(
        [
            "hrl-util",
            "lut",
            "smooth",
            "--in_file",
            str(TEST_DIR / "measurements_8bit.csv"),
            "--out_file",
            str(out_file),
            "--order",
            "0",
        ],
        check=True,
    )
    result = np.genfromtxt(out_file, skip_header=1, delimiter=",")

    # Verify
    expected = np.genfromtxt(TEST_DIR / "measurements_8bit.csv", skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result, expected, decimal=10)


def test_smooth_with_kernel(tmp_path):
    """Order=2 kernel smoothing matches pre-computed expected values.

    Input: 256 intensity measurements with gamma~2.2 nonlinearity and small noise
    Output: Smoothed data with 2 iterations of kernel smoothing applied
    Validates: Numerical accuracy via regression against known-good output
    """
    out_file = tmp_path / "smooth.csv"

    # Run
    subprocess.run(
        [
            "hrl-util",
            "lut",
            "smooth",
            "--in_file",
            str(TEST_DIR / "measurements_8bit.csv"),
            "--out_file",
            str(out_file),
            "--order",
            "2",
        ],
        check=True,
    )
    result = np.genfromtxt(out_file, skip_header=1, delimiter=",")

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
    out_file = tmp_path / "lut.csv"

    # Run
    subprocess.run(
        [
            "hrl-util",
            "lut",
            "linearize",
            "--in_file",
            str(TEST_DIR / "measurements_8bit.csv"),
            "--out_file",
            str(out_file),
        ],
        check=True,
    )
    header = out_file.read_text().splitlines()[0]
    result = np.genfromtxt(out_file, skip_header=1, delimiter=",")

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
    out_file = tmp_path / "lut.csv"

    # Run
    subprocess.run(
        [
            "hrl-util",
            "lut",
            "linearize",
            "--in_file",
            str(TEST_DIR / f"measurements_{input_bitdepth}bit.csv"),
            "--out_file",
            str(out_file),
            "--bit_depth",
            str(bit_depth),
        ],
        check=True,
    )
    result = np.genfromtxt(out_file, skip_header=1, delimiter=",")

    # Verify
    assert len(result) <= 2**bit_depth
    expected = np.genfromtxt(TEST_DIR / f"lut_{bit_depth}bit.csv", skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result, expected, decimal=10)


def test_verify(tmp_path):
    """Verify command runs end-to-end with mocked HRL and validates LUT.

    Input: LUT from lut_8bit.csv
    Output: Verification CSV with measured luminance values for each intensity
    Validates: Measured luminance values match expected values from LUT within tolerance
    """
    from hrl.luts import gamma_correct_grey
    from hrl.util.lut.verify import command, parser

    lut_file = TEST_DIR / "lut_8bit.csv"
    lut = np.genfromtxt(lut_file, skip_header=1, delimiter=",")
    out_file = tmp_path / "verify.csv"
    n_samples = 2

    args = parser.parse_args(
        [
            "--lut",
            str(lut_file),
            "--out_file",
            str(out_file),
            "--n_samples",
            str(n_samples),
        ]
    )

    mock_ihrl = types.SimpleNamespace(
        photometer=MockPhotometer(luminance_mapping=lut),
        graphics=types.SimpleNamespace(gamma_correct=lambda x: gamma_correct_grey(x, LUT=lut)),
        inputs=None,
        close=lambda: None,
    )

    with patch("hrl.util.lut.verify.HRL", return_value=mock_ihrl):
        with patch("hrl.util.lut.verify.draw_uniform_square", _mock_draw):
            command(args)

    measurements = np.genfromtxt(out_file, delimiter=",", skip_header=1)
    assert measurements.shape == (256, n_samples + 1)

    for i in range(n_samples):
        np.testing.assert_array_equal(measurements[:, i + 1], lut[:, -1])


### ERROR HANDLING ###
def test_smooth_fails_on_missing_input(tmp_path):
    """Smooth command exits with non-zero status when input file is missing."""
    result = subprocess.run(
        [
            "hrl-util",
            "lut",
            "smooth",
            "--in_file",
            str(tmp_path / "nonexistent.csv"),
        ],
        capture_output=True,
    )
    assert result.returncode != 0


def test_linearize_fails_on_missing_input(tmp_path):
    """Linearize command exits with non-zero status when input file is missing."""
    result = subprocess.run(
        [
            "hrl-util",
            "lut",
            "linearize",
            "--in_file",
            str(tmp_path / "nonexistent.csv"),
        ],
        capture_output=True,
    )
    assert result.returncode != 0
