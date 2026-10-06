"""Tests for `_monotonic`, and `make_monotonic` which applies it to measurements."""

import numpy as np
import pytest

from hrl.cluts.calibrate import _monotonic, average, channel_sweeps, make_monotonic
from tests.cluts.conftest import display_xyz


def test_already_monotone_is_unchanged():
    x = np.array([0.0, 1.0, 2.0, 5.0, 5.0, 9.0])
    np.testing.assert_allclose(_monotonic(x), x)


def test_single_dip_is_averaged():
    # 3,1 -> both become 2
    np.testing.assert_allclose(_monotonic([0.0, 3.0, 1.0, 4.0]), [0.0, 2.0, 2.0, 4.0])


def test_output_is_always_non_decreasing():
    rng = np.random.default_rng(0)
    for _ in range(200):
        x = rng.normal(size=rng.integers(2, 300))
        y = _monotonic(x)
        assert np.all(np.diff(y) >= -1e-12), "not monotone"
        assert len(y) == len(x)


def test_preserves_the_mean():
    rng = np.random.default_rng(1)
    for _ in range(50):
        x = rng.normal(size=100)
        np.testing.assert_allclose(_monotonic(x).mean(), x.mean(), atol=1e-12)


def test_is_the_least_squares_monotone_fit():
    """Beat it with any other non-decreasing curve and it is not the closest."""
    rng = np.random.default_rng(2)
    for _ in range(50):
        x = rng.normal(size=40)
        y = _monotonic(x)
        best = ((y - x) ** 2).sum()
        for _ in range(200):
            cand = np.sort(y + rng.normal(0, 0.1, size=40))
            assert ((cand - x) ** 2).sum() >= best - 1e-9


def test_decreasing_input_becomes_the_mean():
    x = np.array([5.0, 4.0, 3.0, 2.0, 1.0])
    np.testing.assert_allclose(_monotonic(x), np.full(5, 3.0))


def _noisy_measurements(noise=0.06, seed=3):
    """Channel-isolated readings with noise, black included, as `average` returns them."""
    triplets = channel_sweeps(64)
    xyz = 100.0 * display_xyz(triplets)
    xyz = xyz + np.random.default_rng(seed).normal(0.0, noise, size=xyz.shape) * np.maximum(
        xyz, 1.0
    )
    return average(np.column_stack([triplets, xyz]))


def _ramp(measurements, channel):
    """One channel's rows, black first, in order of its input."""
    others = [index for index in range(3) if index != channel]
    rows = measurements[np.all(measurements[:, others] == 0.0, axis=1)]
    return rows[np.argsort(rows[:, channel])]


def test_no_channel_gets_darker_as_its_input_goes_up():
    result = make_monotonic(_noisy_measurements())

    for channel in range(3):
        assert np.all(np.diff(_ramp(result, channel)[:, 3:], axis=0) >= 0.0), channel


def test_no_reading_is_darker_than_black():
    measurements = _noisy_measurements()
    black = measurements[np.all(measurements[:, :3] == 0.0, axis=1), 3:][0]

    result = make_monotonic(measurements)

    assert np.all(result[:, 3:] >= black)


def test_leaves_the_inputs_and_the_black_reading_alone():
    measurements = _noisy_measurements()
    black = np.all(measurements[:, :3] == 0.0, axis=1)

    result = make_monotonic(measurements)

    np.testing.assert_array_equal(result[:, :3], measurements[:, :3])
    np.testing.assert_array_equal(result[black], measurements[black])


def test_leaves_monotonic_measurements_as_they_are():
    measurements = make_monotonic(_noisy_measurements())

    np.testing.assert_allclose(make_monotonic(measurements), measurements, atol=1e-12)


def test_needs_a_black_reading():
    measurements = _noisy_measurements()
    lit = ~np.all(measurements[:, :3] == 0.0, axis=1)

    with pytest.raises(ValueError, match="no reading at RGB"):
        make_monotonic(measurements[lit])
