"""Tests for `smooth`, which averages each channel's measurements over neighbouring levels."""

import numpy as np

from hrl.cluts.calibrate import average, smooth
from hrl.cluts.triplets import channel_sweeps
from tests.cluts.conftest import display_xyz


def _measurements(noise=0.0, seed=0, n_samples=1):
    triplets = np.repeat(channel_sweeps(256), n_samples, axis=0)
    xyz = 100.0 * display_xyz(triplets)
    if noise:
        rng = np.random.default_rng(seed)
        xyz = xyz * (1.0 + rng.normal(0.0, noise, size=xyz.shape))
    return average(np.column_stack([triplets, xyz]))


def test_width_one_changes_nothing():
    measurements = _measurements()

    np.testing.assert_array_equal(smooth(measurements, width=1), measurements)


def test_leaves_the_input_triplets_alone():
    measurements = _measurements(noise=0.05)

    got = smooth(measurements, width=5)

    np.testing.assert_array_equal(got[:, :3], measurements[:, :3])


def test_leaves_the_black_reading_as_measured():
    """Black belongs to all three channels' ramps, so it is not overwritten by any."""
    measurements = _measurements(noise=0.05)
    black = np.all(measurements[:, :3] == 0.0, axis=1)

    got = smooth(measurements, width=5)

    np.testing.assert_array_equal(got[black], measurements[black])


def test_a_noiseless_ramp_is_barely_changed():
    """Smoothing a smooth curve should not move it much.

    It does move it a little, because a gamma curve is curved and a boxcar cuts
    corners, most where the curve bends most.
    """
    measurements = _measurements()

    got = smooth(measurements, width=5)

    shift = np.abs(got[:, 3:] - measurements[:, 3:]).max()
    assert shift < 0.01 * measurements[:, 3:].max()


def test_reduces_noise():
    clean = _measurements()
    noisy = _measurements(noise=0.05, seed=1)

    before = np.abs(noisy[:, 3:] - clean[:, 3:]).std()
    after = np.abs(smooth(noisy, width=5)[:, 3:] - clean[:, 3:]).std()

    assert after < before
