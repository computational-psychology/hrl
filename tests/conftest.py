import numpy as np
import pytest

from hrl.luts import create_clut, create_lut

# Standard gamma exponent for all gamma-related fixtures and tests
DEFAULT_GAMMA = 2.2


@pytest.fixture
def no_lut():
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
def no_clut():
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
    dark = np.array([0.01, 0.012, 0.015])
    return create_clut(gamma=1.0, dark_chromaticity=dark, color_matrix=np.eye(3))


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
    dark = np.array([0.01, 0.012, 0.015])
    color_matrix = np.array(
        [
            [0.85, 0.05, 0.01],
            [0.03, 0.87, 0.04],
            [0.02, 0.06, 0.84],
        ]
    )
    return create_clut(gamma=DEFAULT_GAMMA, dark_chromaticity=dark, color_matrix=color_matrix)
