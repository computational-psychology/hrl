"""Tests for calibration.measurement.measure_lut using MockPhotometer."""

import types
from pathlib import Path

import numpy as np
import pytest

from hrl.calibration.measurement import measure_lut
from hrl.luts import create_lut
from hrl.photometer.photometer import MockPhotometer

TEST_DIR = Path(__file__).parent


@pytest.fixture
def mock_hrl():
    """Mock a minimal HRL object stand-in.

    No actual graphics or inputs; mock photometer to simulate luminance readings based on a LUT.

    Factory fixture: call mock_hrl(lut) to get a minimal hrl stand-in.
    """

    def _make(lut):
        ihrl = types.SimpleNamespace()
        ihrl.photometer = MockPhotometer(luminance_mapping=lut)
        ihrl.graphics = types.SimpleNamespace(gamma_correct=lambda x: x)
        ihrl.inputs = None
        return ihrl

    return _make


def mock_draw(ihrl, intensity):
    """Draw stub: updates photometer's current_intensity instead of actually drawing to screen."""
    intensity_out = ihrl.graphics.gamma_correct(intensity)
    ihrl.photometer.current_intensity = intensity_out


# LUT configurations: (n, gamma, k, dark, id)
_LUT_CASES = [
    pytest.param(128, 2.2, 100.0, 1.0, id="n128-gamma2.2"),
    pytest.param(256, 2.2, 100.0, 1.0, id="n256-gamma2.2"),
    pytest.param(1024, 2.2, 100.0, 1.0, id="n1024-gamma2.2"),
    pytest.param(64, 2.0, 120.0, 2.5, id="n64-gamma2.0-lumrange"),
]


@pytest.mark.parametrize("n_samples", [1, 3, 5])
@pytest.mark.parametrize("n,gamma,k,dark", _LUT_CASES)
def test_measure_lut(n, gamma, k, dark, n_samples, mock_hrl):
    lut = create_lut(n=n, gamma=gamma, k=k, dark=dark)
    ihrl = mock_hrl(lut)

    measurements = measure_lut(
        ihrl, intensities=lut[:, 1], stim_draw_func=mock_draw, n_samples=n_samples
    )

    assert len(measurements) == len(lut)
    np.testing.assert_array_equal(measurements[:, 0], lut[:, 1])

    # Each luminance sample should match the LUT value for that intensity
    for i in range(n_samples):
        np.testing.assert_array_equal(measurements[:, i + 1], lut[:, -1])


@pytest.mark.parametrize("n_samples", [1, 3])  # skip large n_samples for speed
@pytest.mark.parametrize("n,gamma,k,dark", _LUT_CASES)
def test_csv_output(n, gamma, k, dark, n_samples, mock_hrl, tmp_path):
    lut = create_lut(n=n, gamma=gamma, k=k, dark=dark)
    ihrl = mock_hrl(lut)
    out_file = tmp_path / "measurements.csv"

    measure_lut(
        ihrl,
        intensities=lut[:, 1],
        stim_draw_func=mock_draw,
        n_samples=n_samples,
        out_file=out_file,
    )

    measurements = np.genfromtxt(out_file, delimiter=",", skip_header=1)

    assert len(measurements) == len(lut)
    np.testing.assert_array_equal(measurements[:, 0], lut[:, 1])

    # Each luminance sample should match the LUT value for that intensity
    for i in range(n_samples):
        np.testing.assert_array_equal(measurements[:, i + 1], lut[:, -1])
