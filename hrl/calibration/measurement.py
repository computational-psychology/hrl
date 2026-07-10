from functools import partial
from pathlib import Path

import numpy as np


def setup_intensities(i_min, i_max, n_steps, n_samples=1, shuffle=False, reverse=False):
    """Set up the intensity values to be measured

    Parameters
    ----------
    i_min : float
        minimum intensity value to be measured
    i_max : float
        maximum intensity value to be measured
    n_steps : int
        number of intensity values to be measured
    n_samples : int, optional
        number of samples to be measured for each intensity value, by default 1
    shuffle : bool, optional
        shuffle the intensity values, by default False
    reverse : bool, optional
        reverse the order of the intensity values, by default False

    Returns
    -------
    np.ndarray
        array of intensity values to be measured
    """
    intensities = np.linspace(i_min, i_max, n_steps)
    intensities = np.repeat(intensities, n_samples)  # repeat each intensity value n_samples times

    if shuffle:
        np.random.shuffle(intensities)
    elif reverse:
        intensities = intensities[::-1]

    return intensities


def draw_uniform_square(ihrl, intensity, patch_size=0.5):
    """Draw a centered square patch of uniform intensity

    Parameters
    ----------
    ihrl : HRL
        the HRL instance to use for drawing the patch
    intensity : float
        intensity of the patch (0.0 to 1.0)
    patch_size : float, optional
        size of the patch as a fraction of the screen, by default 0.5
    """
    screen_width, screen_height = ihrl.graphics.width, ihrl.graphics.height
    patch_width = screen_width * patch_size
    patch_height = screen_height * patch_size
    patch_position = (
        (screen_width - patch_width) / 2,
        (screen_height - patch_height) / 2,
    )
    patch = ihrl.graphics.newTexture(np.array([[intensity]]))
    patch.draw(patch_position, (patch_width, patch_height))
    ihrl.graphics.flip()


def measure_lut(
    ihrl,
    intensities=setup_intensities(0.0, 1.0, 2**16, n_samples=5),
    stim_draw_func=partial(draw_uniform_square, patch_size=0.5),
    out_file=None,
    sleep_time=200,
):
    """Measure luminance for a range of intensity values

    Parameters
    ----------
    ihrl : HRL
        the HRL instance to use
    intensities : array-like
        intensity values to measure, by default 2**16 steps from 0 to 1
    stim_draw_func : callable, optional
        function with signature `(ihrl, intensity)` that draws the stimulus
        for each measurement; defaults to `draw_uniform_square(patch_size=0.5)`
    out_file : str or Path, optional
        path to output file for measurements, by default None (no file output)
    sleep_time : float
        time (ms) to wait between photometer readings, by default 200ms
    """
    if out_file is not None:
        out_file = Path(out_file).expanduser().resolve()

    measurements = np.full((len(intensities), 2), np.nan, dtype=float)

    for idx_int, intensity in enumerate(intensities):
        print(
            f"Current Intensity: {intensity:.2f} "
            f"[{idx_int:d} of {len(intensities)} "
            f"({idx_int / len(intensities):.2%}%)]"
        )

        measurements[idx_int, 0] = intensity

        # Draw (update) stimulus
        stim_draw_func(ihrl, intensity)

        # Multiple samples for each intensity value
        sample = ihrl.photometer.readLuminance(5, int(sleep_time))
        measurements[idx_int, 1] = sample

        # Write measured samples to file
        if out_file is not None:
            np.savetxt(
                out_file,
                measurements,
                delimiter=",",
                header="intensity,luminance",
                comments="",
            )

        if ihrl.inputs is not None and ihrl.inputs.checkEscape():
            break

    return measurements


