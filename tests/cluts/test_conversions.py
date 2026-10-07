import numpy as np
import pytest

from hrl.cluts import RGB_to_XYZ, XYZ_to_RGB, create_clut, primaries_from_CLUT


@pytest.mark.parametrize("seed,shape", [(0, (3,)), (1, (5, 3)), (2, (4, 5, 3))])
def test_XYZ_RGB_conversion_roundtrip(seed, shape):
    """One triplet, a list of them, or an image: the same shape back."""
    rng = np.random.default_rng(seed)
    M = np.eye(3) + 0.2 * rng.random((3, 3))
    CLUT = create_clut(n=256, gamma=2.2, primaries_matrix=M, black_point=0.05 * rng.random(3))
    rgb = rng.random(shape)

    xyz = RGB_to_XYZ(rgb, CLUT)
    rgb_back = XYZ_to_RGB(xyz, CLUT)

    assert xyz.shape == shape
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
def test_primaries_from_CLUT(M, dark):
    CLUT = create_clut(n=5, gamma=1.0, primaries_matrix=M, black_point=dark)

    color_matching_matrix, black_point = primaries_from_CLUT(CLUT)

    np.testing.assert_allclose(color_matching_matrix, M, atol=1e-12)
    np.testing.assert_allclose(black_point, dark, atol=1e-12)


@pytest.mark.parametrize("dark", [np.array([0.1, 0.2, 0.3]), np.array([0.0, 0.05, 0.02])])
def test_RGB_to_XYZ_adds_black_point(dark):
    CLUT = create_clut(n=256, gamma=1.0, primaries_matrix=np.eye(3), black_point=dark)
    rgb = np.array([0.2, 0.4, 0.6])

    np.testing.assert_allclose(RGB_to_XYZ(rgb, CLUT), rgb + dark, atol=1e-12)


@pytest.mark.parametrize("dark", [np.array([0.05, 0.03, 0.04]), np.array([0.02, 0.0, 0.03])])
def test_XYZ_to_RGB_subtracts_black_point(dark):
    CLUT = create_clut(n=256, gamma=1.0, primaries_matrix=np.eye(3), black_point=dark)
    rgb = np.array([0.3, 0.2, 0.1])

    np.testing.assert_allclose(XYZ_to_RGB(rgb + dark, CLUT), rgb, atol=1e-12)
