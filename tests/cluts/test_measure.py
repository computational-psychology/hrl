"""Tests for hrl.cluts.measure using MockColorimeter."""

import types

import numpy as np
import pytest

from hrl.cluts import _setup_rgb_triplets, measure
from hrl.photometer.photometer import MockColorimeter

GAMMA_PHYS = np.array([2.0, 2.2, 1.8])
COLOR_MATRIX = np.array(
    [
        [0.80, 0.05, 0.02],
        [0.03, 0.90, 0.04],
        [0.02, 0.05, 0.88],
    ]
)
DARK_XYZ = np.array([0.01, 0.012, 0.015])


def _physical_xyz(r, g, b):
    rgb = np.array([r, g, b], dtype=float)
    linear_rgb = rgb**GAMMA_PHYS
    return tuple(linear_rgb @ COLOR_MATRIX.T + DARK_XYZ)


@pytest.fixture
def mock_hrl():
    """Factory fixture that returns a minimal HRL stand-in."""

    def _make(noise=0.0, rng=None):
        ihrl = types.SimpleNamespace()
        ihrl.photometer = MockColorimeter(color_mapping=_physical_xyz, noise=noise, rng=rng)
        ihrl.graphics = types.SimpleNamespace(gamma_correct=lambda x: x)
        ihrl.inputs = None
        return ihrl

    return _make


def mock_draw(ihrl, triplet):
    """Draw stub: updates current RGB triplet for the mock colorimeter."""
    ihrl.photometer.current_triplet = np.asarray(ihrl.graphics.gamma_correct(triplet), dtype=float)


@pytest.mark.parametrize("n_steps,n_samples", [(16, 1), (32, 2)])
def test_measure_returns_expected_xyz(n_steps, n_samples, mock_hrl):
    triplets = _setup_rgb_triplets(n_steps=n_steps, n_samples=n_samples)
    ihrl = mock_hrl(noise=0.0)

    measurements = measure(ihrl, triplets=triplets, stim_draw_func=mock_draw)

    assert measurements.shape == (len(triplets), 6)
    np.testing.assert_array_equal(measurements[:, :3], triplets)

    expected_xyz = np.array([_physical_xyz(*triplet) for triplet in triplets])
    np.testing.assert_allclose(measurements[:, 3:], expected_xyz, atol=1e-12)


def test_measure_csv_output(tmp_path, mock_hrl):
    triplets = _setup_rgb_triplets(n_steps=16, n_samples=2)
    out_file = tmp_path / "measurements.csv"
    ihrl = mock_hrl(noise=0.0)

    measure(ihrl, triplets=triplets, stim_draw_func=mock_draw, out_file=out_file)

    measured_csv = np.genfromtxt(out_file, delimiter=",", skip_header=1)
    assert measured_csv.shape == (len(triplets), 6)
    np.testing.assert_allclose(measured_csv[:, :3], triplets, atol=1e-12)


def test_setup_rgb_triplets_shape_and_isolation():
    n_steps = 8
    n_samples = 3
    triplets = _setup_rgb_triplets(n_steps=n_steps, n_samples=n_samples)

    assert triplets.shape == (3 * n_steps * n_samples, 3)

    # Channel-isolated: at most one channel is non-zero in each row.
    non_zero_channels = np.sum(triplets > 0.0, axis=1)
    assert np.all(non_zero_channels <= 1)
