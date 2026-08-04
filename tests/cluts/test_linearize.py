"""Tests for hrl.cluts.linearize."""

import numpy as np

from hrl.cluts import _setup_rgb_triplets, linearize

GAMMA_PHYS = np.array([2.0, 2.2, 1.8])
COLOR_MATRIX = np.array(
    [
        [0.80, 0.05, 0.02],
        [0.03, 0.90, 0.04],
        [0.02, 0.05, 0.88],
    ]
)
DARK_XYZ = np.array([0.01, 0.012, 0.015])


def _make_measurements(n_steps=256):
    triplets = _setup_rgb_triplets(n_steps=n_steps, n_samples=1)
    linear_rgb = triplets**GAMMA_PHYS
    xyz = linear_rgb @ COLOR_MATRIX.T + DARK_XYZ
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
            x ** (1.0 / GAMMA_PHYS[0]),
            x ** (1.0 / GAMMA_PHYS[1]),
            x ** (1.0 / GAMMA_PHYS[2]),
        ]
    )

    np.testing.assert_allclose(clut[:, 1:4], expected, atol=8e-3)


def test_linearize_recovers_dark_and_color_matrix():
    measurements = _make_measurements(256)
    clut = linearize(measurements, bit_depth=8)

    np.testing.assert_allclose(np.diag(clut[0, 4:13].reshape(3, 3)), DARK_XYZ, atol=1e-12)
    np.testing.assert_allclose(clut[-1, 4:13].reshape(3, 3), COLOR_MATRIX, atol=5e-3)
