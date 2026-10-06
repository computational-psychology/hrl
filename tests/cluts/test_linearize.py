"""Tests for hrl.cluts.linearize."""

import numpy as np

from hrl.cluts.calibrate import channel_sweeps, linearize
from tests.cluts.conftest import BLACK_POINT, DISPLAY_GAMMA, PRIMARIES_MATRIX, display_xyz


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
