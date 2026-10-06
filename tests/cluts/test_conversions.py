import numpy as np
import pytest

from hrl.cluts import RGB_to_XYZ, XYZ_from_CLUT, XYZ_to_RGB, create_clut, invert_primaries_matrix


@pytest.mark.parametrize(
    "seed,shape",
    [
        (0, (4, 5, 3)),
        (1, (2, 3, 3)),
    ],
)
def test_XYZ_RGB_conversion_roundtrip_image(seed, shape):
    rng = np.random.default_rng(seed)
    M = rng.random((3, 3))
    invM = invert_primaries_matrix(M)

    dark = np.zeros((3, 3))
    rgb = rng.random(shape)

    xyz = RGB_to_XYZ(rgb, M, dark)
    rgb_back = XYZ_to_RGB(xyz, invM, dark)

    np.testing.assert_allclose(rgb_back, rgb, rtol=1e-12, atol=1e-12)


@pytest.mark.parametrize(
    "M,dark",
    [
        (
            np.array([[0.9, 0.1, 0.0], [0.2, 0.7, 0.1], [0.0, 0.3, 0.8]]),
            np.array([0.01, 0.02, 0.03]),
        ),
        (np.eye(3) * 0.8, np.array([0.0, 0.02, 0.01])),
    ],
)
def test_XYZ_from_CLUT(M, dark):
    CLUT = create_clut(n=5, gamma=1.0, primaries_matrix=M, black_point=dark)

    color_matching_matrix, black_point = XYZ_from_CLUT(CLUT)

    np.testing.assert_allclose(color_matching_matrix, M, atol=1e-12)
    np.testing.assert_allclose(black_point, np.diag(dark), atol=1e-12)


@pytest.mark.parametrize(
    "dark",
    [
        np.array([[0.1, 0.0, 0.0], [0.0, 0.2, 0.0], [0.0, 0.0, 0.3]]),
        np.array([[0.0, 0.05, 0.0], [0.01, 0.0, 0.02], [0.0, 0.0, 0.0]]),
    ],
)
def test_RGB_to_XYZ_adds_black_point(dark):
    M = np.eye(3)
    add_vec = dark.sum(axis=0)
    rgb = np.array([[[0.2, 0.4, 0.6]]])
    xyz = RGB_to_XYZ(rgb, M, dark)
    np.testing.assert_allclose(xyz, rgb + add_vec, atol=1e-12)


@pytest.mark.parametrize(
    "dark",
    [
        np.array([[0.05, 0.01, 0.02], [0.0, 0.03, 0.0], [0.0, 0.0, 0.04]]),
        np.array([[0.0, 0.0, 0.0], [0.02, 0.0, 0.01], [0.0, 0.03, 0.0]]),
    ],
)
def test_XYZ_to_RGB_subtracts_black_point(dark):
    M = np.eye(3)
    invM = invert_primaries_matrix(M)
    sub_vec = dark.sum(axis=0)
    rgb = np.array([[[0.3, 0.2, 0.1]]])
    xyz = rgb + sub_vec
    rgb_back = XYZ_to_RGB(xyz, invM, dark)
    np.testing.assert_allclose(rgb_back, rgb, atol=1e-12)
