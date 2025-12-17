import numpy as np
import pytest
from conftest import DEFAULT_GAMMA

from hrl.luts import gamma_correct_grey


@pytest.mark.parametrize(
    "input_intensity",
    [
        0.0,
        0.25,
        0.5,
        0.75,
        1.0,
    ],
    ids=["black", "low_grey", "mid_grey", "high_grey", "white"],
)
def test_gamma_correct_grey_no_lut(input_intensity, no_lut):
    """Test gamma correction with no_lut (gamma=1.0, k=1.0, dark=0.0)."""
    linearized_intensity = gamma_correct_grey(input_intensity, no_lut)

    # Test output is scalar
    assert np.isscalar(linearized_intensity)

    # Check expected output intensity
    assert np.array_equal(linearized_intensity, input_intensity)

    # Check expected luminance
    actual_luminance = np.interp(input_intensity, no_lut[:, 0], no_lut[:, 2])
    assert np.array_equal(actual_luminance, input_intensity)


@pytest.mark.parametrize(
    "input_intensity,expected_luminance",
    [
        (0.0, 2.0),
        (0.25, 39.5),
        (0.5, 77.0),
        (0.75, 114.5),
        (1.0, 152.0),
    ],
    ids=["black", "low_grey", "mid_grey", "high_grey", "white"],
)
def test_gamma_correct_grey_linear_lut(input_intensity, expected_luminance, linear_lut):
    """Test gamma correction with linear_lut (gamma=1.0, k=150.0, dark=2.0)."""
    linearized_intensity = gamma_correct_grey(input_intensity, linear_lut)

    # Test output is scalar
    assert np.isscalar(linearized_intensity)

    # Check expected output intensity
    assert np.array_equal(linearized_intensity, input_intensity)

    # Check expected luminance
    actual_luminance = np.interp(input_intensity, linear_lut[:, 0], linear_lut[:, 2])
    assert np.array_equal(actual_luminance, expected_luminance)


@pytest.mark.parametrize(
    "input_intensity,expected_output,expected_luminance",
    [
        (0.0, 0.0 ** (1 / DEFAULT_GAMMA), 1.0),
        (0.25, 0.25 ** (1 / DEFAULT_GAMMA), 1.0 + 150.0 * 0.25**DEFAULT_GAMMA),
        (0.5, 0.5 ** (1 / DEFAULT_GAMMA), 1.0 + 150.0 * 0.5**DEFAULT_GAMMA),
        (0.75, 0.75 ** (1 / DEFAULT_GAMMA), 1.0 + 150.0 * 0.75**DEFAULT_GAMMA),
        (1.0, 1.0 ** (1 / DEFAULT_GAMMA), 1.0 + 150.0 * 1.0**DEFAULT_GAMMA),
    ],
    ids=["black", "low_grey", "mid_grey", "high_grey", "white"],
)
def test_gamma_correct_grey_nonlinear_lut(
    input_intensity, expected_output, expected_luminance, nonlinear_lut
):
    """Test gamma correction with nonlinear_lut (gamma=2.2, k=150.0, dark=1.0)."""
    linearized_intensity = gamma_correct_grey(input_intensity, nonlinear_lut)

    # Test output is scalar
    assert np.isscalar(linearized_intensity)

    # Check expected output intensity
    assert np.allclose(linearized_intensity, expected_output)

    # Check expected luminance
    actual_luminance = np.interp(input_intensity, nonlinear_lut[:, 0], nonlinear_lut[:, 2])
    assert np.allclose(actual_luminance, expected_luminance, rtol=1e-4)
