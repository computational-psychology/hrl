"""Integration tests for CLUT calibration pipeline: measure -> remove_outliers -> average -> linearize."""

import types
from pathlib import Path

import numpy as np

from hrl.cluts import (
    _setup_rgb_triplets,
    average,
    linearize,
    measure,
    remove_outliers,
)
from hrl.photometer.photometer import MockColorimeter

TEST_DIR = Path(__file__).parent

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


def _make_mock_hrl(noise=0.0, rng=None):
    ihrl = types.SimpleNamespace()
    ihrl.photometer = MockColorimeter(color_mapping=_physical_xyz, noise=noise, rng=rng)
    ihrl.graphics = types.SimpleNamespace(gamma_correct=lambda x: x)
    ihrl.inputs = None
    return ihrl


def _mock_draw(ihrl, triplet):
    ihrl.photometer.current_triplet = np.asarray(triplet, dtype=float)


def test_full_clut_pipeline_with_repeats_and_outliers():
    ihrl = _make_mock_hrl(noise=0.0, rng=42)
    triplets = _setup_rgb_triplets(n_steps=256, n_samples=3)

    measurements = measure(ihrl, triplets=triplets, stim_draw_func=_mock_draw)

    cleaned = remove_outliers(measurements)
    averaged = average(cleaned)
    clut = linearize(averaged, bit_depth=8)

    assert clut.shape == (256, 13)
    assert np.all(np.isfinite(clut))

    # Validate recovered gamma correction is close to the expected inverse monitor gamma.
    x = clut[:, 0]
    expected = np.column_stack(
        [
            x ** (1.0 / GAMMA_PHYS[0]),
            x ** (1.0 / GAMMA_PHYS[1]),
            x ** (1.0 / GAMMA_PHYS[2]),
        ]
    )

    np.testing.assert_allclose(clut[:, 1:4], expected, atol=8e-3)

    # Validate matrix endpoints.
    np.testing.assert_allclose(np.diag(clut[0, 4:13].reshape(3, 3)), DARK_XYZ, atol=5e-3)
    np.testing.assert_allclose(clut[-1, 4:13].reshape(3, 3), COLOR_MATRIX, atol=2e-2)


def test_pipeline_regression_from_saved_measurements():
    """Regression: saved measurements run through full pipeline to known-good CLUT."""
    measurements = np.genfromtxt(TEST_DIR / "measurements_8bit.csv", skip_header=1, delimiter=",")

    result = linearize(average(remove_outliers(measurements)), bit_depth=8)
    expected = np.genfromtxt(TEST_DIR / "clut_8bit.csv", skip_header=1, delimiter=",")

    np.testing.assert_array_almost_equal(result, expected, decimal=10)
