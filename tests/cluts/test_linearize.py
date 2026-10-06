"""Tests for hrl.cluts.linearize."""

from pathlib import Path

import numpy as np
import pytest

from hrl.cluts.calibrate import (
    average,
    linearize,
    make_monotonic,
    remove_outliers,
    smooth,
)
from hrl.cluts.triplets import channel_sweeps
from tests.cluts.conftest import BLACK_POINT, DISPLAY_GAMMA, PRIMARIES_MATRIX, display_xyz

TEST_DIR = Path(__file__).parent


def _make_measurements(n_steps=256):
    triplets = channel_sweeps(n_steps)
    xyz = display_xyz(triplets)
    return np.column_stack([triplets, xyz])


def test_linearize_output_shape_and_ranges():
    measurements = _make_measurements(256)
    clut = linearize(measurements, bit_depth=8)

    assert clut.shape == (2**8, 13)
    assert np.all(clut[:, 0] >= 0.0) and np.all(clut[:, 0] <= 1.0)
    assert np.all(clut[:, 1:4] >= 0.0) and np.all(clut[:, 1:4] <= 1.0)


def test_linearize_outputs_monotonic_per_channel():
    measurements = _make_measurements(256)
    clut = linearize(measurements, bit_depth=8)

    assert np.all(np.diff(clut[:, 1]) >= 0.0)
    assert np.all(np.diff(clut[:, 2]) >= 0.0)
    assert np.all(np.diff(clut[:, 3]) >= 0.0)


def test_linearize_recovers_expected_gamma_mapping():
    measurements = _make_measurements(256)
    clut = linearize(measurements, bit_depth=8)

    x = clut[:, 0]
    expected = np.column_stack(
        [
            x ** (1.0 / DISPLAY_GAMMA[0]),
            x ** (1.0 / DISPLAY_GAMMA[1]),
            x ** (1.0 / DISPLAY_GAMMA[2]),
        ]
    )

    np.testing.assert_allclose(clut[:, 1:4], expected, atol=8e-3)


def test_linearize_records_each_channel_measured_alone():
    """Each channel's columns hold the XYZ with only that channel on.

    At input 0 that is the black screen, for all three channels. Above it, for a display
    with fixed primaries like this one, it is black plus the input times the channel's
    primary: linearized, the channel's light goes up in a straight line.
    """
    measurements = _make_measurements(256)
    clut = linearize(measurements, bit_depth=8)

    x = clut[:, 0]
    for channel in range(3):
        alone = clut[:, 4 + 3 * channel : 7 + 3 * channel]
        np.testing.assert_allclose(alone[0], BLACK_POINT, atol=1e-12)
        expected = BLACK_POINT + x[:, None] * PRIMARIES_MATRIX[:, channel]
        np.testing.assert_allclose(alone, expected, atol=5e-3)


def _processed_measurements():
    """The fixture measurements after `remove_outliers`, `average`, `smooth` and
    `make_monotonic`.

    The CLUT fixtures are what the documented pipeline produces, smoothing included, so a
    regression test has to start from the same place.
    """
    measurements = np.genfromtxt(TEST_DIR / "measurements_8bit.csv", skip_header=1, delimiter=",")
    return make_monotonic(smooth(average(remove_outliers(measurements))))


def test_linearize_8bit_regression():
    """Regression: 8-bit CLUT matches known-good fixture."""
    result = linearize(_processed_measurements(), bit_depth=8)
    expected = np.genfromtxt(TEST_DIR / "clut_8bit.csv", skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result, expected, decimal=10)


def test_linearize_10bit_regression():
    """Regression: 10-bit CLUT matches known-good fixture."""
    result = linearize(_processed_measurements(), bit_depth=10)
    expected = np.genfromtxt(TEST_DIR / "clut_10bit.csv", skip_header=1, delimiter=",")
    np.testing.assert_array_almost_equal(result, expected, decimal=10)


def test_linearize_refuses_a_channel_whose_luminance_goes_down():
    measurements = _make_measurements(256)
    green = np.flatnonzero((measurements[:, 1] > 0.5) & (measurements[:, 0] == 0.0))[0]
    measurements[green, 4] -= 10.0  # one green reading darker than the one before it

    with pytest.raises(ValueError, match="G channel's luminance goes down"):
        linearize(measurements, bit_depth=8)


def test_input_0_drives_every_channel_at_0_when_its_curve_starts_flat():
    """A display gives no measurable light at its lowest drive values: the first row is black."""
    measurements = _make_measurements(256)
    channel_alone = (measurements[:, :3] > 0).sum(axis=1) == 1
    first_steps = channel_alone & (measurements[:, :3].max(axis=1) <= 4 / 255)
    measurements[first_steps, 3:] = BLACK_POINT  # flat at black up to drive 4/255

    clut = linearize(make_monotonic(average(measurements)), bit_depth=8)

    np.testing.assert_array_equal(clut[0, 1:4], 0.0)
    np.testing.assert_allclose(clut[0, 4:13], np.tile(BLACK_POINT, 3))
