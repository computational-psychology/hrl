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
    sleep_time=0.1,
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
        time in seconds to wait between photometer readings, by default 0.1
    """
    _sleeptime = int(sleep_time * 1000)  # convert to ms once

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
            sample = ihrl.photometer.readLuminance(5, _sleeptime)
            ihrl.results[f"Luminance{idx_sample}"] = sample

        # Write measured samples to file
        ihrl.writeResultLine()

        if ihrl.inputs.checkEscape():
            break
