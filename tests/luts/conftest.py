"""Fixtures for the LUT tests: LUTs, and a stand-in for HRL with a photometer."""

import types

import pytest

from hrl.luts import create_lut
from hrl.photometer.photometer import MockPhotometer

# Standard gamma exponent for all gamma-related fixtures and tests
DEFAULT_GAMMA = 2.2


@pytest.fixture
def identity_lut():
    """Simple pass-through LUT with no gamma correction and no dark luminance.

    Returns
    -------
    Array
        with 3 columns [intensity_in, intensity_out, luminance].
        intensity_out = intensity_in^(1/1.0) = intensity_in.
        luminance = 1.0 * intensity_in + 0.0 = intensity_in.
        First row is zero-intensity with dark luminance = 0.0.
    """
    return create_lut(gamma=1.0, k=1.0, dark=0.0)


@pytest.fixture
def linear_lut():
    """Linear luminance LUT with no gamma correction, scaled luminance and dark luminance.

    Returns
    -------
    Array
        with 3 columns [intensity_in, intensity_out, luminance].
        intensity_out = intensity_in^(1/1.0) = intensity_in.
        luminance = 150.0 * intensity_in + 2.0.
        First row is zero-intensity with dark luminance = 2.0.
    """
    return create_lut(gamma=1.0, k=150.0, dark=2.0)


@pytest.fixture
def nonlinear_lut():
    """Nonlinear luminance LUT with gamma correction, scaled luminance and dark luminance.

    Returns
    -------
    Array
        with 3 columns [intensity_in, intensity_out, luminance].
        intensity_out = intensity_in^(1/2.2).
        luminance = 150.0 * intensity_in^2.2 + 1.0.
        First row is zero-intensity with dark luminance = 1.0.
    """
    return create_lut(gamma=DEFAULT_GAMMA, k=150.0, dark=1.0)


@pytest.fixture
def mock_hrl():
    """A minimal stand-in for HRL, whose photometer reads luminance off a LUT.

    Factory fixture: ``mock_hrl(lut)`` gives the stand-in; `noise` and `rng` go to
    `MockPhotometer`.
    """

    def _make(lut, noise=0.0, rng=None):
        ihrl = types.SimpleNamespace()
        ihrl.photometer = MockPhotometer(luminance_mapping=lut, noise=noise, rng=rng)
        ihrl.graphics = types.SimpleNamespace(gamma_correct=lambda x: x)
        ihrl.inputs = None
        return ihrl

    return _make


def mock_draw(ihrl, intensity):
    """Draw stub: sets the photometer's current intensity instead of drawing to screen."""
    ihrl.photometer.current_intensity = ihrl.graphics.gamma_correct(intensity)
