"""Tests for `XYZ_to_RGB`, the numerical inverse of `RGB_to_XYZ`.

There's no closed form for the full per-level model, so `XYZ_to_RGB` seeds
from `XYZ_to_RGB_single_matrix` and refines with Gauss-Newton steps against
`RGB_to_XYZ`. See `docs/calibration/xyz_from_clut` for the worked example
this was promoted from.
"""

from pathlib import Path

import numpy as np

from hrl.cluts import RGB_to_XYZ, XYZ_to_RGB

TEST_DIR = Path(__file__).parent


def test_recovers_known_rgb_from_its_own_forward_prediction():
    """Generate a target XYZ from a known RGB, then solve backward -- should
    recover (close to) the original RGB."""
    clut = np.genfromtxt(TEST_DIR / "clut_8bit.csv", delimiter=",", skip_header=1)

    true_rgb = np.array([0.6, 0.4, 0.5])
    xyz_target = RGB_to_XYZ(true_rgb, clut)[0]

    solved_rgb = XYZ_to_RGB(xyz_target, clut)

    np.testing.assert_allclose(solved_rgb[0], true_rgb, atol=1e-2)


def test_solution_actually_reproduces_target_xyz():
    """Regardless of how close the solved RGB is to any particular 'true'
    RGB, it should reproduce the target XYZ closely when run forward."""
    clut = np.genfromtxt(TEST_DIR / "clut_8bit.csv", delimiter=",", skip_header=1)

    xyz_target = RGB_to_XYZ(np.array([0.5, 0.6, 0.4]), clut)[0]
    solved_rgb = XYZ_to_RGB(xyz_target, clut)
    xyz_achieved = RGB_to_XYZ(solved_rgb, clut)[0]

    np.testing.assert_allclose(xyz_achieved, xyz_target, atol=1e-2)


def test_accepts_batch_of_targets():
    clut = np.genfromtxt(TEST_DIR / "clut_8bit.csv", delimiter=",", skip_header=1)

    true_rgb = np.array([[0.2, 0.8, 0.5], [0.7, 0.3, 0.3]])
    xyz_targets = RGB_to_XYZ(true_rgb, clut)

    solved_rgb = XYZ_to_RGB(xyz_targets, clut)

    assert solved_rgb.shape == (2, 3)
    np.testing.assert_allclose(solved_rgb, true_rgb, atol=1e-2)


def test_output_is_clipped_to_gamut():
    """An unreachable target (e.g. way outside the display's gamut) should
    still return a finite, in-[0, 1] result rather than diverging."""
    clut = np.genfromtxt(TEST_DIR / "clut_8bit.csv", delimiter=",", skip_header=1)

    unreachable_xyz = np.array([1e6, 1e6, 1e6])
    solved_rgb = XYZ_to_RGB(unreachable_xyz, clut)

    assert np.all(np.isfinite(solved_rgb))
    assert np.all(solved_rgb >= 0.0) and np.all(solved_rgb <= 1.0)


def test_matches_reference_on_real_clut():
    """On the real CLUT where the single-matrix seed is a rougher
    approximation, the refined solve should still land very close to the
    known-true RGB."""
    real_clut_path = TEST_DIR.parents[1] / "docs" / "calibration" / "VIEWPixx3D_20260808.clut.csv"
    if not real_clut_path.exists():
        import pytest

        pytest.skip(f"Real CLUT fixture not found: {real_clut_path}")

    clut = np.genfromtxt(real_clut_path, delimiter=",", skip_header=1)

    true_rgb = np.array([0.6, 0.4, 0.5])
    xyz_target = RGB_to_XYZ(true_rgb, clut)[0]

    solved_rgb = XYZ_to_RGB(xyz_target, clut)

    np.testing.assert_allclose(solved_rgb[0], true_rgb, atol=1e-3)
