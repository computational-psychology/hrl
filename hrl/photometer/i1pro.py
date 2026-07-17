"""Read luminance and tristimulus values with the X-Rite i1Pro.

This module provides the :class:`i1Pro` class, a thin wrapper around the
X-Rite i1Pro spectrophotometer used for monitor calibration. It exposes
methods to calibrate the device and to read CIE XYZ tristimulus values as
well as luminance (the Y tristimulus value, in candela per square meter).

The wrapper relies on the ``pypixxlib`` library from VPixx to talk to the
device, and on ``pygame`` for timing and keyboard input during the
interactive calibration steps.
"""

import numpy as np
import pygame
from pypixxlib.i1 import I1Pro

from .photometer import Photometer


def wait_any_button(timeout=0):
    """Block until a key is pressed or an optional timeout elapses.

    Polls the ``pygame`` event queue and returns as soon as a key is pressed.
    This is used to pause execution during calibration so the
    experimenter can place move the device and confirm they are ready to continue.

    Note that a working ``pygame`` display and event loop must be initialised
    by the caller for the keyboard events to be delivered.

    Parameters
    ----------
    timeout : int, optional
        Maximum time to wait, in milliseconds. If ``0`` (the default) the
        function waits indefinitely until a key is pressed.

    Returns
    -------
    None
    """
    t0 = pygame.time.get_ticks()
    btn = None
    while (timeout == 0) or (pygame.time.get_ticks() - t0 < timeout):
        event = pygame.event.wait(1)  # waits for only 1 ms
        if event.type == pygame.KEYDOWN:
            break


class i1Pro(Photometer):
    """Photometer driver for the X-Rite i1Pro spectrophotometer.

    Concrete implementation of the :class:`~hrl.photometer.photometer.Photometer`
    abstract base class for the X-Rite i1Pro. On construction the device is
    connected, its colour space is set to CIE XYZ and a calibration is performed,
    so that the instance is ready to take measurements. The device is calibrated
    for measurements of emitting surfaces, i.e. monitors.

    Measurements are returned either as full CIE XYZ tristimulus values (see
    :meth:`readTristimulus`) or as luminance alone (see :meth:`readLuminance`),
    with luminance defined as the Y tristimulus value in candela per square
    meter.

    Attributes
    ----------
    phtm : pypixxlib.i1.I1Pro
        The underlying VPixx device handle used for all hardware operations.
    """

    def __init__(self, timeout=5):
        """Connect to the i1Pro, set the colour space and calibrate it.

        Opens a connection to the device, prints its revision and serial
        number, configures the ``CIEXYZ`` colour space and immediately runs
        the calibration method.

        Parameters
        ----------
        timeout : int, optional
            Reserved for interface compatibility, not currently used.
        """
        super(i1Pro, self).__init__()
        self.phtm = I1Pro()

        print("i1Pro device connected")
        print(f"revision: {self.phtm.revision} - serial number: {self.phtm.serial_number}")
        self.phtm.setColorSpace("CIEXYZ")

        # calibrate always at the start
        self.calibrate()

    def calibrate(self):
        """Run a calibration of the device.

        Prompts the experimenter to place the i1Pro on its calibration nest
        and press the side button, then performs a calibration.
        The current colour space, measurement mode and illumination mode are
        printed for reference. Finally it waits (via :func:`wait_any_button`)
        for the experimenter to place the device on the screen and press any
        key before measurements begin.

        This method is called automatically at construction time and again by
        :meth:`readTristimulus` whenever the previous calibration has expired.

        Returns
        -------
        None
        """
        print("****************************************************")
        print("Calibrating device, put the device on its nest and push the side button")
        self.phtm.calibrate("Emission")

        print(f"Current color space is {self.phtm.getColorSpace()}")
        print(f"Current measurement mode is {self.phtm.getMeasurementMode()}")
        print(f"Current illumination mode is {self.phtm.getIlluminationMode()}")
        print("... Calibration done.")
        print("****************************************************")
        print("")
        print(
            "Put the device on the screen to be measured and press any key to start / continue the measurements"
        )
        wait_any_button(timeout=0)

    def readTristimulus(self, n=3, slp=1, verbose=False):
        """Read CIE XYZ tristimulus values from the device.

        Re-calibrates first if the device reports that its calibration has
        expired. Then attempts up to ``n`` measurements, returning the XYZ
        values of the first successful reading. If a measurement raises an
        error the attempt is retried; if every attempt fails, ``numpy.nan``
        is returned.

        Parameters
        ----------
        n : int, optional
            Maximum number of measurement attempts before giving up.
            Defaults is ``3``.
        slp : int, optional
            Delay in milliseconds inserted before each measurement attempt,
            applied via ``pygame.time.delay``. Defaults is ``1``.
        verbose : bool, optional
            If ``True``, print the measured X, Y and Z values to console.
            Default is ``False``.

        Returns
        -------
        tuple of float or float
            The ``(X, Y, Z)`` tristimulus values from the first successful
            measurement, or ``numpy.nan`` if all ``n`` attempts failed.
        """

        # check if calibration is needed
        if self.phtm.isCalibrationExpired():
            self.calibrate()

        # do measurements
        for i in range(n):
            try:
                pygame.time.delay(slp)

                # measure the XYZ tristimulus values
                self.phtm.runMeasurement()
                X, Y, Z = self.phtm.getLatestTriStimulusMeasurements()
                if verbose:
                    print("Tristimulus values:")
                    print(f"X: {X}, Y: {Y}, Z:{Z}")

                return X, Y, Z
            except:
                print("Error in reading from instrument")
        # if no try was successful
        return np.nan, np.nan, np.nan

    def readLuminance(self, n=3, slp=1, verbose=False):
        """Read the luminance from the device, in candela per square meter.

        Convenience wrapper around :meth:`readTristimulus` that returns only
        the Y tristimulus value, which is luminance by definition in the CIE
        XYZ colour space.

        Parameters
        ----------
        n : int, optional
            Maximum number of measurement attempts before giving up.
            Defaults to ``3``.
        slp : int, optional
            Delay in milliseconds inserted before each measurement attempt.
            Defaults to ``1``.
        verbose : bool, optional
            If ``True``, print the measured X, Y and Z values. Defaults to
            ``False``.

        Returns
        -------
        float
            The luminance (Y) in candela per square meter. If every
            measurement attempt fails, :meth:`readTristimulus` returns
            ``numpy.nan`` and this method will raise a ``TypeError`` while
            unpacking, so callers should ensure the device is measuring
            correctly.
        """
        # reads tristimulus values X, Y, Z.
        _, lum, _ = self.readTristimulus(n=n, slp=slp, verbose=verbose)

        # returns Y, which is luminance by definition.
        return lum
