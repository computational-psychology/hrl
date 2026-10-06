"""Tests for `differences`: how far measured colors are from expected ones."""

import numpy as np
import pytest

from hrl.cluts import differences


def test_the_same_color_differs_by_nothing():
    xyz = np.array([[30.0, 40.0, 50.0], [1.0, 2.0, 0.5]])

    np.testing.assert_allclose(differences(xyz, xyz), 0.0, atol=1e-15)


def test_a_brighter_color_of_the_same_chromaticity_differs_in_luminance_only():
    expected = np.array([30.0, 40.0, 50.0])

    xyz, luminance, chromaticity = differences(1.02 * expected, expected)

    assert luminance == pytest.approx(0.02)
    assert chromaticity < 1e-15
    np.testing.assert_allclose(xyz, 0.02 * np.linalg.norm(expected))


def test_a_tint_at_the_same_luminance_differs_in_chromaticity_only():
    expected = np.array([30.0, 40.0, 50.0])
    measured = expected + np.array([2.0, 0.0, -2.0])

    xyz, luminance, chromaticity = differences(measured, expected)

    assert luminance == 0.0
    assert chromaticity > 0.01
    np.testing.assert_allclose(xyz, np.sqrt(8.0))


def test_keeps_the_shape_but_the_last_axis():
    rng = np.random.default_rng(0)
    measured, expected = rng.uniform(1, 2, size=(4, 5, 3)), rng.uniform(1, 2, size=(4, 5, 3))

    assert differences(measured, expected).shape == (4, 5, 3)
    assert differences(measured[0, 0], expected[0, 0]).shape == (3,)
