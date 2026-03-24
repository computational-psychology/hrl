from functools import partial

import numpy as np


def setup_intensities(i_min, i_max, n_steps, shuffle=False, reverse=False):
    """Set up the intensity values to be measured

    Parameters
    ----------
    i_min : float
        minimum intensity value to be measured
    i_max : float
        maximum intensity value to be measured
    n_steps : int
        number of intensity values to be measured
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


def measure_lut(
    ihrl,
    intensities=setup_intensities(0.0, 1.0, 2**16),
    stim_draw_func=partial(draw_uniform_square, patch_size=0.5),
    n_samples=5,
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
    n_samples : int
        number of photometer readings per intensity level, by default 5
    sleep_time : float
        time (ms) to wait between photometer readings, by default 200ms
    """

    for idx_int, intensity in enumerate(intensities):
        print(
            f"Current Intensity: {intensity:.2f} "
            f"[{idx_int:d} of {len(intensities)} "
            f"({idx_int / len(intensities) * 100:.1f}%)]"
        )
        ihrl.results["Intensity"] = intensity

        # Draw (update) stimulus
        stim_draw_func(ihrl, intensity)
        ihrl.graphics.flip()

        # Multiple samples for each intensity value
        for idx_sample in range(n_samples):
            sample = ihrl.photometer.readLuminance(5, int(sleep_time))
            ihrl.results[f"Luminance{idx_sample}"] = sample

        # Write measured samples to file
        ihrl.writeResultLine()

        if ihrl.inputs.checkEscape():
            break


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


def remove_outliers(luminance_map, abs_tol=0.075, rel_tol=0.0075):
    """Remove outlier measurements from intensity-to-luminance map

    Outliers are values that deviate more than abs_tol from
    the closest measurement at the same intensity,
    AND where that deviation is more than rel_tol.

    Parameters
    ----------
    luminance_map : dict[float: numpy.ndarray]
        dictionary mapping {intensity: measured luminances}, output from combine
    abs_tol : float, optional
        absolute tolerance, in cd/m2, by default 0.075
    rel_tol : float, optional
        relative tolerance, i.e., proportion of closest measurement, by default 0.0075

    Returns
    -------
    dict[float: numpy.ndarray]
        dictionary mapping {intensity: measured luminances}, without outliers

    Raises
    ------
    RuntimeError
        when there are no valid (non-NaN) measurements left for a given intensity value
    """
    # set outliers to NaN.
    for intensity, luminances in luminance_map.items():
        min_diff = np.zeros_like(luminances)
        for i, lum in enumerate(luminances):
            diffs = np.abs(luminances - lum)  # absolute difference between this lum, and all lums
            diffs[i] = np.nan  # don't compare to yourself
            min_diff[i] = np.nanmin(diffs)  # get minimum difference, i.e., to closest measurement

        # Set outliers to NaN
        luminances[(min_diff > abs_tol) & (min_diff / luminances > rel_tol)] = np.nan

        # Reinsert into map
        if all(np.isnan(luminances)):
            raise RuntimeError(f"no valid measurement for {intensity:.4f}")
        luminance_map[intensity] = luminances

    return luminance_map


def average(luminance_map):
    """Average measured luminances per intensity value, and return as table

    Parameters
    ----------
    luminance_map : dict[float: numpy.ndarray]
        dictionary mapping {intensity: measured luminances}

    Returns
    -------
    numpy.ndarray
        table with a first column indicating the set monitor intensity (in domain [0, 1]),
        and a second column with the average measured luminance (in cd/m2)
    """
    for intensity, luminances in luminance_map.items():
        luminance_map[intensity] = np.nanmean(luminances)

    # Convert to numpy array
    table = np.array(list(luminance_map.items()))

    # Sort
    table = table[table.argsort(axis=0)[:, 0]]

    # print(table.shape)

    return table


def smooth(measurements, order=1, kernel=[0.2, 0.2, 0.2, 0.2, 0.2]):
    """Smooth measurements (of adjacent intensities) by given kernel

    Parameters
    ----------
    measurements : numpy.ndarray
        1D array of luminance values (in cd/m²), one value per intensity level
    order : int, optional
        order of smoothing, i.e., number of repeated smoothings, by default 1
    kernel : ArrayLike, optional
        smoothing kernel, by default [0.2, 0.2, 0.2, 0.2, 0.2]

    Returns
    -------
    numpy.ndarray
        1D array of smoothed luminance values, same length as input
    """

    smoothed = np.array(measurements).copy()

    for _ in range(order):
        # Pad
        smoothed = np.pad(
            smoothed,
            pad_width=len(kernel) // 2,
            constant_values=(smoothed[0], smoothed[-1]),
        )

        # Convolve
        smoothed = np.convolve(smoothed, kernel, "valid")

    return smoothed


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
