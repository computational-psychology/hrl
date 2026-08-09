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
RGB_to_XYZ(rgb, CLUT, gamma_correct=True) / XYZ_to_RGB(xyz, CLUT)
    **Recommended default** for predicting/solving RGB<->XYZ. Uses the full
    per-level CLUT forward model (the level-dependent 3x3 matrix stored in
    every CLUT row), not a single fixed matrix. `XYZ_to_RGB` has no closed
    form and refines numerically.
RGB_to_XYZ_single_matrix(rgb, CLUT) / XYZ_to_RGB_single_matrix(xyz, CLUT)
    Cheap, closed-form single-matrix approximation. Assumes the display's
    RGB->XYZ transform doesn't change with intensity level, which is untrue
    in general -- prefer `RGB_to_XYZ` / `XYZ_to_RGB` unless you have a
    specific reason to want the cheaper approximation.
apply_color_matrix(img, color_matrix, dark_chromaticity) / apply_inverse_color_matrix(...)
    Low-level: apply a color matrix you already have (not derived from a
    CLUT) to an image. `invert_color_matrix` inverts one.
create_clut(n=256, gamma=[1.0, 1.0, 1.0], color_matrix=None, dark_chromaticity=None)
    Create a parametric CLUT with gamma correction and color conversion.

"""

import numpy as np


def _as_triplets(arr):
    """Return an array with shape (N, 3)."""
    arr = np.asarray(arr, dtype=float)
    if arr.ndim == 1:
        arr = arr.reshape(1, 3)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise ValueError("Expected shape (N, 3) or (3,)")
    return arr


def _interp_unique(x, xp, fp):
    """`np.interp` wrapper that averages duplicate `xp` values before interpolating.

    CLUT rows can have repeated intensity/drive values (e.g. a clipped
    channel), which would otherwise make interpolation ill-defined.
    """
    order = np.argsort(xp)
    xp_sorted = xp[order]
    fp_sorted = fp[order]

    uniq_xp, inverse = np.unique(xp_sorted, return_inverse=True)
    if len(uniq_xp) == len(xp_sorted):
        uniq_fp = fp_sorted
    else:
        sums = np.bincount(inverse, weights=fp_sorted)
        counts = np.bincount(inverse)
        uniq_fp = sums / counts

    return np.interp(x, uniq_xp, uniq_fp)


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


def _single_matrix_from_CLUT(CLUT):
    """Extract the single-matrix RGB->XYZ approximation from a CLUT.

    Calibrated against raw input RGB directly (no gamma correction needed):
    scales the full-scale-row matrix so it's relative to input level
    (column 0) rather than drive (columns 1-3) -- see
    `RGB_to_XYZ_single_matrix` for why that distinction matters.
    """
    drive_at_full_scale = CLUT[-1, 1:4]
    intensity_in_at_full_scale = CLUT[-1, 0]
    color_matrix = CLUT[-1, 4:13].reshape(3, 3) * drive_at_full_scale / intensity_in_at_full_scale
    dark_chromaticity = CLUT[0, 4:13].reshape((3, 3))
    return color_matrix, dark_chromaticity


def apply_color_matrix(img, color_matrix, dark_chromaticity=np.zeros((3, 3))):
    """Convert an RGB image to CIE 1931 XYZ using an explicit color matrix.

    Low-level: `XYZ = img @ color_matrix.T + dark_chromaticity.sum(axis=0)`.
    Use this when you already have a color matrix from somewhere else. To
    predict what a specific, measured display shows, prefer `RGB_to_XYZ` or
    `RGB_to_XYZ_single_matrix`, which get the matrix from a CLUT for you.

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
    XYZ_reshaped = XYZ_reshaped + dark_chromaticity.sum(axis=0)

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


