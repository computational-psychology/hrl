"""Tests for the single-matrix RGB<->XYZ approximation.

`RGB_to_XYZ_single_matrix` / `XYZ_to_RGB_single_matrix` are calibrated
against raw input RGB directly (no gamma correction needed)
"""

from pathlib import Path

import numpy as np

from hrl.cluts import RGB_to_XYZ, RGB_to_XYZ_single_matrix, XYZ_to_RGB_single_matrix

TEST_DIR = Path(__file__).parent


def test_forward_and_inverse_round_trip():
    clut = np.genfromtxt(TEST_DIR / "clut_8bit.csv", delimiter=",", skip_header=1)

    rgb = np.array([0.3, 0.6, 0.45])
    xyz = RGB_to_XYZ_single_matrix(rgb, clut)
    rgb_back = XYZ_to_RGB_single_matrix(xyz, clut)

    np.testing.assert_allclose(rgb_back[0], rgb, atol=1e-8)


def test_accepts_batch_of_triplets():
    clut = np.genfromtxt(TEST_DIR / "clut_8bit.csv", delimiter=",", skip_header=1)

    rgb = np.array([[0.1, 0.2, 0.3], [0.5, 0.5, 0.5], [0.9, 0.1, 0.4]])
    xyz = RGB_to_XYZ_single_matrix(rgb, clut)
    assert xyz.shape == (3, 3)

    rgb_back = XYZ_to_RGB_single_matrix(xyz, clut)
    np.testing.assert_allclose(rgb_back, rgb, atol=1e-8)


def test_matches_full_model_at_full_scale():
    """At the full-scale row, the single-matrix prediction must exactly
    match the full per-level model (both are calibrated from the same
    endpoint)."""
    clut = np.genfromtxt(TEST_DIR / "clut_8bit.csv", delimiter=",", skip_header=1)

    white = np.array([1.0, 1.0, 1.0])
    xyz_single_matrix = RGB_to_XYZ_single_matrix(white, clut)
    xyz_full = RGB_to_XYZ(white, clut)

    np.testing.assert_allclose(xyz_single_matrix, xyz_full, atol=1e-6)


def test_is_a_good_approximation_of_the_full_model():
    """On a CLUT where per-channel luminance is close to linear in input
    level (by `linearize`'s construction), this single matrix should track
    the full per-level model closely."""
    clut = np.genfromtxt(TEST_DIR / "clut_8bit.csv", delimiter=",", skip_header=1)

    gray_levels = np.linspace(0.0, 1.0, 100)
    red = np.column_stack([gray_levels, np.zeros_like(gray_levels), np.zeros_like(gray_levels)])

    Y_full = RGB_to_XYZ(red, clut)[:, 1]
    Y_single_matrix = RGB_to_XYZ_single_matrix(red, clut)[:, 1]

    max_rel_error = np.max(np.abs(Y_single_matrix - Y_full)) / (Y_full.max() - Y_full.min())
    assert max_rel_error < 0.05
