"""Color LookUp table (CLUT) utilities for gamma correction and color correction.

HRL uses CLUTs to perform gamma correction on color images,
mapping input intensities to linearized output intensities.
This module provides functions to create and apply these CLUTs.

The Color LUTs map input R, G, B intensities to linearized RGB values
and provide a color transformation matrix for each intensity level.
These CLUTs are structured as 2D NumPy arrays with thirteen columns:
0: `intensity_in`: Input intensities (ranging between [0.0, 1.0])
1-3: `R_out`, `G_out`, `B_out`: Gamma-corrected output RGB values
4-12: 3x3 color transformation (RGB -> XYZ) matrix values, flattened row-wise:
    [X_R, X_G, X_B, Y_R, Y_G, Y_B, Z_R, Z_G, Z_B]

Generally, these CLUTs are created through measurement of a display
and linearization of the resulting measurements.
This can be done using the `hrl-util`, documented elsewhere.
Here, we do provide a function to create parametric CLUTs
based on standard gamma correction formulas
-- this is useful for testing and simulation, but should not be used
for real display characterization!


Functions
---------
gamma_correct_RGB(img, CLUT)
    Apply gamma correction to an RGB array using a provided color LUT.
create_clut(n=256, gamma=[1.0, 1.0, 1.0], color_matrix=None, dark_chromaticity=None)
    Create a parametric CLUT with gamma correction and color conversion.

"""

import numpy as np


def gamma_correct_RGB(img, CLUT):
    """Apply gamma correction to an RGB array using a provided color LUT.

    Parameters
    ----------
    img : Array[float]
        input RGB array with values between [0.0, 1.0].
        Can be a single RGB triplet (shape: (1, 1, 3)) or an RGB image (shape: (H, W, 3)).
    CLUT : Array[float]
        Color LookUp Table with at least shape (N, 4), where the first column is
        input intensities and the next three columns are the corrected R, G, B values.
        Can have more columns, which will be ignored.

    Returns
    -------
    Array[float]
        gamma-corrected RGB array with the same shape as input.
    """
    # Apply interpolation per channel
    linearized_RGB = np.array(
        [
            np.interp(img[..., channel], CLUT[:, 0], CLUT[:, channel + 1])
            for channel in range(img.shape[-1])
        ]
    )

    # Move channel axis from first to last position
    # For (1, 1, 3) input: (3, 1, 1) -> (1, 1, 3)
    # For (H, W, 3) input: (3, H, W) -> (H, W, 3)
    linearized_RGB = np.moveaxis(linearized_RGB, 0, -1)

    return linearized_RGB


def XYZ_from_CLUT(CLUT):
    """Extract CIE 1931 XYZ color matching functions from a provided Color LUT.

    Parameters
    ----------
    CLUT : Array[float]
        Color Lookup Table with shape (N, 13), where
        the first column is linear input intensities between [0.0, 1.0],
        the next three columns are the corrected R, G, B values [0.0, 1.0],
        and the last 3x3 columns are the CIE 1931 X, Y, Z values for each channel.

    Returns
    -------
    Array[float]
        color matrix (XYZ CIE 1931 from RGB) with shape (3, 3).
    """
    color_matrix = CLUT[-1, 4:13].reshape(3, 3)
    dark_chromaticity = CLUT[0, 4:13].reshape((3, 3))

    return color_matrix, dark_chromaticity


def RGB_to_XYZ(img, color_matrix, dark_chromaticity=np.zeros((3, 3))):
    """Convert RGB image to CIE 1931 XYZ color space using provided color matching functions.

    Parameters
    ----------
    img : Array[float]
        RGB image with values between [0.0, 1.0].
        Shape: (H, W, 3).
    color_matrix : Array[float]
        color matrix (XYZ CIE 1931 from RGB) with shape (3, 3).
    dark_chromaticity : Array[float], optional
        dark chromaticity values for each channel with shape (3, 3), by default: None

    Returns
    -------
    Array[float]
        XYZ CIE 1931 image with shape (H, W, 3).
    """
    # Reshape image to (H*W, 3) for matrix multiplication
    H, W, _ = img.shape
    img_reshaped = img.reshape(-1, 3)

    # Convert RGB to XYZ
    XYZ_reshaped = img_reshaped @ color_matrix.T

    # Add dark chromaticity
    XYZ_reshaped += dark_chromaticity.sum(axis=0)

    # Reshape back to (H, W, 3)
    XYZ = XYZ_reshaped.reshape(H, W, 3)

    return XYZ