def apply_inverse_color_matrix(XYZ, inv_color_matrix, dark_chromaticity=np.zeros((3, 3))):
    """Convert a CIE 1931 XYZ image to RGB using an explicit inverse color matrix.

    Low-level: the inverse of `apply_color_matrix`. Use this when you
    already have an (inverse) color matrix from somewhere else. To solve
    for the RGB a specific, measured display needs, prefer `XYZ_to_RGB` or
    `XYZ_to_RGB_single_matrix`, which get the matrix from a CLUT for you.

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

    # Subtract dark chromaticity (avoid -=: reshape can return a view, and an
    # in-place op would then silently mutate the caller's XYZ array).
    XYZ_reshaped = XYZ_reshaped - dark_chromaticity.sum(axis=0)

    # Convert XYZ to RGB
    RGB_reshaped = XYZ_reshaped @ inv_color_matrix.T

    # Reshape back to (H, W, 3)
    RGB = RGB_reshaped.reshape(H, W, 3)

    return RGB


def RGB_to_XYZ_single_matrix(rgb, CLUT):
    """Predict XYZ from input-level RGB using a single-matrix approximation.

    Cheap and closed-form, and a solid approximation on a well-calibrated
    real CLUT -- but it assumes the display's RGB->XYZ transform doesn't
    change with intensity level, which is untrue in general. **Prefer
    `RGB_to_XYZ`** (the full per-level model) unless you specifically want
    the cheaper approximation.

    The matrix is calibrated against raw input RGB (CLUT column 0) directly,
    with no separate gamma-correction step needed: `linearize` constructs
    that coordinate specifically so per-channel luminance is close to linear
    in it, which is what makes a single matrix a reasonable approximation at
    all.

    Parameters
    ----------
    rgb : array-like
        Input-level RGB, shape (3,) or (N, 3).
    CLUT : Array[float]
        Color Lookup Table with shape (N, 13), see module docstring.

    Returns
    -------
    Array[float]
        XYZ values with shape (N, 3).
    """
    rgb = _as_triplets(rgb)
    color_matrix, dark_chromaticity = _single_matrix_from_CLUT(CLUT)
    xyz = apply_color_matrix(
        rgb.reshape(-1, 1, 3), color_matrix=color_matrix, dark_chromaticity=dark_chromaticity
    )
    return xyz.reshape(-1, 3)


def XYZ_to_RGB_single_matrix(xyz, CLUT):
    """Invert `RGB_to_XYZ_single_matrix` via a direct matrix inverse.

    Instant (closed-form), but inherits the single-matrix approximation's
    error -- it's what `XYZ_to_RGB` uses internally as a fast starting point
    before refining against the full model. **Prefer `XYZ_to_RGB`** unless
    you specifically want the cheaper approximation.

    Parameters
    ----------
    xyz : array-like
        Target XYZ, shape (3,) or (N, 3).
    CLUT : Array[float]
        Color Lookup Table with shape (N, 13), see module docstring.

    Returns
    -------
    Array[float]
        Input-level RGB with shape (N, 3). Not clipped to [0, 1].
    """
    xyz = _as_triplets(xyz)
    color_matrix, dark_chromaticity = _single_matrix_from_CLUT(CLUT)
    rgb = apply_inverse_color_matrix(
        xyz.reshape(-1, 1, 3),
        inv_color_matrix=invert_color_matrix(color_matrix),
        dark_chromaticity=dark_chromaticity,
    )
    return rgb.reshape(-1, 3)


def RGB_to_XYZ(rgb, CLUT, gamma_correct=True):
    """Predict XYZ from RGB using the full per-level CLUT forward model.

    **Recommended default** for predicting what a CLUT-characterized display
    shows. `RGB_to_XYZ_single_matrix` approximates the display with a single
    fixed RGB->XYZ matrix (typically the full-scale CLUT row), which is only
    correct if the display's effective color transform does not change with
    intensity level. Real displays often violate this, sometimes
    substantially at low/mid levels. This function instead uses the
    level-dependent 3x3 matrix stored in *every* CLUT row: for each channel,
    it interpolates the drive level and then the per-level XYZ contribution
    curve, summing contributions across channels plus the dark-level offset.

    Parameters
    ----------
    rgb : array-like
        RGB input(s) with values in [0.0, 1.0]. Shape (3,) or (N, 3).
    CLUT : Array[float]
        Color Lookup Table with shape (N, 13), see module docstring.
    gamma_correct : bool, optional
        If True (default), first map `rgb` through the CLUT's input->drive
        gamma correction (columns 0-3), matching `gamma_correct_RGB`. If
        False, `rgb` is treated as already being in drive space.

    Returns
    -------
    Array[float]
        XYZ values with shape (N, 3).
    """
    rgb = _as_triplets(rgb)

    intensity_in = np.asarray(CLUT[:, 0], dtype=float)
    rgb_out = np.asarray(CLUT[:, 1:4], dtype=float)
    matrices = np.asarray(CLUT[:, 4:13], dtype=float).reshape(-1, 3, 3)

    # First row stores dark chromaticity on the diagonal.
    dark_xyz = matrices[0].sum(axis=0)

    xyz = np.tile(dark_xyz, (len(rgb), 1))

    for channel in range(3):
        out_curve = rgb_out[:, channel]
        contrib_curve = out_curve[:, None] * matrices[:, :, channel]

        if gamma_correct:
            drive = _interp_unique(rgb[:, channel], intensity_in, out_curve)
        else:
            drive = rgb[:, channel]

        for dim in range(3):
            xyz[:, dim] += _interp_unique(drive, out_curve, contrib_curve[:, dim])

    return xyz


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
