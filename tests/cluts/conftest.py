"""Fixtures for the CLUT tests: CLUTs, and a simulated display to measure."""

import types

import numpy as np
import pytest

from hrl.cluts import create_clut
from hrl.photometer.photometer import MockColorimeter

# Standard gamma exponent for all gamma-related fixtures and tests
DEFAULT_GAMMA = 2.2
BLACK_POINT = np.array([0.01, 0.012, 0.015])
PRIMARIES_MATRIX = np.array(
    [
        [0.80, 0.05, 0.02],
        [0.03, 0.90, 0.04],
        [0.02, 0.05, 0.88],
    ]
)

# The simulated display measured in tests: each channel has a gamma of its own, so
# that mixing them up shows, and the primaries matrix and black point above
DISPLAY_GAMMA = np.array([2.0, 2.2, 1.8])


def display_xyz(rgb):
    """The CIE XYZ the simulated display shows for input RGB, shape (..., 3)."""
    return np.asarray(rgb, dtype=float) ** DISPLAY_GAMMA @ PRIMARIES_MATRIX.T + BLACK_POINT


@pytest.fixture
def mock_hrl():
    """A minimal stand-in for HRL, whose colorimeter reads the simulated display.

    Factory fixture: ``mock_hrl()`` gives the stand-in; `noise` and `rng` go to
    `MockColorimeter`.
    """

    def _make(noise=0.0, rng=None):
        ihrl = types.SimpleNamespace()
        ihrl.photometer = MockColorimeter(
            color_mapping=lambda r, g, b: tuple(display_xyz([r, g, b])), noise=noise, rng=rng
        )
        ihrl.graphics = types.SimpleNamespace(gamma_correct=lambda x: x)
        ihrl.inputs = None
        return ihrl

    return _make


def mock_draw(ihrl, triplet):
    """Draw stub: sets the colorimeter's current triplet instead of drawing to screen."""
    ihrl.photometer.current_triplet = np.asarray(ihrl.graphics.gamma_correct(triplet), dtype=float)


@pytest.fixture
def identity_clut():
    """Simple pass-through CLUT with no gamma correction and no Black point.

    Returns
    -------
    Array
        with 13 columns [intensity_in, R_out, G_out, B_out, 9 matrix values].
        R_out = G_out = B_out = intensity_in^(1/1.0) = intensity_in.
        Black point: zeros. Primaries matrix: identity.
    """
    return create_clut(gamma=1.0, black_point=np.zeros(3), primaries_matrix=np.eye(3))


@pytest.fixture
def linear_clut():
    """Linear CLUT with no gamma correction, with black point and identity primaries matrix.

    Returns
    -------
    Array
        with 13 columns [intensity_in, R_out, G_out, B_out, 9 matrix values].
        R_out = G_out = B_out = intensity_in^(1/1.0) = intensity_in.
        Black point: small nonzero values. Primaries matrix: identity.
    """
    return create_clut(gamma=1.0, black_point=BLACK_POINT, primaries_matrix=np.eye(3))


@pytest.fixture
def linear_conversion_clut():
    """Linear CLUT with channel crosstalk, no gamma correction, no Black point.

    Returns
    -------
    Array
        with 13 columns [intensity_in, R_out, G_out, B_out, 9 matrix values].
        R_out = G_out = B_out = intensity_in^(1/1.0) = intensity_in.
        Black point: zeroes. Primaries matrix: simulates channel crosstalk.
    """
    return create_clut(gamma=1.0, black_point=np.zeros(3), primaries_matrix=PRIMARIES_MATRIX)


@pytest.fixture
def nonlinear_clut():
    """Nonlinear CLUT with gamma correction, Black point and channel crosstalk.

    Returns
    -------
    Array
        with 13 columns [intensity_in, R_out, G_out, B_out, 9 matrix values].
        R_out = G_out = B_out = intensity_in^(1/2.2).
        Black point: small nonzero values. Primaries matrix: simulates channel crosstalk.
    """
    return create_clut(
        gamma=DEFAULT_GAMMA, black_point=BLACK_POINT, primaries_matrix=PRIMARIES_MATRIX
    )
