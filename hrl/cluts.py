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
invert_gamma_correct_RGB(img, CLUT)
    Invert `gamma_correct_RGB`: recover raw input RGB from drive RGB.
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
measure(ihrl, triplets, stim_draw_func, out_file, sleep_time)
    Measure CIE XYZ tristimulus values for channel-isolated RGB triplets.
remove_outliers(measurements, abs_tol=0.075, rel_tol=0.0075)
    Remove outlier tristimulus measurements within repeated RGB triplets.
average(measurements)
    Average repeated tristimulus measurements per RGB triplet.
linearize(measurements, bit_depth=8)
    Build a linearized CLUT from averaged channel-isolated measurements.
create_clut(n=256, gamma=[1.0, 1.0, 1.0], color_matrix=None, dark_chromaticity=None)
    Create a parametric CLUT with gamma correction and color conversion.

"""

from functools import partial
from pathlib import Path

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


def invert_gamma_correct_RGB(img, CLUT):
    """Invert `gamma_correct_RGB`: recover raw input RGB from drive RGB.

    Given RGB already mapped through a CLUT's input->drive gamma correction
    (columns 0-3), this recovers the original input RGB. Drive values can
    repeat across rows (e.g. a clipped/saturated channel), so this
    interpolates against a duplicate-safe version of the drive curve.

    Parameters
    ----------
    img : Array[float]
        drive RGB array with values between [0.0, 1.0].
        Can be a single RGB triplet (shape: (1, 1, 3)) or an RGB image (shape: (H, W, 3)).
    CLUT : Array[float]
        Color LookUp Table with at least shape (N, 4), where the first column is
        input intensities and the next three columns are the corrected R, G, B values.
        Can have more columns, which will be ignored.

    Returns
    -------
    Array[float]
        input RGB array with the same shape as input.
    """
    input_RGB = np.array(
        [
            _interp_unique(img[..., channel], CLUT[:, channel + 1], CLUT[:, 0])
            for channel in range(img.shape[-1])
        ]
    )

    input_RGB = np.moveaxis(input_RGB, 0, -1)

    return input_RGB


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


def XYZ_to_RGB(xyz, CLUT, tol=1e-3, max_iter=40):
    """Invert `RGB_to_XYZ`: solve for input-level RGB that reproduces a target XYZ.

    **Recommended default** for solving what RGB a CLUT-characterized
    display needs to show a target XYZ. There's no closed form for this
    (the full per-level model isn't a fixed linear map), so this refines
    numerically: seed from the instant `XYZ_to_RGB_single_matrix`
    approximation, then run Gauss-Newton steps against the exact model
    (`RGB_to_XYZ`) until the residual drops below `tol` or `max_iter` is
    reached.

    Parameters
    ----------
    xyz : array-like
        Target XYZ, shape (3,) or (N, 3).
    CLUT : Array[float]
        Color Lookup Table with shape (N, 13), see module docstring.
    tol : float, optional
        Stop refining a point once its XYZ error norm drops below this, by default 1e-3.
    max_iter : int, optional
        Maximum Gauss-Newton iterations per point, by default 40.

    Returns
    -------
    Array[float]
        Input-level RGB with shape (N, 3), each row clipped to [0, 1]. Not
        every target is reachable (the display gamut is finite) -- to check
        how well a target was actually hit, compare `RGB_to_XYZ` of the
        result against `xyz`.
    """
    xyz = _as_triplets(xyz)
    x = XYZ_to_RGB_single_matrix(xyz, CLUT)
    x = np.clip(np.nan_to_num(x, nan=0.5, posinf=1.0, neginf=0.0), 0.0, 1.0)

    for i in range(len(xyz)):
        target = xyz[i]
        xi = x[i]
        pred = RGB_to_XYZ(xi, CLUT)[0]
        err = pred - target
        err_norm = float(np.linalg.norm(err))

        for _ in range(max_iter):
            if err_norm <= tol:
                break

            eps = 1e-4
            J = np.zeros((3, 3))
            for j in range(3):
                x_up, x_dn = xi.copy(), xi.copy()
                x_up[j] = min(1.0, x_up[j] + eps)
                x_dn[j] = max(0.0, x_dn[j] - eps)
                denom = x_up[j] - x_dn[j]
                if denom == 0.0:
                    continue
                J[:, j] = (RGB_to_XYZ(x_up, CLUT)[0] - RGB_to_XYZ(x_dn, CLUT)[0]) / denom

            try:
                step = np.linalg.lstsq(J, -err, rcond=None)[0]
            except np.linalg.LinAlgError:
                break

            improved = False
            for alpha in (1.0, 0.5, 0.25, 0.125, 0.0625):
                x_candidate = np.clip(xi + alpha * step, 0.0, 1.0)
                pred_candidate = RGB_to_XYZ(x_candidate, CLUT)[0]
                err_candidate = pred_candidate - target
                err_norm_candidate = float(np.linalg.norm(err_candidate))
                if err_norm_candidate < err_norm:
                    xi, pred, err, err_norm = (
                        x_candidate,
                        pred_candidate,
                        err_candidate,
                        err_norm_candidate,
                    )
                    improved = True
                    break
            if not improved:
                break

        x[i] = xi

    return x


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


def _setup_rgb_triplets(
    i_min=0.0, i_max=1.0, n_steps=2**8, n_samples=1, shuffle=False, reverse=False
):
    """Set up channel-isolated RGB triplets for CLUT measurements.

    Generates triplets for red-only, green-only, and blue-only stimulation,
    each sweeping intensity from ``i_min`` to ``i_max``.

    Parameters
    ----------
    i_min : float, optional
        minimum channel intensity, by default 0.0
    i_max : float, optional
        maximum channel intensity, by default 1.0
    n_steps : int, optional
        number of intensity values per channel, by default 2**8
    n_samples : int, optional
        number of repeated measurements per RGB triplet, by default 1
    shuffle : bool, optional
        shuffle triplet order, by default False
    reverse : bool, optional
        reverse triplet order, by default False

    Returns
    -------
    numpy.ndarray
        array with shape ``(3 * n_steps * n_samples, 3)`` and columns ``R, G, B``
    """
    intensities = np.linspace(i_min, i_max, n_steps)

    r_triplets = np.column_stack(
        [intensities, np.zeros_like(intensities), np.zeros_like(intensities)]
    )
    g_triplets = np.column_stack(
        [np.zeros_like(intensities), intensities, np.zeros_like(intensities)]
    )
    b_triplets = np.column_stack(
        [np.zeros_like(intensities), np.zeros_like(intensities), intensities]
    )

    triplets = np.vstack([r_triplets, g_triplets, b_triplets])
    triplets = np.repeat(triplets, n_samples, axis=0)

    if shuffle:
        np.random.shuffle(triplets)
    elif reverse:
        triplets = triplets[::-1]

    return triplets


def _draw_uniform_rgb_square(ihrl, triplet, patch_size=0.5):
    """Draw a centered RGB square patch for CLUT measurements.

    Parameters
    ----------
    ihrl : HRL
        HRL instance used for drawing and flipping
    triplet : array-like
        RGB triplet in [0.0, 1.0]
    patch_size : float, optional
        size of patch as fraction of the screen, by default 0.5
    """
    screen_width, screen_height = ihrl.graphics.width, ihrl.graphics.height
    patch_width = screen_width * patch_size
    patch_height = screen_height * patch_size
    patch_position = (
        (screen_width - patch_width) / 2,
        (screen_height - patch_height) / 2,
    )
    patch = ihrl.graphics.newTexture(np.array([[triplet]], dtype=float))
    patch.draw(patch_position, (patch_width, patch_height))
    ihrl.graphics.flip()


def measure(
    ihrl,
    triplets=_setup_rgb_triplets(),
    stim_draw_func=partial(_draw_uniform_rgb_square, patch_size=0.5),
    out_file=None,
    sleep_time=200,
):
    """Measure CIE XYZ tristimulus values for a sequence of RGB triplets.

    Parameters
    ----------
    ihrl : HRL
        HRL instance with a configured colorimeter.
    triplets : array-like, optional
        RGB triplets to measure, shape ``(N, 3)``.
        Defaults to channel-isolated 8-bit sweep via ``_setup_rgb_triplets()``.
    stim_draw_func : callable, optional
        function with signature ``(ihrl, triplet)`` that draws the stimulus,
        by default a centered uniform square patch.
    out_file : str or Path, optional
        output CSV path, by default None (no file output).
    sleep_time : float, optional
        delay in ms passed to the colorimeter, by default 200.

    Returns
    -------
    numpy.ndarray
        table with columns ``R, G, B, X, Y, Z``.
    """
    triplets = np.asarray(triplets, dtype=float)
    if triplets.ndim != 2 or triplets.shape[1] != 3:
        raise ValueError("triplets must be a 2D array with shape (N, 3)")

    if out_file is not None:
        out_file = Path(out_file).expanduser().resolve()

    measurements = np.full((len(triplets), 6), np.nan, dtype=float)

    for idx_triplet, triplet in enumerate(triplets):
        print(
            "Current Triplet: "
            f"({triplet[0]:.3f}, {triplet[1]:.3f}, {triplet[2]:.3f}) "
            f"[{idx_triplet:d} of {len(triplets)} "
            f"({idx_triplet / len(triplets):.2%}%)]"
        )

        measurements[idx_triplet, :3] = triplet

        # Draw (update) stimulus
        stim_draw_func(ihrl, triplet)

        # Measure tristimulus
        xyz = ihrl.photometer.readTristimulus(5, int(sleep_time))
        measurements[idx_triplet, 3:] = xyz

        # Write measured samples to file
        if out_file is not None:
            np.savetxt(
                out_file,
                measurements,
                delimiter=",",
                header="R,G,B,X,Y,Z",
                comments="",
            )

        if ihrl.inputs is not None and ihrl.inputs.checkEscape():
            break

    return measurements


def remove_outliers(measurements, abs_tol=0.075, rel_tol=0.0075):
    """Remove outlier tristimulus measurements within repeated RGB triplets.

    Outliers are identified within each repeated RGB triplet group based on
    nearest-neighbor distance in XYZ space.

    Parameters
    ----------
    measurements : array-like
        table with columns ``R, G, B, X, Y, Z``
    abs_tol : float, optional
        absolute tolerance in XYZ Euclidean distance, by default 0.075
    rel_tol : float, optional
        relative tolerance vs. XYZ norm, by default 0.0075

    Returns
    -------
    numpy.ndarray
        measurements with outlier XYZ rows set to NaN
    """
    measurements = np.asarray(measurements, dtype=float)

    # Sort by triplet and then by XYZ norm so nearest neighbors are adjacent per triplet.
    xyz_norm = np.linalg.norm(measurements[:, 3:], axis=1)
    sort_idx = np.lexsort(
        (
            xyz_norm,
            measurements[:, 2],
            measurements[:, 1],
            measurements[:, 0],
        )
    )
    measurements = measurements[sort_idx].copy()

    rgb = measurements[:, :3]
    xyz = measurements[:, 3:]
    xyz_norm = np.linalg.norm(xyz, axis=1)

    _, starts = np.unique(rgb, axis=0, return_index=True)
    ends = np.concatenate([starts[1:] - 1, [len(measurements) - 1]])

    diff_prev = np.linalg.norm(np.diff(xyz, axis=0, prepend=np.full((1, 3), np.inf)), axis=1)
    diff_next = np.linalg.norm(np.diff(xyz, axis=0, append=np.full((1, 3), np.inf)), axis=1)
    diff_prev[starts] = np.inf
    diff_next[ends] = np.inf

    min_diff = np.minimum(diff_prev, diff_next)

    # Singletons have no neighbors in their triplet group and cannot be outliers.
    min_diff[np.isinf(diff_prev) & np.isinf(diff_next)] = 0.0

    rel_denom = np.where(xyz_norm > 0.0, xyz_norm, np.inf)
    outliers = (min_diff > abs_tol) & ((min_diff / rel_denom) > rel_tol)

    measurements[outliers, 3:] = np.nan

    return measurements


def average(measurements):
    """Average repeated tristimulus measurements per RGB triplet.

    Parameters
    ----------
    measurements : array-like
        table with columns ``R, G, B, X, Y, Z``

    Returns
    -------
    numpy.ndarray
        averaged table with one row per unique triplet and columns
        ``R, G, B, X, Y, Z``
    """
    measurements = np.asarray(measurements, dtype=float)

    # Drop rows where at least one tristimulus value is NaN.
    valid = ~np.isnan(measurements[:, 3:]).any(axis=1)
    measurements = measurements[valid]

    rgb = measurements[:, :3]
    xyz = measurements[:, 3:]

    unique_rgb, inverse = np.unique(rgb, axis=0, return_inverse=True)
    counts = np.bincount(inverse)

    xyz_avg = np.column_stack(
        [
            np.bincount(inverse, weights=xyz[:, 0]) / counts,
            np.bincount(inverse, weights=xyz[:, 1]) / counts,
            np.bincount(inverse, weights=xyz[:, 2]) / counts,
        ]
    )

    return np.column_stack([unique_rgb, xyz_avg])


def _channel_subset(measurements, channel, atol=1e-10):
    """Extract channel-isolated rows for a given RGB channel index."""
    other = [idx for idx in range(3) if idx != channel]
    mask = np.isclose(measurements[:, other[0]], 0.0, atol=atol) & np.isclose(
        measurements[:, other[1]], 0.0, atol=atol
    )
    subset = measurements[mask]
    subset = subset[np.argsort(subset[:, channel])]
    return subset


def linearize(measurements, bit_depth=8):
    """Linearize channel-isolated XYZ measurements into a 13-column CLUT.

    Parameters
    ----------
    measurements : array-like
        averaged measurements with columns ``R, G, B, X, Y, Z``
    bit_depth : int, optional
        target CLUT input resolution, by default 8

    Returns
    -------
    numpy.ndarray
        CLUT with columns
        ``[intensity_in, R_out, G_out, B_out, X_R, X_G, X_B, Y_R, Y_G, Y_B, Z_R, Z_G, Z_B]``
    """
    measurements = np.asarray(measurements, dtype=float)
    if measurements.ndim != 2 or measurements.shape[1] != 6:
        raise ValueError("measurements must be a 2D array with 6 columns: R,G,B,X,Y,Z")

    n_samples = 2**bit_depth
    intensity_in = np.linspace(0.0, 1.0, n_samples)

    # Determine dark tristimulus from explicit black triplet if available.
    black_mask = np.isclose(measurements[:, :3], 0.0, atol=1e-10).all(axis=1)
    if np.any(black_mask):
        dark_xyz = np.mean(measurements[black_mask, 3:], axis=0)
    else:
        dark_idx = np.argmin(np.sum(measurements[:, :3], axis=1))
        dark_xyz = measurements[dark_idx, 3:]

    channel_out = []
    channel_xyz = []

    for channel in range(3):
        subset = _channel_subset(measurements, channel)
        if len(subset) < 2:
            raise RuntimeError(
                "linearize requires at least two measurements per isolated channel "
                f"for channel index {channel}"
            )

        ch_input = subset[:, channel]
        ch_xyz = subset[:, 3:]

        # Collapse repeated measurements at identical channel input before interpolation.
        unique_input, inverse = np.unique(ch_input, return_inverse=True)
        counts = np.bincount(inverse)
        ch_xyz = np.column_stack(
            [
                np.bincount(inverse, weights=ch_xyz[:, 0]) / counts,
                np.bincount(inverse, weights=ch_xyz[:, 1]) / counts,
                np.bincount(inverse, weights=ch_xyz[:, 2]) / counts,
            ]
        )
        ch_input = unique_input

        # Linearize using Y (luminance) progression per channel.
        # Enforce non-decreasing Y to make interpolation stable under measurement noise.
        y_vals = np.maximum.accumulate(ch_xyz[:, 1])
        desired_y = np.linspace(np.min(y_vals), np.max(y_vals), n_samples)

        channel_out.append(np.interp(desired_y, y_vals, ch_input))
        channel_xyz.append(
            np.column_stack(
                [
                    np.interp(desired_y, y_vals, ch_xyz[:, 0]),
                    np.interp(desired_y, y_vals, ch_xyz[:, 1]),
                    np.interp(desired_y, y_vals, ch_xyz[:, 2]),
                ]
            )
        )

    rgb_out = np.column_stack(channel_out)

    matrices = np.zeros((n_samples, 3, 3), dtype=float)
    for i in range(n_samples):
        for channel in range(3):
            out_val = rgb_out[i, channel]
            if out_val > 0.0:
                matrices[i, :, channel] = (channel_xyz[channel][i] - dark_xyz) / out_val

    # Forward-fill zero rows where out_val == 0 (typically the first row).
    for i in range(1, n_samples):
        zero_cols = np.isclose(matrices[i], 0.0).all(axis=0)
        matrices[i, :, zero_cols] = matrices[i - 1, :, zero_cols]

    # Encode dark chromaticity in the first row, consistent with create_clut.
    matrices[0] = np.diag(dark_xyz)

    matrices_flat = matrices.reshape(n_samples, -1)
    return np.column_stack([intensity_in, rgb_out, matrices_flat])