def invert_color_matrix(XYZ_from_RGB_matrix):
    """Compute the inverse of a color matching matrix.

    Parameters
    ----------
    XYZ_from_RGB_matrix : Array[float]
        color matrix (XYZ CIE 1931 from RGB) with shape (3, 3).

    Returns
    -------
    Array[float]
        inverted color matrix (RGB from XYZ CIE 1931) with shape (3, 3).
    """
    return np.linalg.inv(XYZ_from_RGB_matrix)


def XYZ_to_RGB(XYZ, inv_color_matrix, dark_chromaticity=np.zeros((3, 3))):
    """Convert CIE 1931 XYZ image to RGB color space using provided inverse color matching functions.

    Parameters
    ----------
    XYZ : Array[float]
        XYZ CIE 1931 image with shape (H, W, 3).
    inv_color_matrix : Array[float]
        inverse color matrix (RGB from XYZ CIE 1931) with shape (3, 3).
    dark_chromaticity : Array[float], optional
        dark chromaticity values for each channel with shape (3, 3), by default: None

    Returns
    -------
    Array[float]
        RGB image with values between [0.0, 1.0] and shape (H, W, 3).
    """
    # Reshape image to (H*W, 3) for matrix multiplication
    H, W, _ = XYZ.shape
    XYZ_reshaped = XYZ.reshape(-1, 3)

    # Subtract dark chromaticity
    XYZ_reshaped -= dark_chromaticity.sum(axis=0)

    # Convert XYZ to RGB
    RGB_reshaped = XYZ_reshaped @ inv_color_matrix.T

    # Reshape back to (H, W, 3)
    RGB = RGB_reshaped.reshape(H, W, 3)

    return RGB


def create_clut(
    n=256,
    gamma=[1.0, 1.0, 1.0],
    color_matrix=None,
    dark_chromaticity=None,
):
    """Create a parametric CLUT with gamma correction and color conversion.

    Parameters
    ----------
    n : int, optional
        number of entries in the CLUT, by default 256.
    gamma : [float, float, float] or float, optional
        gamma exponents for R, G, B correction, by default [1.0, 1.0, 1.0].
    color_matrix : Array, optional
        3x3 color transformation matrix, by default identity (XYZ=RGB).
    dark_chromaticity : Array, optional
        3-element vector for dark state chromaticity (XYZ at black), by default zeros (no dark light).

    Returns
    -------
    Array
        with 13 columns [intensity_in, R_out, G_out, B_out, 9 matrix values]:
            R_out, G_out, B_out = intensity_in^(1/gamma[i]) for each channel
            First row's 3x3 matrix represents dark_chromaticity as the black point
            Last row's 3x3 matrix is color_matrix
            Intermediate rows linearly interpolate between dark and full color
    """
    if dark_chromaticity is None:
        dark_chromaticity = np.zeros(3)
    if color_matrix is None:
        color_matrix = np.eye(3)
    if isinstance(gamma, (int, float)):
        gamma = [gamma, gamma, gamma]

    x = np.linspace(0.0, 1.0, n)
    corrected = [x ** (1 / g) for g in gamma]
    rgb = np.column_stack(corrected)

    # RGB->XYZ matrices per entry: linearly interpolate from dark to full color
    # At x=0: dark chromaticity as diagonal (simplified representation)
    # At x=1: full color_matrix
    dark_matrix = np.diag(dark_chromaticity)
    matrices = x[:, None, None] * (color_matrix - dark_matrix) + dark_matrix
    matrices_flat = matrices.reshape(n, -1)

    # Combine all columns
    return np.column_stack([x, rgb, matrices_flat])
