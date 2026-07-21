"""Mock photometer (for testing) using a lookup table to simulate luminance readings.

Simulated photometer object that adheres to the same interface as the real photometer,
but returns simulated luminance values (based on a LUT) instead of reading from a physical device.

The challenge with mocking a photometer is that it has no knowledge of what
intensity is currently being displayed -- that information travels through the
physical path (screen → photons → sensor).

MockPhotometer solves this by holding ``current_intensity`` as a direct attribute,
which a stimulus draw function should update before ``readLuminance`` is called.

Typical usage::

    ihrl.photometer = MockPhotometer(lut)

    def mock_draw(ihrl, intensity):
        ihrl.photometer.current_intensity = intensity
        # draw_uniform_square(ihrl, intensity)

    measure_lut(ihrl, stim_draw_func=mock_draw, ...)
"""

import numpy as np

from .photometer import Photometer


class MockPhotometer(Photometer):
    """Photometer that returns simulated luminance values from a LUT.

    The currently displayed intensity is tracked via the ``current_intensity``
    attribute, which must be updated by the stimulus drawing code before each
    call to ``readLuminance``.

    Parameters
    ----------
    luminance_mapping : callable or array-like or
        Defines the mapping of intensity to luminance, as either a:

        - **callable**: ``luminance_mapping(intensity: float) -> float`` returning cd/m².
            This could be a function, or a lambda,
            e.g. ``lambda x: 100 * x**2.2`` for a simple gamma mapping.
        - **array** of shape ``(N, 2)`` or ``(N, 3)``:
            First column (Column 0) is intensity (input),
            the *last* column is luminance (cd/m²).
            Values are linearly interpolated.
    noise : float, optional
        Standard deviation of zero-mean Gaussian noise added to each reading,
        in cd/m², by default 0.0 (noiseless).
    rng : numpy.random.Generator or int or None, optional
        Random number generator (or seed) used for noise.  Pass an integer
        for reproducible results. By default None (unseeded).

    Attributes
    ----------
    current_intensity : float
        The intensity value (in [0, 1]) most recently drawn to the screen.
        Update this before calling ``readLuminance``.
    """

    def __init__(self, luminance_mapping, noise=0.0, rng=None):
        super().__init__()
        self.current_intensity = 0.0
        self.noise = noise
        self.rng = np.random.default_rng(rng)

        if callable(luminance_mapping):
            self._lut_func = luminance_mapping
        else:
            luminance_mapping = np.asarray(luminance_mapping)
            if luminance_mapping.shape[1] == 3:
                # Full 3-column LUT (intensity_in, intensity_out, luminance):
                # use intensity_out (col 1) as the physical intensity axis.
                intensities = luminance_mapping[:, 1]
            else:
                intensities = luminance_mapping[:, 0]
            luminances = luminance_mapping[:, -1]
            self._lut_func = lambda x: float(np.interp(x, intensities, luminances))

    def readLuminance(self, n=3, slp=None):
        """Return simulated luminance for the currently displayed intensity.

        Parameters
        ----------
        n : int
            Number of samples to average (mirrors the real photometer API).
        slp : int
            Sleep time between samples in ms (ignored in mock).

        Returns
        -------
        float
            Simulated luminance in cd/m², averaged over ``n`` samples.
        """
        base_lum = self._lut_func(self.current_intensity)
        if self.noise > 0.0:
            samples = base_lum + self.rng.normal(0.0, self.noise, size=n)
            return float(np.mean(samples))
        return base_lum
