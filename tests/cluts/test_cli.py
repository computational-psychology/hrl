"""Testing the `hrl-util clut` commands.

Using subprocess for CLI integration and mocks for hardware-facing steps.
"""

import subprocess
import types
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from hrl.cluts import RGB_to_XYZ, gamma_correct_RGB
from hrl.photometer.photometer import MockColorimeter

TEST_DIR = Path(__file__).parent


def _mock_draw(ihrl, triplet, patch_size=None):
    """Draw stub: records CLUT-corrected triplet on the mock colorimeter."""
    triplet_out = np.asarray(ihrl.graphics.gamma_correct(triplet), dtype=float)
    ihrl.photometer.current_triplet = triplet_out


def _make_colorimeter_from_clut(clut):
    """MockColorimeter mapping emitted (already-driven) RGB to XYZ via the
    full per-level CLUT model (`gamma_correct=False`: the mock receives
    drive-space triplets, matching what a real colorimeter is pointed at)."""

    def emitted_rgb_to_xyz(r, g, b):
        xyz = RGB_to_XYZ(np.array([r, g, b], dtype=float), clut, gamma_correct=False)
        return tuple(xyz[0])

    return MockColorimeter(color_mapping=emitted_rgb_to_xyz)


### INTEGRATED CLUT PROCESSING PIPELINE
@pytest.mark.parametrize("bit_depth", [8, 10])
def test_full_pipeline(tmp_path, bit_depth):
    """Complete CLI workflow: smooth -> linearize."""
    measure_file = TEST_DIR / "measurements_8bit.csv"
    smooth_file = tmp_path / "smooth.csv"
    clut_file = tmp_path / f"clut_{bit_depth}bit.csv"

    subprocess.run(
        [
            "hrl-util",
            "clut",
            "smooth",
            "--in_file",
            str(measure_file),
            "--out_file",
            str(smooth_file),
        ],
        check=True,
    )

    subprocess.run(
        [
            "hrl-util",
            "clut",
            "linearize",
            "--in_file",
            str(smooth_file),
            "--out_file",
            str(clut_file),
            "--bit_depth",
            str(bit_depth),
        ],
        check=True,
    )

    result_clut = np.genfromtxt(clut_file, skip_header=1, delimiter=",")
    expected_clut = np.genfromtxt(
        TEST_DIR / f"clut_{bit_depth}bit.csv", skip_header=1, delimiter=","
    )

    np.testing.assert_array_almost_equal(result_clut, expected_clut, decimal=10)


### STEP 0: MEASURE XYZ VALUES
def test_measure(tmp_path):
    """measure command runs end-to-end with mocked HRL and writes correct measurements."""
    from hrl.util.clut.measure import command, parser

    clut = np.genfromtxt(TEST_DIR / "clut_8bit.csv", delimiter=",", skip_header=1)
    out_file = tmp_path / "measure.csv"
    bit_depth = 4  # 16 levels per channel sweep
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
        photometer=_make_colorimeter_from_clut(clut),
        graphics=types.SimpleNamespace(
            gamma_correct=lambda x: gamma_correct_RGB(
                np.asarray(x).reshape(1, 1, 3), CLUT=clut
            ).flatten()
        ),
        inputs=None,
        close=lambda: None,
    )

    with patch("hrl.util.clut.measure.HRL", return_value=mock_ihrl):
        with patch("hrl.util.clut.measure._draw_uniform_rgb_square", _mock_draw):
            command(args)

    measurements = np.genfromtxt(out_file, delimiter=",", skip_header=1)
    assert measurements.shape == (3 * n_samples * 2**bit_depth, 6)


### STEP 1: PROCESS MEASUREMENTS
def test_smooth_output_format(tmp_path):
    """Output CSV file structure and data validity for clut smooth command."""
    out_file = tmp_path / "smooth.csv"

    subprocess.run(
        [
            "hrl-util",
            "clut",
            "smooth",
            "--in_file",
            str(TEST_DIR / "measurements_8bit.csv"),
            "--out_file",
            str(out_file),
        ],
        check=True,
    )

    header = out_file.read_text().splitlines()[0]
    result = np.genfromtxt(out_file, skip_header=1, delimiter=",")

    assert all(k in header for k in ["R", "G", "B", "X", "Y", "Z"])
    assert result.shape[1] == 6
    assert not np.any(np.isnan(result))


### STEP 2: LINEARIZE
def test_linearize_output_format(tmp_path):
    """Output CSV file structure and data validity for clut linearize command."""
    out_file = tmp_path / "clut.csv"

    subprocess.run(
        [
            "hrl-util",
            "clut",
            "linearize",
            "--in_file",
            str(TEST_DIR / "measurements_8bit.csv"),
            "--out_file",
            str(out_file),
            "--bit_depth",
            "8",
        ],
        check=True,
    )

    header = out_file.read_text().splitlines()[0]
    result = np.genfromtxt(out_file, skip_header=1, delimiter=",")

    assert "intensity_in" in header and "R_out" in header and "Z_B" in header
    assert result.shape[1] == 13
    assert not np.any(np.isnan(result))
    assert np.all(result[:, 0] >= 0) and np.all(result[:, 0] <= 1)


def test_verify(tmp_path):
    """verify command runs end-to-end with mocked HRL and writes measurements."""
    from hrl.util.clut.verify import command, parser

    clut_file = TEST_DIR / "clut_8bit.csv"
    clut = np.genfromtxt(clut_file, skip_header=1, delimiter=",")
    out_file = tmp_path / "verify.csv"

    args = parser.parse_args(
        [
            "--lut",
            str(clut_file),
            "--out_file",
            str(out_file),
        ]
    )

    mock_ihrl = types.SimpleNamespace(
        photometer=_make_colorimeter_from_clut(clut),
        graphics=types.SimpleNamespace(
            gamma_correct=lambda x: gamma_correct_RGB(
                np.asarray(x).reshape(1, 1, 3), CLUT=clut
            ).flatten()
        ),
        inputs=None,
        close=lambda: None,
    )

    with patch("hrl.util.clut.verify.HRL", return_value=mock_ihrl):
        with patch("hrl.util.clut.verify._draw_uniform_rgb_square", _mock_draw):
            command(args)

    measurements = np.genfromtxt(out_file, delimiter=",", skip_header=1)
    assert measurements.shape == (3 * clut.shape[0], 6)


### ERROR HANDLING
def test_smooth_fails_on_missing_input(tmp_path):
    result = subprocess.run(
        [
            "hrl-util",
            "clut",
            "smooth",
            "--in_file",
            str(tmp_path / "nonexistent.csv"),
        ],
        capture_output=True,
    )
    assert result.returncode != 0


def test_linearize_fails_on_missing_input(tmp_path):
    result = subprocess.run(
        [
            "hrl-util",
            "clut",
            "linearize",
            "--in_file",
            str(tmp_path / "nonexistent.csv"),
        ],
        capture_output=True,
    )
    assert result.returncode != 0
