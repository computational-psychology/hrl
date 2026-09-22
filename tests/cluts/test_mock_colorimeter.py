"""Test that the MockColorimeter class behaves as expected."""

import numpy as np
import pytest

from hrl.photometer.photometer import MockColorimeter

N_TRIPLETS = 20
rng = np.random.default_rng(0)
random_triplets = [rng.random(3) for _ in range(N_TRIPLETS)]

from tests.cluts.conftest import BLACK_POINT, DEFAULT_GAMMA, PRIMARIES_MATRIX


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
    np.testing.assert_array_almost_equal(colorimeter.readTristimulus(), tristimulus, decimal=12)


@pytest.mark.parametrize("triplet", random_triplets)
def test_unequal_callable(triplet):
    # as callable: different gamma transformations per channel
    colorimeter = MockColorimeter(color_mapping=lambda r, g, b: (r**0.9, g**2.2, b**1.5))

    tristimulus = triplet ** np.array([0.9, 2.2, 1.5])

    colorimeter.current_triplet = triplet
    np.testing.assert_array_almost_equal(colorimeter.readTristimulus(), tristimulus, decimal=12)


@pytest.mark.parametrize("triplet", random_triplets)
def test_identity_array(triplet):
    # as array: 4 columns (intensity_in, R_out, G_out, B_out), identity mapping
    identity_array = np.repeat(np.linspace(0, 1, 2**8), 4).reshape(-1, 4)
    colorimeter = MockColorimeter(color_mapping=identity_array)

    colorimeter.current_triplet = triplet
    np.testing.assert_array_equal(colorimeter.readTristimulus(), triplet)


@pytest.mark.parametrize("triplet", random_triplets)
def test_identity_clut(identity_clut, triplet):
    # as full CLUT table (intensity_in, R_out, G_out, B_out, and additional 9 columns for primaries matrix)
    colorimeter = MockColorimeter(color_mapping=identity_clut)

    colorimeter.current_triplet = triplet
    np.testing.assert_allclose(colorimeter.readTristimulus(), triplet, atol=1e-12)


@pytest.mark.parametrize("triplet", random_triplets)
def test_linear_clut(linear_clut, triplet):
    # as full CLUT table (intensity_in, R_out, G_out, B_out, and additional 9 columns for primaries matrix)
    # linear: no gamma, but dark light
    colorimeter = MockColorimeter(color_mapping=linear_clut)

    colorimeter.current_triplet = triplet

    desired_tristimulus = triplet + BLACK_POINT

    np.testing.assert_allclose(colorimeter.readTristimulus(), desired_tristimulus, atol=1e-12)


@pytest.mark.parametrize("triplet", random_triplets)
def test_linear_conversion_clut(linear_conversion_clut, triplet):
    # as full CLUT table (intensity_in, R_out, G_out, B_out, and additional 9 columns for primaries matrix)
    # linear: no gamma, no dark light, but channel crosstalk
    colorimeter = MockColorimeter(color_mapping=linear_conversion_clut)

    colorimeter.current_triplet = triplet

    desired_tristimulus = PRIMARIES_MATRIX @ triplet

    np.testing.assert_allclose(colorimeter.readTristimulus(), desired_tristimulus, atol=1e-12)


@pytest.mark.parametrize("triplet", random_triplets)
def test_nonlinear_clut(nonlinear_clut, triplet):
    # as full CLUT table (intensity_in, R_out, G_out, B_out, and additional 9 columns for primaries matrix)
    # nonlinear: gamma, dark light, and channel crosstalk
    colorimeter = MockColorimeter(color_mapping=nonlinear_clut)

    colorimeter.current_triplet = triplet

    # The triplet is what the screen is driven with; the display's gamma turns that into
    # light, so the matrix applies to drive ** gamma, the input the CLUT would map there
    desired_tristimulus = PRIMARIES_MATRIX @ triplet**DEFAULT_GAMMA + BLACK_POINT

    # The CLUT holds the gamma curve at 256 inputs, as straight lines in between, so the
    # input the mock works back to is that close; most off near black, where it is steep
    np.testing.assert_allclose(colorimeter.readTristimulus(), desired_tristimulus, atol=2e-3)


@pytest.mark.parametrize("triplet", random_triplets)
def test_readLuminance(identity_clut, triplet):
    # readLuminance() should return the Y tristimulus value from readTristimulus()
    colorimeter = MockColorimeter(color_mapping=identity_clut)

    colorimeter.current_triplet = triplet
    tristimulus = colorimeter.readTristimulus()
    luminance = colorimeter.readLuminance()

    assert luminance == tristimulus[1]  # Y tristimulus value
    assert np.isclose(luminance, triplet[1])  # Y tristimulus value for identity mapping
