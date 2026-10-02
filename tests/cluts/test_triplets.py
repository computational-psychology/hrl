"""Tests for `hrl.cluts.triplets`: sets of RGB triplets to show and measure."""

import numpy as np
import pytest

from hrl.cluts import RGB_to_XYZ, achromatic_RGB, create_clut
from hrl.cluts.triplets import channel_mixtures, channel_sweeps, isoluminant_colors
from tests.cluts.conftest import BLACK_POINT, DISPLAY_GAMMA, PRIMARIES_MATRIX

CLUT = create_clut(
    n=256,
    gamma=DISPLAY_GAMMA,
    primaries_matrix=100.0 * PRIMARIES_MATRIX,
    black_point=100.0 * BLACK_POINT,
)
WHITE_Y = RGB_to_XYZ(np.ones(3), CLUT, per_level=True)[1]


def test_channel_sweeps_light_one_channel_at_a_time():
    triplets = channel_sweeps(8)

    assert triplets.shape == (3 * 8, 3)
    assert np.all((triplets > 0.0).sum(axis=1) <= 1)
    for channel in range(3):
        np.testing.assert_allclose(
            triplets[8 * channel : 8 * (channel + 1), channel], np.linspace(0, 1, 8)
        )


def test_channel_sweeps_takes_the_levels_themselves():
    levels = [0.0, 0.2, 0.9]

    triplets = channel_sweeps(levels)

    np.testing.assert_allclose(triplets[3:6, 1], levels)


def test_channel_mixtures_hold_every_mixture_and_the_parts_it_needs():
    levels = (0.5, 1.0)

    triplets = channel_mixtures(levels=levels)

    lit = (triplets > 0.0).sum(axis=1)
    assert len(triplets) == len(levels) ** 3 + 3 * len(levels) + 1
    assert (lit == 0).sum() == 1, "black has to be measured, to separate the black point"
    assert (lit == 1).sum() == 3 * len(levels)
    assert (lit == 3).sum() == len(levels) ** 3


def test_channel_mixtures_greys_come_with_their_parts():
    triplets = channel_mixtures(levels=(0.5, 1.0), grey_levels=[0.0, 0.25, 0.5, 0.75, 1.0])

    greys = triplets[(triplets > 0.0).all(axis=1) & (triplets == triplets[:, :1]).all(axis=1)]
    np.testing.assert_allclose(np.unique(greys[:, 0]), [0.25, 0.5, 0.75, 1.0])
    assert len(np.unique(triplets, axis=0)) == len(triplets), "each triplet once"
    for grey in np.unique(greys[:, 0]):
        for channel in range(3):
            part = np.zeros(3)
            part[channel] = grey
            assert (triplets == part).all(axis=1).any(), f"{part} not measured"


def test_background_first_then_every_direction_at_every_fraction():
    triplets = isoluminant_colors(CLUT, directions=6, fractions=(0.5, 1.0), per_level=True)

    assert triplets.shape == (1 + 6 * 2, 3)
    np.testing.assert_allclose(
        triplets[0], achromatic_RGB(CLUT, WHITE_Y / 2, per_level=True), atol=1e-12
    )


@pytest.mark.parametrize(
    "background", [None, achromatic_RGB(CLUT, 20.0, per_level=True), np.array([0.6, 0.3, 0.4])]
)
def test_every_color_has_the_background_luminance(background):
    triplets = isoluminant_colors(CLUT, background=background, per_level=True)

    Y = RGB_to_XYZ(triplets, CLUT, per_level=True)[:, 1]

    np.testing.assert_allclose(Y, Y[0], rtol=1e-9)
    if background is None:
        np.testing.assert_allclose(Y[0], WHITE_Y / 2, rtol=1e-9)


def test_colors_differ_from_the_background_and_from_each_other():
    xyz = RGB_to_XYZ(isoluminant_colors(CLUT, per_level=True), CLUT, per_level=True)

    assert len(np.unique(xyz.round(6), axis=0)) == len(xyz)
