"""Tests for the single-matrix RGB<->XYZ approximation.

`RGB_to_XYZ_single_matrix` / `XYZ_to_RGB_single_matrix` are calibrated
against raw input RGB directly (no gamma correction needed)
"""

from pathlib import Path

import numpy as np

from hrl.cluts import RGB_to_XYZ_single_matrix, XYZ_to_RGB_single_matrix

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
