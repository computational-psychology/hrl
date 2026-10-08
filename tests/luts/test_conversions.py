import numpy as np
import pytest

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
