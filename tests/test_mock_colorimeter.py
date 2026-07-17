"""Test that the MockColorimeter class behaves as expected."""

import numpy as np
import pytest

from hrl.cluts import RGB_to_XYZ, gamma_correct_RGB
from hrl.photometer.photometer import MockColorimeter

N_TRIPLETS = 20
rng = np.random.default_rng(0)
random_triplets = [rng.random(3) for _ in range(N_TRIPLETS)]

from conftest import COLOR_MATRIX, DARK_CHROMATICITY, DEFAULT_GAMMA


@pytest.mark.parametrize("triplet", random_triplets)
def test_identity_callable(triplet):
    # as callable: identity: tristimulus == RGB
    colorimeter = MockColorimeter(color_mapping=lambda r, g, b: (r, g, b))

    colorimeter.current_triplet = triplet
    np.testing.assert_array_equal(colorimeter.readTristimulus(), triplet)


@pytest.mark.parametrize("triplet", random_triplets)
def test_equal_callable(triplet):
    # as callable: single gamma transformation for all channels
    colorimeter = MockColorimeter(color_mapping=lambda r, g, b: (r**2.2, g**2.2, b**2.2))

    tristimulus = triplet**2.2

    colorimeter.current_triplet = triplet
    np.testing.assert_array_equal(colorimeter.readTristimulus(), tristimulus)


@pytest.mark.parametrize("triplet", random_triplets)
def test_unequal_callable(triplet):
    # as callable: different gamma transformations per channel
    colorimeter = MockColorimeter(color_mapping=lambda r, g, b: (r**0.9, g**2.2, b**1.5))

    tristimulus = triplet ** np.array([0.9, 2.2, 1.5])

    colorimeter.current_triplet = triplet
    np.testing.assert_array_equal(colorimeter.readTristimulus(), tristimulus)


@pytest.mark.parametrize("triplet", random_triplets)
def test_identity_array(triplet):
    # as array: 4 columns (intensity_in, R_out, G_out, B_out), identity mapping
    identity_array = np.repeat(np.linspace(0, 1, 2**8), 4).reshape(-1, 4)
    colorimeter = MockColorimeter(color_mapping=identity_array)

    colorimeter.current_triplet = triplet
    np.testing.assert_array_equal(colorimeter.readTristimulus(), triplet)


@pytest.mark.parametrize("triplet", random_triplets)
def test_identity_clut(identity_clut, triplet):
    # as full CLUT table (intensity_in, R_out, G_out, B_out, and additional 9 columns for color matrix)
    colorimeter = MockColorimeter(color_mapping=identity_clut)

    colorimeter.current_triplet = triplet
    np.testing.assert_array_equal(colorimeter.readTristimulus(), triplet)


@pytest.mark.parametrize("triplet", random_triplets)
def test_linear_clut(linear_clut, triplet):
    # as full CLUT table (intensity_in, R_out, G_out, B_out, and additional 9 columns for color matrix)
    # linear: no gamma, but dark light
    colorimeter = MockColorimeter(color_mapping=linear_clut)

    colorimeter.current_triplet = triplet

    desired_tristimulus = RGB_to_XYZ(
        triplet.reshape((1, 1, 3)),
        color_matrix=np.eye(3),
        dark_chromaticity=np.diag(DARK_CHROMATICITY),
    ).flatten()

    np.testing.assert_array_equal(colorimeter.readTristimulus(), desired_tristimulus)


@pytest.mark.parametrize("triplet", random_triplets)
def test_linear_conversion_clut(linear_conversion_clut, triplet):
    # as full CLUT table (intensity_in, R_out, G_out, B_out, and additional 9 columns for color matrix)
    # linear: no gamma, no dark light, but channel crosstalk
    colorimeter = MockColorimeter(color_mapping=linear_conversion_clut)

    colorimeter.current_triplet = triplet

    desired_tristimulus = RGB_to_XYZ(
        triplet.reshape((1, 1, 3)), color_matrix=COLOR_MATRIX, dark_chromaticity=np.zeros(3)
    ).flatten()

    np.testing.assert_array_equal(colorimeter.readTristimulus(), desired_tristimulus)


@pytest.mark.parametrize("triplet", random_triplets)
def test_nonlinear_clut(nonlinear_clut, triplet):
    # as full CLUT table (intensity_in, R_out, G_out, B_out, and additional 9 columns for color matrix)
    # nonlinear: gamma, dark light, and channel crosstalk
    colorimeter = MockColorimeter(color_mapping=nonlinear_clut)

    colorimeter.current_triplet = triplet

    # compute desired tristimulus using the nonlinear CLUT
    gamma_corrected = gamma_correct_RGB(triplet.reshape((1, 1, 3)), nonlinear_clut)
    desired_tristimulus = RGB_to_XYZ(
        gamma_corrected,
        color_matrix=COLOR_MATRIX,
        dark_chromaticity=np.diag(DARK_CHROMATICITY),
    ).flatten()

    np.testing.assert_array_equal(colorimeter.readTristimulus(), desired_tristimulus)


@pytest.mark.parametrize("triplet", random_triplets)
def test_readLuminance(identity_clut, triplet):
    # readLuminance() should return the Y tristimulus value from readTristimulus()
    colorimeter = MockColorimeter(color_mapping=identity_clut)

    colorimeter.current_triplet = triplet
    tristimulus = colorimeter.readTristimulus()
    luminance = colorimeter.readLuminance()

    assert luminance == tristimulus[1]  # Y tristimulus value
    assert np.isclose(luminance, triplet[1])  # Y tristimulus value for identity mapping
