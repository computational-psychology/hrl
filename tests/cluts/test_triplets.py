"""Tests for `hrl.cluts.triplets`: sets of RGB triplets to show and measure."""

import numpy as np

from hrl.cluts.triplets import channel_mixtures, channel_sweeps


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