def combine(measurements):
    """Construct an intensity-to-luminance map from (sets of) measurements

    Build a dictionary of {intensity: luminances}, from measurements.
    Measurements should be a collection (list, tuple, set), of numpy.ndarrays,
    where each array (measurements table) has
    a first column indicating the set monitor intensity (in domain [0, 1]),
    and a second column with the measured luminance (in cd/m2).

    Also removes NaN measurements.

    The reason this output is a dict (and not, say, a numpy array)
    is that the number of measured luminances could be different for each intensity.


    Parameters
    ----------
    measurements : Collection[numpy.ndarray]
        (set of) measurement table(s)

    Returns
    -------
    dict[float: numpy.ndarray]
        dictionary mapping {intensity: measured luminances}

    Raises
    ------
    RuntimeError
        when there are no valid (non-NaN) measurements left for a given intensity value
    """
    luminance_map = {}
    for table in measurements:
        for row in table:
            intensity = row[0]
            luminances = row[1:]

            # Remove NaN measurements
            luminances = luminances[~np.isnan(luminances)]

            # Add to map
            if intensity not in luminance_map:
                luminance_map[intensity] = []
            luminance_map[intensity] = np.concatenate([luminance_map[intensity], luminances])

    # Check for NaNs
    for intensity, luminances in luminance_map.items():
        if not luminances.any():  # empty array
            raise RuntimeError(f"no valid measurement for {intensity:.4f}")

    return luminance_map


def remove_outliers(measurements, abs_tol=0.075, rel_tol=0.0075):
    """Remove outlier measurements from a measurements array

    Outliers are values that deviate more than abs_tol from
    the closest measurement at the same intensity,
    AND where that deviation is more than rel_tol.
    Outliers are set to NaN in the returned array.

    Parameters
    ----------
    measurements : ArrayLike
        monitor measurements; first column must be specified intensities,
        second column must be corresponding measured luminances
    abs_tol : float, optional
        absolute tolerance, in cd/m2, by default 0.075
    rel_tol : float, optional
        relative tolerance, i.e., proportion of closest measurement, by default 0.0075

    Returns
    -------
    numpy.ndarray
        measurements array with outliers set to NaN

    Raises
    ------
    RuntimeError
        when there are no valid (non-NaN) measurements left for a given intensity value
    """
    # Sort by (intensity, luminance) so within each intensity group, luminances are ordered
    sort_idx = np.lexsort((measurements[:, 1], measurements[:, 0]))
    measurements = measurements[sort_idx].copy()

    intensities = measurements[:, 0]
    luminances = measurements[:, 1]

    # Identify the start and end indices of each intensity group
    _, _pos = np.unique(intensities, return_index=True)
    ends = np.concatenate([_pos[1:] - 1, [len(measurements) - 1]])

    # If measurement is outlier compared to closes neighbor, also compared to all others in group
    # So, only need to check to nearest neighbors, and since we sorted by luminance (within group),
    # that's just the previous and next measurement in the array
    diff_prev = np.abs(np.diff(luminances, prepend=np.inf))
    diff_next = np.abs(np.diff(luminances, append=np.inf))
    diff_prev[_pos] = np.inf
    diff_next[ends] = np.inf

    # Minimum distance to closest measurement at same intensity
    min_diff = np.minimum(diff_prev, diff_next)

    # Singletons (only measurement at that intensity) have both neighbors set to inf;
    # they have nothing to be compared against, so they cannot be outliers
    min_diff[np.isinf(diff_prev) & np.isinf(diff_next)] = 0

    # Identify outliers: those that deviate (minimal distance) more than abs_tol from closest measurement,
    # AND where that deviation is more than rel_tol
    outliers = (min_diff > abs_tol) & (min_diff / luminances > rel_tol)

    # Set outliers to NaN
    measurements[outliers, 1] = np.nan

    return measurements


