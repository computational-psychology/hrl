import numpy as np


def gamma_correct_grey(img, LUT):
    """Apply gamma correction to a greyscale array using a provided LUT.

    Parameters
    ----------
    img : Array[float]
        input greyscale array with values between [0.0, 1.0].
        Can be a scalar, 1D array, or 2D array.
    LUT : Array[float]
        lookup table with at least shape (N, 2), where the first column is
        input intensities and the second column is the corrected values.
        Can have more columns, which will be ignored.

    Returns
    -------
    Array[float]
        gamma-corrected greyscale array with the same shape as input.
    """
    return np.interp(img, LUT[:, 0], LUT[:, 1])


def create_lut(
    n=256,
    gamma=1.0,
    k=1.0,
    dark=0.0,
):
    """Create a parametric LUT with gamma correction and luminance scaling.

    Parameters
    ----------
    n : int, optional
        Number of entries in the LUT, by default 256.
    gamma : float, optional
        Gamma exponent for correction, by default 1.0 (identity).
    k : float, optional
        Scaling factor for luminance calculation, by default 1.0.
    dark : float, optional
        Dark luminance offset, by default 0.0.

    Returns
    -------
    Array
        with 3 columns [intensity_in, intensity_in, luminance]:
            intensity_in = intensity_in^(1/gamma)
            luminance = k * intensity_in + dark
    """
    x = np.linspace(0.0, 1.0, n)

    out = x ** (1 / gamma)

    lum = k * x**gamma + dark
    lum[0] = dark  # enforce zero row

    return np.column_stack([x, out, lum])
