"""Tests for calibration.measurement.measure_lut using MockPhotometer."""

import types
from pathlib import Path

import numpy as np
import pytest

from hrl.calibration.measurement import measure_lut
from hrl.luts import create_lut
from hrl.photometer.mock import MockPhotometer

TEST_DIR = Path(__file__).parent


@pytest.fixture
def mock_hrl():
    """Mock a minimal HRL object stand-in.

    No actual graphics or inputs; mock photometer to simulate luminance readings based on a LUT.

    Factory fixture: call mock_hrl(lut) to get a minimal hrl stand-in.

    Recorded rows are available as ihrl._recorded after measure_lut returns:
    each entry is a dict with keys 'Intensity', 'Luminance0', 'Luminance1', ...
    """

    def _make(lut):
        ihrl = types.SimpleNamespace()
        ihrl.photometer = MockPhotometer(lut=lut)

        # Mock results recording: measure_lut writes to ihrl.results
        # and calls ihrl.writeResultLine() to record a row.
        ihrl.results = {}
        ihrl._recorded = []
        ihrl.writeResultLine = lambda: ihrl._recorded.append(dict(ihrl.results))

        # Mock graphics and inputs to have the same interface as the real HRL object, but do nothing.
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

    measure_lut(ihrl, intensities=lut[:, 1], stim_draw_func=mock_draw, n_samples=n_samples)

    assert len(ihrl._recorded) == len(lut)

    recorded_intensities = np.array([row["Intensity"] for row in ihrl._recorded])
    np.testing.assert_array_equal(recorded_intensities, lut[:, 1])

    # Each luminance sample should match the LUT value for that intensity
    for i in range(n_samples):
        recorded_luminances = np.array([row[f"Luminance{i}"] for row in ihrl._recorded])
        np.testing.assert_array_equal(recorded_luminances, lut[:, -1])
