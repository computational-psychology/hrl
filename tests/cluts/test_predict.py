"""Tests for `predict` and `predict_from_channels`: the color expected for measured inputs."""

import numpy as np
import pytest

from hrl.cluts import differences
from hrl.cluts.calibrate import predict, predict_from_channels
from hrl.cluts.triplets import channel_mixtures
from tests.cluts.conftest import BLACK_POINT, DISPLAY_CLUT, PRIMARIES_MATRIX

CLUT = DISPLAY_CLUT

# Each channel on its own, at levels between the CLUT's tabulated inputs as well as on them
LEVELS = np.random.default_rng(0).uniform(0.0, 1.0, size=20)
INPUTS = np.vstack([np.eye(3)[channel] * LEVELS[:, None] for channel in range(3)])


def _readings(inputs, scale=(1.0, 1.0, 1.0), excess=0.0):
    """What the display this CLUT describes reads, with the CLUT applied, scaled per axis.

    With its CLUT applied, a channel of this parametric display adds light in a straight
    line with its input: black plus the input times its primary. `excess` makes it emit
    that much more, relative, per lit channel beyond one: a display that does not add up.
    """
    inputs = np.asarray(inputs, dtype=float)
    added = inputs @ PRIMARIES_MATRIX.T
    lit = (inputs > 0.0).sum(axis=1)
    xyz = BLACK_POINT + added * (1.0 + excess * np.maximum(lit - 1, 0))[:, None]
    return np.column_stack([inputs, xyz * np.asarray(scale)])


# --- predict, from a CLUT -------------------------------------------------------------------


def test_a_display_the_CLUT_describes_exactly_is_predicted_exactly():
    readings = _readings(INPUTS)

    np.testing.assert_allclose(predict(readings, CLUT), readings[:, 3:], atol=1e-9)


def test_predicts_row_for_row_without_averaging():
    readings = np.vstack([_readings(INPUTS), _readings(INPUTS[:5])])

    assert predict(readings, CLUT).shape == (len(INPUTS) + 5, 3)


def test_black_is_predicted_by_the_first_row():
    np.testing.assert_allclose(predict(np.zeros((1, 3)), CLUT)[0], CLUT[0, 4:7], atol=1e-12)


def test_a_uniformly_brighter_display_differs_only_in_luminance():
    readings = _readings(INPUTS, scale=(1.02, 1.02, 1.02))

    _, luminance, chromaticity = differences(readings[:, 3:], predict(readings, CLUT)).T

    np.testing.assert_allclose(luminance, 0.02, atol=1e-9)
    np.testing.assert_allclose(chromaticity, 0.0, atol=1e-9)


def test_mixtures_of_channels_are_predicted_too():
    """For a display whose channels add up, the CLUT predicts mixtures as well."""
    readings = _readings(np.random.default_rng(1).uniform(0.0, 1.0, size=(50, 3)))

    np.testing.assert_allclose(predict(readings, CLUT), readings[:, 3:], atol=1e-9)


# --- predict_from_channels, from the measurements themselves ------------------------------------


def test_an_additive_display_is_predicted_by_its_channels():
    readings = _readings(channel_mixtures(levels=(0.25, 0.5, 1.0)))

    np.testing.assert_allclose(predict_from_channels(readings), readings[:, 3:], atol=1e-9)


def test_a_non_additive_display_is_caught_and_its_size_recovered():
    readings = _readings(channel_mixtures(levels=(0.25, 0.5, 1.0)), excess=0.04)
    mixtures = (readings[:, :3] > 0.0).sum(axis=1) == 3

    expected = predict_from_channels(readings)[mixtures]

    # Above black, since both carry the black point, and it does not scale
    excess = (readings[mixtures, 4] - expected[:, 1]) / (expected[:, 1] - BLACK_POINT[1])
    # every mixture here lights three channels, so two channels' worth of excess
    np.testing.assert_allclose(excess, 2 * 0.04, rtol=1e-9)


def test_survives_repeats_and_noise():
    triplets = np.repeat(channel_mixtures(levels=(0.25, 0.5, 1.0)), 5, axis=0)
    readings = _readings(triplets, excess=0.04)
    readings[:, 3:] *= 1.0 + np.random.default_rng(1).normal(0.0, 0.02, size=(len(readings), 3))
    mixtures = (readings[:, :3] > 0.0).sum(axis=1) == 3

    expected = predict_from_channels(readings)[mixtures]

    excess = (readings[mixtures, 4] - expected[:, 1]) / (expected[:, 1] - BLACK_POINT[1])
    assert abs(excess.mean() - 0.08) < 0.01


def test_reads_between_the_levels_a_channel_was_measured_at():
    """Like a CLUT made from this session alone: straight lines between measured levels."""
    readings = _readings(channel_mixtures(levels=(0.5, 1.0)))
    between = np.array([[0.75, 0.0, 0.0], [0.75, 0.75, 0.0]])

    predicted = predict_from_channels(np.vstack([readings, _readings(between)]))[-2:]

    halfway = (_readings([[0.5, 0, 0]]) + _readings([[1.0, 0, 0]]))[0, 3:] / 2
    np.testing.assert_allclose(predicted[0], halfway, atol=1e-9)


def test_cannot_predict_what_its_channels_were_not_measured_for():
    readings = _readings(channel_mixtures(levels=(0.5,)))
    beyond = _readings([[0.8, 0.5, 0.5]])

    predicted = predict_from_channels(np.vstack([readings, beyond]))

    assert np.isnan(predicted[-1]).all(), "red was never measured beyond 0.5"
    assert not np.isnan(predicted[:-1]).any()


def test_needs_a_black_reading():
    readings = _readings(channel_mixtures(levels=(0.5, 1.0)))
    without_black = readings[(readings[:, :3] > 0.0).any(axis=1)]

    with pytest.raises(ValueError, match="no reading at RGB"):
        predict_from_channels(without_black)
