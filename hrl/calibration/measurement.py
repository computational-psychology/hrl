import numpy as np


def measure_lut(
    ihrl,
    intensities,
    patch_size=0.5,
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
    patch_size : float
        size of the patch in proportion of screen size (0.0 to 1.0), by default 0.5
    n_samples : int
        number of photometer readings per intensity level, by default 5
    sleep_time : float
        time in seconds to wait between photometer readings, by default 0.1
    """
    _sleeptime = int(sleep_time * 1000)  # convert to ms once

    screen_width, screen_height = ihrl.graphics.width, ihrl.graphics.height

    (patch_width, patch_height) = (screen_width * patch_size, screen_height * patch_size)
    patch_position = ((screen_width - patch_width) / 2, (screen_height - patch_height) / 2)

    for idx_int, intensity in enumerate(intensities):
        print(
            f"Current Intensity: {intensity:.2f} "
            f"[{idx_int:d} of {len(intensities)} "
            f"({idx_int / len(intensities) * 100:.1f}%)]"
        )
        ihrl.results["Intensity"] = intensity

        patch = ihrl.graphics.newTexture(np.array([[intensity]]))
        patch.draw(patch_position, (patch_width, patch_height))
        ihrl.graphics.flip()

        # Multiple samples for each intensity value
        for idx_sample in range(n_samples):
            sample = ihrl.photometer.readLuminance(5, _sleeptime)
            ihrl.results[f"Luminance{idx_sample}"] = sample

        # Write measured samples to file
        ihrl.writeResultLine()

        if ihrl.inputs.checkEscape():
            break
