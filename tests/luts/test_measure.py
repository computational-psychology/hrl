"""Tests for hrl.lut.measure using MockPhotometer."""

from pathlib import Path

import numpy as np
import pytest

from hrl.luts import create_lut, measure
from tests.luts.conftest import mock_draw

TEST_DIR = Path(__file__).parent


# LUT configurations: (n, gamma, k, dark, id)
_LUT_CASES = [
    pytest.param(128, 2.2, 100.0, 1.0, id="n128-gamma2.2"),
    pytest.param(256, 2.2, 100.0, 1.0, id="n256-gamma2.2"),
    pytest.param(1024, 2.2, 100.0, 1.0, id="n1024-gamma2.2"),
    pytest.param(64, 2.0, 120.0, 2.5, id="n64-gamma2.0-lumrange"),
]


@pytest.mark.parametrize("n_samples", [1, 3, 5])
@pytest.mark.parametrize("n,gamma,k,dark", _LUT_CASES)
def test_measure(n, gamma, k, dark, n_samples, mock_hrl):
    lut = create_lut(n=n, gamma=gamma, k=k, dark=dark)
    ihrl = mock_hrl(lut)

    measurements = measure(
        ihrl, intensities=np.repeat(lut[:, 1], n_samples), stim_draw_func=mock_draw
    )

    assert len(measurements) == len(lut) * n_samples
    np.testing.assert_array_equal(measurements[:, 0], np.repeat(lut[:, 1], n_samples))

    # Each luminance sample should match the LUT value for that intensity
    np.testing.assert_array_equal(measurements[:, 1], np.repeat(lut[:, -1], n_samples))


@pytest.mark.parametrize("n_samples", [1, 3])  # skip large n_samples for speed
@pytest.mark.parametrize("n,gamma,k,dark", _LUT_CASES)
def test_csv_output(n, gamma, k, dark, n_samples, mock_hrl, tmp_path):
    lut = create_lut(n=n, gamma=gamma, k=k, dark=dark)
    ihrl = mock_hrl(lut)
    out_file = tmp_path / "measurements.csv"

    measure(
        ihrl,
        intensities=np.repeat(lut[:, 1], n_samples),
        stim_draw_func=mock_draw,
        out_file=out_file,
    )

    measurements = np.genfromtxt(out_file, delimiter=",", skip_header=1)

    assert len(measurements) == len(lut) * n_samples
    np.testing.assert_array_equal(measurements[:, 0], np.repeat(lut[:, 1], n_samples))

    # Each luminance sample should match the LUT value for that intensity
    np.testing.assert_array_equal(measurements[:, 1], np.repeat(lut[:, -1], n_samples))
