"""Fixtures for the CLUT tests: CLUTs, and a simulated display to measure."""

import numpy as np
import pytest

from hrl.cluts import create_clut

# Standard gamma exponent for all gamma-related fixtures and tests
DEFAULT_GAMMA = 2.2
DARK_CHROMATICITY = np.array([0.01, 0.012, 0.015])
COLOR_MATRIX = np.array(
    [
        [0.85, 0.05, 0.01],
        [0.03, 0.87, 0.04],
        [0.02, 0.06, 0.84],
    ]
)


@pytest.fixture
def identity_clut():
    """Simple pass-through CLUT with no gamma correction and no dark chromaticity.

    Returns
    -------
    Array
        with 13 columns [intensity_in, R_out, G_out, B_out, 9 matrix values].
        R_out = G_out = B_out = intensity_in^(1/1.0) = intensity_in.
        Dark chromaticity: zeros. Color matrix: identity.
    """
    return create_clut(gamma=1.0, dark_chromaticity=np.zeros(3), color_matrix=np.eye(3))


@pytest.fixture
def linear_clut():
    """Linear CLUT with no gamma correction, with dark chromaticity and identity color matrix.

    Returns
    -------
    Array
        with 13 columns [intensity_in, R_out, G_out, B_out, 9 matrix values].
        R_out = G_out = B_out = intensity_in^(1/1.0) = intensity_in.
        Dark chromaticity: small nonzero values. Color matrix: identity.
    """
    return create_clut(gamma=1.0, dark_chromaticity=DARK_CHROMATICITY, color_matrix=np.eye(3))


@pytest.fixture
def linear_conversion_clut():
    """Linear CLUT with channel crosstalk, no gamma correction, no dark chromaticity.

    Returns
    -------
    Array
        with 13 columns [intensity_in, R_out, G_out, B_out, 9 matrix values].
        R_out = G_out = B_out = intensity_in^(1/1.0) = intensity_in.
        Dark chromaticity: zeroes. Color matrix: simulates channel crosstalk.
    """
    return create_clut(gamma=1.0, dark_chromaticity=np.zeros(3), color_matrix=COLOR_MATRIX)


@pytest.fixture
def nonlinear_clut():
    """Nonlinear CLUT with gamma correction, dark chromaticity and channel crosstalk.

    Returns
    -------
    Array
        with 13 columns [intensity_in, R_out, G_out, B_out, 9 matrix values].
        R_out = G_out = B_out = intensity_in^(1/2.2).
        Dark chromaticity: small nonzero values. Color matrix: simulates channel crosstalk.
    """
    return create_clut(
        gamma=DEFAULT_GAMMA, dark_chromaticity=DARK_CHROMATICITY, color_matrix=COLOR_MATRIX
    )
