"""Tests for `neutral_RGB`, the input for a grey of a chosen luminance."""

import numpy as np
import pytest

from hrl.cluts import RGB_to_XYZ, achromatic_RGB, create_clut
from tests.cluts.conftest import DISPLAY_GAMMA, PRIMARIES_MATRIX

# The black point here is bluish, unlike the display's white, so it tints equal inputs
CLUT = create_clut(
    n=256,
    gamma=DISPLAY_GAMMA,
    primaries_matrix=100.0 * PRIMARIES_MATRIX,
    black_point=np.array([0.2, 0.2, 0.6]),
)


def _xy(xyz):
    return xyz[:2] / xyz.sum()


@pytest.mark.parametrize("luminance", [5.0, 30.0, 70.0])
def test_has_the_requested_luminance_and_the_white_chromaticity(luminance):
    white = RGB_to_XYZ(np.ones(3), CLUT, per_level=True)

    shown = RGB_to_XYZ(achromatic_RGB(CLUT, luminance, per_level=True), CLUT, per_level=True)

    assert shown[1] == pytest.approx(luminance, abs=1e-9)
    np.testing.assert_allclose(_xy(shown), _xy(white), atol=1e-12)


def test_full_white_luminance_gives_full_input():
    white = RGB_to_XYZ(np.ones(3), CLUT, per_level=True)

    np.testing.assert_allclose(
        achromatic_RGB(CLUT, white[1], per_level=True), np.ones(3), atol=1e-9
    )


def test_is_not_equal_inputs_when_the_black_point_is_tinted():
    """Equal inputs would add the black point's tint; the grey has to correct for it."""
    rgb = achromatic_RGB(CLUT, 30.0, per_level=True)

    assert np.ptp(rgb) > 1e-3
