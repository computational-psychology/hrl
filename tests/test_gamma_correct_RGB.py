import numpy as np
import pytest
from conftest import DEFAULT_GAMMA

from hrl.luts import gamma_correct_RGB


@pytest.mark.parametrize(
    "input_RGB",
    [
        (0.0, 0.0, 0.0),
        (0.25, 0.25, 0.25),
        (0.5, 0.5, 0.5),
        (0.75, 0.75, 0.75),
        (1.0, 1.0, 1.0),
    ],
    ids=["black", "low_grey", "mid_grey", "high_grey", "white"],
)
def test_gamma_correct_RGB_triplet_no_clut(input_RGB, no_clut):
    """Test gamma correction on RGB triplet with no_clut (gamma=1.0)."""
    rgb_triplet = np.reshape(input_RGB, (1, 1, 3))

    # Linearize RGB triplet using CLUT
    linearized_RGB = gamma_correct_RGB(rgb_triplet, no_clut)

    # Test output shape
    assert linearized_RGB.shape == (1, 1, 3)

    # Check expected output RGB (should be identity)
    expected_RGB = np.array(input_RGB)
    assert np.allclose(linearized_RGB.flatten(), expected_RGB)


@pytest.mark.parametrize(
    "input_RGB",
    [
        (0.0, 0.0, 0.0),
        (0.25, 0.25, 0.25),
        (0.5, 0.5, 0.5),
        (0.75, 0.75, 0.75),
        (1.0, 1.0, 1.0),
    ],
    ids=["black", "low_grey", "mid_grey", "high_grey", "white"],
)
def test_gamma_correct_RGB_triplet_linear_clut(input_RGB, linear_clut):
    """Test gamma correction on RGB triplet with linear_clut (gamma=1.0)."""
    rgb_triplet = np.reshape(input_RGB, (1, 1, 3))

    # Linearize RGB triplet using CLUT
    linearized_RGB = gamma_correct_RGB(rgb_triplet, linear_clut)

    # Test output shape
    assert linearized_RGB.shape == (1, 1, 3)

    # Check expected output RGB (should be identity with gamma=1.0)
    expected_RGB = np.array(input_RGB)
    assert np.allclose(linearized_RGB.flatten(), expected_RGB)


@pytest.mark.parametrize(
    "input_RGB",
    [
        (0.0, 0.0, 0.0),
        (0.25, 0.25, 0.25),
        (0.5, 0.5, 0.5),
        (0.75, 0.75, 0.75),
        (1.0, 1.0, 1.0),
    ],
    ids=["black", "low_grey", "mid_grey", "high_grey", "white"],
)
def test_gamma_correct_RGB_triplet_nonlinear_clut(input_RGB, nonlinear_clut):
    """Test gamma correction on RGB triplet with nonlinear_clut (gamma=2.2)."""
    rgb_triplet = np.reshape(input_RGB, (1, 1, 3))

    # Linearize RGB triplet using CLUT
    linearized_RGB = gamma_correct_RGB(rgb_triplet, nonlinear_clut)

    # Test output shape
    assert linearized_RGB.shape == (1, 1, 3)

    # Check expected output RGB
    expected_RGB = np.array(input_RGB) ** (1 / DEFAULT_GAMMA)
    assert np.allclose(linearized_RGB.flatten(), expected_RGB, rtol=1e-4)
