"""Testing the `hrl-util clut` commands.

Using subprocess for CLI integration and mocks for hardware-facing steps.
"""

import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from hrl.cluts import gamma_correct_RGB
from hrl.cluts.calibrate import read_measurements
from hrl.photometer.photometer import MockColorimeter

TEST_DIR = Path(__file__).parent

# Invoked as a module rather than through the `hrl-util` console script. The script is
# generated at install time from `[project.scripts]`, so an environment installed before
# that entry point last changed has a stale one, and these tests then fail for a reason
# that has nothing to do with the CLI they are testing.
CLI = [sys.executable, "-m", "hrl.util"]


def _mock_draw(ihrl, triplet, patch_size=None):
    """Draw stub: records CLUT-corrected triplet on the mock colorimeter."""
    triplet_out = np.asarray(ihrl.graphics.gamma_correct(triplet), dtype=float)
    ihrl.photometer.current_triplet = triplet_out


### INTEGRATED CLUT PROCESSING PIPELINE
@pytest.mark.parametrize("bit_depth", [8, 10])
def test_full_pipeline(tmp_path, bit_depth):
    """Complete CLI workflow: smooth -> linearize."""
    measure_file = TEST_DIR / "measurements_8bit.csv"
    smooth_file = tmp_path / "smooth.csv"
    clut_file = tmp_path / f"clut_{bit_depth}bit.csv"

    subprocess.run(
        CLI + ["clut", "smooth", "--in_file", str(measure_file), "--out_file", str(smooth_file)],
        check=True,
    )

    subprocess.run(
        CLI
        + [
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
        photometer=MockColorimeter(color_mapping=clut),
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

    measurements, labels = read_measurements(out_file)
    assert measurements.shape == (3 * n_samples * 2**bit_depth, 6)
    assert (labels == "channels").all()


### STEP 1: PROCESS MEASUREMENTS
def test_smooth_output_format(tmp_path):
    """Output CSV file structure and data validity for clut smooth command."""
    out_file = tmp_path / "smooth.csv"

    subprocess.run(
        CLI
        + [
            "clut",
            "smooth",
            "--in_file",
            str(TEST_DIR / "measurements_8bit.csv"),
            "--out_file",
            str(out_file),
        ],
        check=True,
    )

    with open(out_file) as f:
        assert f.readline().strip() == "R,G,B,X,Y,Z"
    result = np.genfromtxt(out_file, skip_header=1, delimiter=",")
    assert result.shape[1] == 6
    assert not np.any(np.isnan(result))


def test_smooth_fails_on_missing_input(tmp_path):
    result = subprocess.run(
        CLI + ["clut", "smooth", "--in_file", str(tmp_path / "nonexistent.csv")],
        capture_output=True,
    )
    assert result.returncode != 0


### STEP 2: LINEARIZE
def test_linearize_output_format(tmp_path):
    """Output CSV file structure and data validity for clut linearize command."""
    out_file = tmp_path / "clut.csv"

    subprocess.run(
        CLI
        + [
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

    assert "intensity_in" in header and "R_out" in header and "B_Z" in header
    assert result.shape[1] == 13
    assert not np.any(np.isnan(result))
    assert np.all(result[:, 0] >= 0) and np.all(result[:, 0] <= 1)


### STEP 3: VERIFY, BY MEASURING WITH THE CLUT APPLIED
def _run_measure(tmp_path, *extra_args):
    """Run the measure command with the 8-bit CLUT applied and HRL mocked; return the
    CLUT and what was saved."""
    from hrl.util.clut.measure import command, parser

    clut_file = TEST_DIR / "clut_8bit.csv"
    clut = np.genfromtxt(clut_file, skip_header=1, delimiter=",")
    out_file = tmp_path / "verify.csv"

    args = parser.parse_args(
        ["--lut", str(clut_file), "--out_file", str(out_file), "--n_samples", "1", *extra_args]
    )

    mock_ihrl = types.SimpleNamespace(
        photometer=MockColorimeter(color_mapping=clut),
        graphics=types.SimpleNamespace(
            gamma_correct=lambda x: gamma_correct_RGB(
                np.asarray(x).reshape(1, 1, 3), CLUT=clut
            ).flatten()
        ),
        inputs=None,
        close=lambda: None,
    )

    with patch("hrl.util.clut.measure.HRL", return_value=mock_ihrl) as HRL:
        with patch("hrl.util.clut.measure._draw_uniform_rgb_square", _mock_draw):
            command(args)

    assert HRL.call_args.kwargs["lut"] == clut_file
    return clut, *read_measurements(out_file)


def test_measure_with_a_clut_applied(tmp_path):
    """measure --lut measures with the CLUT applied."""
    clut, measurements, labels = _run_measure(tmp_path)

    # each channel on its own, at every level of an 8-bit CLUT
    assert measurements.shape == (3 * 2**8, 6)
    assert (labels == "channels").all()


def test_measure_mixtures_with_a_clut_applied(tmp_path):
    clut, measurements, labels = _run_measure(tmp_path, "--sets", "sweeps", "mixtures")

    # each channel at every level; the mixtures: black, each channel alone at the 4
    # mixture levels and the 15 grey levels between black and white, 64 mixtures and those
    # 15 greys
    assert measurements.shape == (3 * 2**8 + 1 + 3 * (4 + 15) + 64 + 15, 6)
    for label, count in [
        ("channels", 3 * 2**8),
        ("additivity", 1 + 3 * (4 + 15) + 64 + 15),
    ]:
        assert (labels == label).sum() == count, label


def test_measure_triplets_from_a_file(tmp_path):
    triplets_file = tmp_path / "triplets.csv"
    triplets_file.write_text("R,G,B,label\n0.5,0.5,0.5,grey\n1,0,0,red\n0.2,0.4,0.6,\n")

    clut, measurements, labels = _run_measure(tmp_path, "--triplets", str(triplets_file))

    # only the file's triplets, as no sets were asked for; with their labels, if any
    np.testing.assert_array_equal(
        measurements[:, :3], [[0.5, 0.5, 0.5], [1, 0, 0], [0.2, 0.4, 0.6]]
    )
    np.testing.assert_array_equal(labels, ["grey", "red", ""])


def test_measure_triplets_from_a_file_besides_sets(tmp_path):
    triplets_file = tmp_path / "triplets.csv"
    triplets_file.write_text("R,G,B\n0.5,0.5,0.5\n")

    clut, measurements, labels = _run_measure(
        tmp_path, "--sets", "sweeps", "--triplets", str(triplets_file)
    )

    assert measurements.shape == (3 * 2**8 + 1, 6)
    np.testing.assert_array_equal(measurements[-1, :3], [0.5, 0.5, 0.5])
    assert labels[-1] == ""


### EVALUATE
def test_evaluate_reports_each_channel(tmp_path):
    clut_file = TEST_DIR / "clut_8bit.csv"
    clut = np.genfromtxt(clut_file, skip_header=1, delimiter=",")

    # Readings exactly as the CLUT records them: each channel on its own, at its levels
    rows = [
        np.column_stack([np.outer(clut[:, 0], np.eye(3)[c]), clut[:, 4 + 3 * c : 7 + 3 * c]])
        for c in range(3)
    ]
    in_file = tmp_path / "verify.csv"
    np.savetxt(in_file, np.vstack(rows), delimiter=",", header="R,G,B,X,Y,Z", comments="")

    result = subprocess.run(
        CLI + ["clut", "evaluate", "--lut", str(clut_file), "--in_file", str(in_file)],
        capture_output=True,
        text=True,
        check=True,
    )

    for line in ["red alone", "green alone", "blue alone", "all"]:
        assert line in result.stdout
    assert "none measured" not in result.stdout
    all_line = next(line for line in result.stdout.splitlines() if line.strip().startswith("all"))
    assert "+0.00%   0.00%   0.0000" in all_line, "no difference from the CLUT's own columns"