def average(measurements):
    """Average measured luminances per intensity value

    Parameters
    ----------
    measurements : ArrayLike
        monitor measurements; first column must be specified intensities,
        second column must be corresponding measured luminances

    Returns
    -------
    numpy.ndarray
        table with a first column indicating the set monitor intensity (in domain [0, 1]),
        and a second column with the average measured luminance (in cd/m2)
    """
    # Sort
    measurements = measurements[np.argsort(measurements[:, 0])]

    # Drop NaN measurements
    measurements = measurements[~np.isnan(measurements[:, 1])]

    # Extract intensities
    intensities = measurements[:, 0].copy()

    # Group by intensity value
    _id, _pos, m_count = np.unique(intensities, return_index=True, return_counts=True)

    # Summed luminances per intensity value
    l_sum = np.add.reduceat(measurements[:, 1], _pos, axis=0)

    # Average luminances per intensity value
    l_avg = l_sum / m_count

    # Out
    table = np.column_stack((_id, l_avg))

    return table


def smooth(measurements, order=1, kernel=[0.2, 0.2, 0.2, 0.2, 0.2]):
    """Smooth measurements (of adjacent intensities) by given kernel

    Parameters
    ----------
    measurements : ArrayLike
        monitor measurements; first column must be specified intensities,
        second column must be corresponding measured luminances
    order : int, optional
        order of smoothing, i.e., number of repeated smoothings, by default 1
    kernel : ArrayLike, optional
        smoothing kernel, by default [0.2, 0.2, 0.2, 0.2, 0.2]

    Returns
    -------
    numpy.ndarray
        measurements array with smoothed luminance values
    """

    smoothed = np.array(measurements[:, 1]).copy()

    for _ in range(order):
        # Pad
        smoothed = np.pad(
            smoothed,
            pad_width=len(kernel) // 2,
            constant_values=(smoothed[0], smoothed[-1]),
        )

        # Convolve
        smoothed = np.convolve(smoothed, kernel, "valid")

    return np.column_stack((measurements[:, 0], smoothed))


def linearize(measurements, bit_depth=16):
    """Linearize LUT from measurements

    Finds each measurement that most closely corresponding to
    each linear luminance step between measured max and min luminance.

    NOTE: that this linearization *does not* interpolate between measurements.
    Thus, the resulting LUT is *at most* as long as the measurements.
    Possibly, it is shorter:
    if multiple input values were measured as (approx.) the same luminance.

    Parameters
    ----------
    measurements : ArrayLike
        monitor measurements; first column must be specified intensities,
        second column must be corresponding measured luminances
    bit_depth : int, optional
        bit depth, i.e., resolution of the linearized LUT, by default 16 (2**16 = 65536 entries)

    Returns
    -------
    numpy.ndarray
        linearized LUT, with columns "Intensity In", "Intensity Out", (measured) "Luminance"
    """

    # Separate measured intensities, luminances
    ints_measured = measurements[:, 0]
    lums_measured = measurements[:, 1]

    n_samples = 2**bit_depth

    # Setup linearized luminances
    linear_luminances = np.linspace(np.min(lums_measured), np.max(lums_measured), n_samples)
    linear_intensities = np.linspace(0, 1, n_samples)

    # Find unique measured luminances for linear steps
    measurement_indices = []
    sample_indices = np.zeros(n_samples, dtype=bool)
    for i, lum_desired in enumerate(linear_luminances):
        # Which measured luminance is the first greater than the desired luminance for this step?
        first_idx = np.argwhere(lums_measured >= lum_desired)[0][0]

        # If this measurement is not yet in our list, add it
        if not len(measurement_indices) or (first_idx != measurement_indices[-1]):
            sample_indices[i] = True
            measurement_indices.append(first_idx)

    # Construct Lookup Table
    linearized_lut = np.transpose(
        [
            linear_intensities[sample_indices],  # intensity in
            ints_measured[measurement_indices],  # intensity out (measured)
            lums_measured[measurement_indices],  # luminance (measured)
        ]
    )

    return linearized_lut
    # return lambda x: np.interp(x,np.linspace(0,1,n_samples),ints_measured[measurement_indices])
