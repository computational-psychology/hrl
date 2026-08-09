"""Tests for the full per-level CLUT forward model (`RGB_to_XYZ`)."""

from pathlib import Path

import numpy as np

from hrl.cluts import RGB_to_XYZ, RGB_to_XYZ_single_matrix

TEST_DIR = Path(__file__).parent
REAL_CLUT_PATH = TEST_DIR.parents[1] / "docs" / "calibration" / "VIEWPixx3D_20260808.clut.csv"


def _toy_clut():
    """Small nonlinear CLUT with intensity-dependent XYZ matrices."""
    intensity_in = np.array([0.0, 0.5, 1.0], dtype=float)
    rgb_out = np.array(
        [
            [0.0, 0.0, 0.0],
            [0.2, 0.2, 0.2],
            [1.0, 1.0, 1.0],
        ],
        dtype=float,
    )

    dark_xyz = np.array([0.2, 0.3, 0.4], dtype=float)
    matrices = np.zeros((3, 3, 3), dtype=float)
    matrices[0] = np.diag(dark_xyz)

    for i, y_scale in enumerate([30.0, 75.0], start=1):
        matrices[i] = np.array(
            [
                [0.6 * y_scale, 0.6 * y_scale, 0.6 * y_scale],
                [1.0 * y_scale, 1.0 * y_scale, 1.0 * y_scale],
                [1.4 * y_scale, 1.4 * y_scale, 1.4 * y_scale],
            ],
            dtype=float,
        )

    return np.column_stack([intensity_in, rgb_out, matrices.reshape(3, -1)])


def _manual_forward(rgb, clut, gamma_correct):
    rgb = np.asarray(rgb, dtype=float)
    intensity_in = clut[:, 0]
    rgb_out = clut[:, 1:4]
    matrices = clut[:, 4:13].reshape(-1, 3, 3)

    dark_xyz = matrices[0].sum(axis=0)
    xyz = np.tile(dark_xyz, (len(rgb), 1))

    for c in range(3):
        out_curve = rgb_out[:, c]
        contrib_curve = out_curve[:, None] * matrices[:, :, c]

        if gamma_correct:
            drive = np.interp(rgb[:, c], intensity_in, out_curve)
        else:
            drive = rgb[:, c]

        for d in range(3):
            xyz[:, d] += np.interp(drive, out_curve, contrib_curve[:, d])

    return xyz


def test_forward_model_matches_manual_reference():
    clut = _toy_clut()
    rgb = np.array([[0.0, 0.0, 0.0], [0.2, 0.5, 0.8], [1.0, 1.0, 1.0]], dtype=float)

    xyz_on = RGB_to_XYZ(rgb, clut, gamma_correct=True)
    xyz_on_ref = _manual_forward(rgb, clut, gamma_correct=True)
    np.testing.assert_allclose(xyz_on, xyz_on_ref, rtol=0, atol=1e-10)

    xyz_off = RGB_to_XYZ(rgb, clut, gamma_correct=False)
    xyz_off_ref = _manual_forward(rgb, clut, gamma_correct=False)
    np.testing.assert_allclose(xyz_off, xyz_off_ref, rtol=0, atol=1e-10)


def test_forward_model_accepts_single_triplet():
    clut = _toy_clut()
    xyz = RGB_to_XYZ(np.array([0.5, 0.5, 0.5]), clut)
    assert xyz.shape == (1, 3)


def test_forward_model_matches_single_matrix_at_full_scale():
    """At full scale (input=1), the per-level matrix *is* the single fixed matrix,
    so the two models must agree exactly there."""
    clut = np.genfromtxt(TEST_DIR / "clut_8bit.csv", delimiter=",", skip_header=1)

    white = np.array([1.0, 1.0, 1.0])
    xyz_full = RGB_to_XYZ(white, clut)
    xyz_single = RGB_to_XYZ_single_matrix(white, clut)

    np.testing.assert_allclose(xyz_full, xyz_single, atol=1e-8)


def test_forward_model_can_diverge_from_single_matrix_at_low_input():
    """On a real measured CLUT (where the display's primaries genuinely
    shift with level), the two models should disagree away from full scale
    -- otherwise the full model buys nothing. The bundled synthetic test
    fixtures are built from a level-invariant physical model, so they don't
    exhibit this; a real CLUT is needed to demonstrate it."""
    if not REAL_CLUT_PATH.exists():
        import pytest

        pytest.skip(f"Real CLUT fixture not found: {REAL_CLUT_PATH}")

    clut = np.genfromtxt(REAL_CLUT_PATH, delimiter=",", skip_header=1)

    low = np.array([0.05, 0.05, 0.05])
    xyz_full = RGB_to_XYZ(low, clut)[0]
    xyz_single = RGB_to_XYZ_single_matrix(low, clut)[0]

    assert not np.allclose(xyz_full, xyz_single, atol=1e-3)
