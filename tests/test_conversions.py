import numpy as np
import pytest

from hrl.cluts import RGB_to_XYZ, XYZ_from_CLUT, XYZ_to_RGB, invert_color_matrix
from hrl.luts import grey_to_lum, lum_conversion_from_LUT, lum_to_grey


@pytest.mark.parametrize(
    "grey,k,dark",
    [
        (0.0, 50.0, 0.5),
        (0.25, 120.0, 1.5),
        (0.75, 10.0, 0.0),
        (1.0, 200.0, 2.0),
    ],
)
def test_luminance_conversion_roundtrip_scalar(grey, k, dark):
    lum = grey_to_lum(grey, k, dark)
    grey_back = lum_to_grey(lum, k, dark)
    np.testing.assert_allclose(grey_back, grey, atol=1e-12)


@pytest.mark.parametrize(
    "shape,k,dark",
    [
        ((2, 3), 50.0, 0.5),
        ((4, 1), 120.0, 1.5),
    ],
)
def test_luminance_conversion_roundtrip_array(shape, k, dark):
    rng = np.random.default_rng(hash((shape, k, dark)) % (2**32))
    grey = rng.uniform(0.0, 1.0, size=shape)
    lum = grey_to_lum(grey, k, dark)
    grey_back = lum_to_grey(lum, k, dark)
    np.testing.assert_allclose(grey_back, grey, atol=1e-12)


@pytest.mark.parametrize(
    "k,dark,n_points",
    [
        (100.0, 2.0, 10),
        (75.0, 0.5, 6),
        (150.0, 5.0, 12),
    ],
)
def test_lum_conversion_from_LUT(k, dark, n_points):
    # LUT columns: [linearized_input, output, luminance]
    # Convention: first row must be zero-intensity with luminance = dark
    x = np.linspace(0.0, 1.0, n_points)
    out = x  # corrected output intensities
    lum = k * x + dark
    lum[0] = dark  # ensure zero row encodes the dark luminance
    lut = np.column_stack([x, out, lum])

    conversion, dark_lum = lum_conversion_from_LUT(lut)

    np.testing.assert_allclose(conversion, k, atol=1e-12)
    np.testing.assert_allclose(dark_lum, dark, atol=1e-12)


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
    invM = invert_color_matrix(M)

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
            np.array([[0.01, 0.02, 0.03], [0.04, 0.05, 0.06], [0.07, 0.08, 0.09]]),
        ),
        (
            np.eye(3) * 0.8,
            np.array([[0.0, 0.0, 0.0], [0.02, 0.0, 0.01], [0.0, 0.03, 0.0]]),
        ),
    ],
)
def test_XYZ_from_CLUT(M, dark):
    x = np.linspace(0.0, 1.0, 5)
    rgb = np.column_stack([x, x, x])

    rows = []
    for i, xi in enumerate(x):
        if i == 0:
            mat = dark
        elif i == len(x) - 1:
            mat = M
        else:
            mat = np.zeros((3, 3))
        row = np.concatenate([[xi], rgb[i], mat.reshape(-1)])
        rows.append(row)
    CLUT = np.vstack(rows)

    color_matching_matrix, dark_chromaticity = XYZ_from_CLUT(CLUT)

    np.testing.assert_allclose(color_matching_matrix, M, atol=1e-12)
    np.testing.assert_allclose(dark_chromaticity, dark, atol=1e-12)


@pytest.mark.parametrize(
    "dark",
    [
        np.array([[0.1, 0.0, 0.0], [0.0, 0.2, 0.0], [0.0, 0.0, 0.3]]),
        np.array([[0.0, 0.05, 0.0], [0.01, 0.0, 0.02], [0.0, 0.0, 0.0]]),
    ],
)
def test_RGB_to_XYZ_adds_dark_chromaticity(dark):
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
def test_XYZ_to_RGB_subtracts_dark_chromaticity(dark):
    M = np.eye(3)
    invM = invert_color_matrix(M)
    sub_vec = dark.sum(axis=0)
    rgb = np.array([[[0.3, 0.2, 0.1]]])
    xyz = rgb + sub_vec
    rgb_back = XYZ_to_RGB(xyz, invM, dark)
    np.testing.assert_allclose(rgb_back, rgb, atol=1e-12)
