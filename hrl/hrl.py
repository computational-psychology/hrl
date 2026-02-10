### Imports ###

import csv
import os

import numpy as np
import pygame

import hrl.graphics
import hrl.inputs
import hrl.photometer

### HRL Class ###


class HRL:
    """
    HRL (High Resolution Luminance) is a class which interfaces with a set of
    devices for assembling a psychophysics experiment. The sorts of devices are
    graphics devices for driving display, inputs for reading input from a
    subject, and photometers for calibration. For more information about these
    components, see the relevant help files.

    An optional aspect of HRLs functionality is the ability to automatically
    read design matrices, and print out result matrices.  While this
    functionality is little more than a reexportation of python's csv package,
    it can still simplify the code of many experiment scripts. These features
    can be activated with the appropriate hrl initializaiton arguments. When
    activated, the corresponding HRL instance has the fields 'designs' and
    'results' added to it. hrl.designs is an iterator over the lines of the
    design matrix and can be used for example in a for loop - 'for dsgn in
    hrl.designs:'.  hrl.results is a dictionary which is written to the result
    matrix file when hrl.writeResultLine() is called.
    """

    ## Core methods ##

    def __init__(
        self,
        graphics="gpu",
        inputs="keyboard",
        photometer=None,
        wdth=1024,
        hght=768,
        bg=0.0,
        fs=False,
        wdth_offset=0,
        db=True,
        scrn=None,
        dfl=None,
        rfl=None,
        rhds=None,
        lut=None,
        mouse=False,
    ):
        """Initialize an HRL object.

        Parameters
        ----------
        graphics : str
            alias for the desired graphics device, by default "gpu".
            Valid options are defined in hrl.graphics.ALIAS_MAP.
        inputs : str
            alias for the desired input device, by default "keyboard".
        photometer : str or None
            alias for the desired photometer device, by default None.
        wdth : int
            width of the screen in pixels, by default 1024.
        hght : int
            height of the screen in pixels, by default 768.
        bg : float or tuple, optional
            background intensity value (0.0, 1.0), by default 0.0.
            For grayscale devices, this is a gray level;
            for color devices, can specify an RGB triplet.
        fs : bool, optional
            run in Fullscreen, currently fixed to False -- because in later versions of pygame
            fullscreen on a second screen gives very weird behavior on recording of keyboard events,
            effectively hanging the computer.
        wdth_offset: int, optional
            horizontal offset of the window, in pixels, by default 0.
            Useful for setups with multiple monitors but a single Xscreen session.
        db : bool, optional
            use double buffering, by default True.
        scrn : int or str, optional
            which monitor to use, by default None (use the environment).
            Given as an integer (e.g., 0, 1),
            or as a string containing the X11 screen specification string (e.g., ":0.1" or ":1").
        dfl : Path or str or None, optional
            path to design file, by default None.
        rfl : Path or str or None, optional
            path to results file, by default None.
        rhds : List(str) or None, optional
            headers for the Result Matrix, by default None.
            The string names should be without spaces, e.g. 'InputLuminance'.
            If rfl != None, rhds must be provided.
        lut : Path or str or None, optional
            Path to Look-up Table, by default None.
        mouse: bool, optional
            enables or disables the mouse cursor, by default False.

        Returns
        -------
        HRL
            an initialized hrl instance.
            Comes with a number of methods required to run an experiment.
        """

        ## Setup screen and graphics ##
        self.graphics = hrl.graphics.new_graphics(
            graphics_alias=graphics.lower(),
            width=wdth,
            height=hght,
            background=bg,
            fullscreen=fs,
            double_buffer=db,
            lut=lut,
            mouse=mouse,
            screen=scrn,
            width_offset=wdth_offset,
        )

        ## Setup Input Device ##
        self.inputs = hrl.inputs.new_input(
            input_alias=inputs,
            device=self.graphics.device,
        )

        ## Setup photometer ##
        if photometer is not None:
            self.photometer = hrl.photometer.new_photometer(
                photometer_alias=photometer,
                device="/dev/ttyUSB0",
                timeout=10,
            )

        ## Results file ##
        self._rfl = None
        if rfl != None:
            # check if the file exists,,, if so then check how many trials have been made,
            # then opens file in 'a' mode, and do not write the header
            if os.path.exists(rfl):
                # checks how many trials have been run
                r = open(rfl, "r")
                reader = csv.DictReader(r, delimiter=",")
                l = list(reader)
                r.close()
                # length of list is the number of rows that has been written (without counting the header)
                self.starttrial = len(l)

                self._rfl = open(rfl, "a")
                self._rwtr = csv.DictWriter(self._rfl, rhds, delimiter=",")

            # if it doesnt exist, open in 'wb' mode and write the header
            else:
                self._rfl = open(rfl, "w")
                self._rwtr = csv.DictWriter(self._rfl, rhds, delimiter=",")
                self._rfl.write(" ".join(rhds) + "\r\n")  # writes header
                self.starttrial = 0

            # initalizing empty results dict (for trial-based saving)
            self.results = {}

        ## Design matrix file ##
        self._dfl = None
        if dfl != None:
            self._dfl = open(dfl, "r")
            self.designs = csv.DictReader(self._dfl, delimiter=",", skipinitialspace=True)
            # skip trials already done
            for i in range(self.starttrial):
                self.designs.next()

    def close(self):
        """
        Closes all the devices and systems maintained by the HRL object.
        This should be called at the end of the program.
        """
        if self.graphics.device != None:
            self.graphics.device.close()
        if self._rfl != None:
            self._rfl.close()
        if self._dfl != None:
            self._dfl.close()
        pygame.quit()

    @property
    def height(self):
        return self.graphics.height if self.graphics else None

    @property
    def width(self):
        return self.graphics.width if self.graphics else None

    @property
    def background(self):
        return self.graphics.background if self.graphics else None

    @property
    def device(self):
        return self.graphics.device if self.graphics else None

    ## File methods ##

    def writeResultLine(self, dct=None):
        """
        Given an appropriate dicitonary of values, writes the line to
        the result file. The dictionary must include all the names given
        to the hrl instance when it was initialized. i.e. if the
        rhds=['Input','Output'] then dct must have elements dct['Input']
        and dct['Output'].

        By default, hrl uses the dictionary hrl.results, but the dictionary
        can be given directly if desired.

        Parameters
        ----------
        dct : The dictionary of results in the current trial.
        """
        if dct is None:
            self._rwtr.writerow(self.results)
        else:
            self._rwtr.writerow(dct)
