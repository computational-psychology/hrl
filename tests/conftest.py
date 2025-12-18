import pytest

from hrl.luts import create_lut

# Standard gamma exponent for all gamma-related fixtures and tests
DEFAULT_GAMMA = 2.2


@pytest.fixture
def no_lut():
    """Simple pass-through LUT with no gamma correction and no dark luminance.

    Returns
    -------
    Array
        with 3 columns [intensity_in, intensity_in, luminance].
        intensity_in = intensity_in^(1/1.0) = intensity_in.
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
        with 3 columns [intensity_in, intensity_in, luminance].
        intensity_in = intensity_in^(1/1.0) = intensity_in.
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
        with 3 columns [intensity_in, intensity_in, luminance].
        intensity_in = intensity_in^(1/2.2).
        luminance = 150.0 * intensity_in^2.2 + 1.0.
        First row is zero-intensity with dark luminance = 1.0.
    """
    return create_lut(gamma=DEFAULT_GAMMA, k=150.0, dark=1.0)
