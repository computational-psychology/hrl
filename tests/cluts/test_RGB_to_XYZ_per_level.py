"""Tests for `RGB_to_XYZ` (per level), the color a display shows for given input RGB."""

from pathlib import Path

import numpy as np
import pytest

from hrl.cluts import RGB_to_XYZ
from tests.cluts.conftest import BLACK_POINT, DISPLAY_CLUT, PRIMARIES_MATRIX

TEST_DIR = Path(__file__).parent

PARAMETRIC = DISPLAY_CLUT

FIXTURES = {
    name: np.genfromtxt(TEST_DIR / name, delimiter=",", skip_header=1)
    for name in ["clut_8bit.csv", "clut_10bit.csv"]
}


def test_parametric_display_through_its_CLUT_is_linear():
    """With its CLUT applied, a parametric display's light is a straight line in the input."""
    rgb = np.random.default_rng(0).uniform(0.0, 1.0, size=(500, 3))

    np.testing.assert_allclose(
        RGB_to_XYZ(rgb, PARAMETRIC, per_level=True),
        BLACK_POINT + rgb @ PRIMARIES_MATRIX.T,
        atol=1e-9,
    )


@pytest.mark.parametrize("name", sorted(FIXTURES))
def test_one_channel_on_reads_its_own_columns(name):
    """At a tabulated input, one channel on its own shows what its columns record."""
    clut = FIXTURES[name]

    for channel in range(3):
        rgb = np.zeros((len(clut), 3))
        rgb[:, channel] = clut[:, 0]
        np.testing.assert_allclose(
            RGB_to_XYZ(rgb, clut, per_level=True),
            clut[:, 4 + 3 * channel : 7 + 3 * channel],
            atol=1e-9,
        )


def test_between_tabulated_inputs_it_reads_along_a_straight_line():
    clut = FIXTURES["clut_8bit.csv"]
    lower, upper = clut[100, 0], clut[101, 0]

    rgb = np.array([[lower, 0, 0], [(lower + upper) / 2, 0, 0], [upper, 0, 0]])
    xyz = RGB_to_XYZ(rgb, clut, per_level=True)

    np.testing.assert_allclose(xyz[1], (xyz[0] + xyz[2]) / 2, atol=1e-12)


def test_channels_add_up():
    """The model's one assumption: the color is black plus what each channel adds."""
    clut = FIXTURES["clut_8bit.csv"]
    rgb = np.array([0.3, 0.6, 0.45])
    black = RGB_to_XYZ(np.zeros(3), clut, per_level=True)

    alone = [
        RGB_to_XYZ(np.where(np.arange(3) == c, rgb, 0.0), clut, per_level=True) for c in range(3)
    ]

    np.testing.assert_allclose(
        RGB_to_XYZ(rgb, clut, per_level=True), black + sum(a - black for a in alone), atol=1e-12
    )


def test_agrees_with_the_primaries_matrix_when_primaries_are_fixed():
    """For a display whose primaries keep their color, both ways of reading it agree."""
    rgb = np.random.default_rng(2).uniform(0.0, 1.0, size=(500, 3))
    by_matrix = RGB_to_XYZ(rgb, PARAMETRIC)

    np.testing.assert_allclose(RGB_to_XYZ(rgb, PARAMETRIC, per_level=True), by_matrix, atol=1e-9)


def test_follows_a_primary_whose_color_drifts():
    """Per level, each input gets the color recorded for it, where one matrix cannot."""
    clut = PARAMETRIC.copy()
    clut[:, 9] += 10.0 * clut[:, 0] ** 2  # green gains Z as its input goes up
    rgb = np.column_stack([np.zeros(256), clut[:, 0], np.zeros(256)])

    np.testing.assert_allclose(RGB_to_XYZ(rgb, clut, per_level=True), clut[:, 7:10], atol=1e-9)

    by_matrix = RGB_to_XYZ(rgb, clut)
    assert np.abs(by_matrix[:, 2] - clut[:, 9]).max() > 1.0
