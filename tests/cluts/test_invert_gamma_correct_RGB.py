import numpy as np
import pytest

from hrl.cluts import gamma_correct_RGB, invert_gamma_correct_RGB


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
@pytest.mark.parametrize(
    "clut_fixture", ["identity_clut", "linear_clut", "nonlinear_clut"]
)
def test_invert_gamma_correct_RGB_round_trip_triplet(input_RGB, clut_fixture, request):
    """Inverting a gamma-corrected triplet should recover the original input."""
    clut = request.getfixturevalue(clut_fixture)
    rgb_triplet = np.reshape(input_RGB, (1, 1, 3))

    drive = gamma_correct_RGB(rgb_triplet, clut)
    recovered = invert_gamma_correct_RGB(drive, clut)

    assert recovered.shape == (1, 1, 3)
    assert np.allclose(recovered.flatten(), np.array(input_RGB), atol=1e-3)


@pytest.mark.parametrize(
    "shape",
    [(5, 5), (10, 8), (1, 1), (50, 50)],
    ids=["small_square", "rectangular", "single_pixel", "large_square"],
)
def test_invert_gamma_correct_RGB_round_trip_img(shape, nonlinear_clut):
    """Inverting a gamma-corrected image should recover the original input."""
    seed = hash(shape) % (2**32)
    rng = np.random.default_rng(seed)
    rgb_img = rng.uniform(0, 1, size=(*shape, 3))

    drive = gamma_correct_RGB(rgb_img, nonlinear_clut)
    recovered = invert_gamma_correct_RGB(drive, nonlinear_clut)

    assert recovered.shape == (*shape, 3)
    assert np.allclose(recovered, rgb_img, atol=1e-2)


def test_invert_gamma_correct_RGB_single_flat_triplet(nonlinear_clut):
    """Also accepts a flat (3,) triplet, matching `gamma_correct_RGB`'s shape handling."""
    x = np.array([0.3, 0.6, 0.9])
    drive = gamma_correct_RGB(x, nonlinear_clut)
    recovered = invert_gamma_correct_RGB(drive, nonlinear_clut)

    assert recovered.shape == (3,)
    assert np.allclose(recovered, x, atol=1e-3)
