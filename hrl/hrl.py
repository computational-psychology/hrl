### Imports ###

import csv
import os
import platform

import numpy as np
import pygame

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
        """
        Initialize an HRL object.

        Parameters
        ----------

        graphics : The graphics device to use. Available: 'gpu','datapixx'
            (to be used with DataPixx 1) or 'viewpixx' (for ViewPixx 3D).
            Default: 'gpu'
        inputs : The input device to use. Available: 'keyboard', 'responsepixx'.
            Default: 'keyboard'
        photometer : The graphics device to use. Available: 'optical', 'minolta', None.
            Default: None
        wdth : The desired width of the screen. Default: 1024
        hght : The desired height of the screen. Default: 768
        bg : The background luminance on a scale from 0 to 1. Default: 0.0
        fs : Whether or not to run in Fullscreen. Default: False
        wdth_offset: The desired horizontal offset of the window. Useful for setups
              with multiple monitors but a single Xscreen session. Default: 0
        db : Whether or not to use double buffering. Default: True
        scrn: Which monitor to use, given as an integer (e.g. 0, 1), or as a string containing the 
              X11 screen specification string (e.g. ":0.1" or ":1"). 
              Default: None (uses the default settings) 
        dfl : The read location of the design matrix. Default: None
        rfl : The write location of the result matrix. Default: None
        rhds : A list of the string names of the headers for the Result
            Matrix. The string names should be without spaces, e.g.
            'InputLuminance'. If rfl != None, rhds must be provided.
            Default: None
        lut : The lookup table. Default: None
        mouse: enables or disables the mouse cursor. Default: False

        Returns
        -------
        hrl instance. Comes with a number of methods required to run an
        experiment.
        """

        ####### Setting up on which monitor to use
        # In older systems or systems with separate Xscreens, the naming is still :0.0 or :0.1.
        # For systems with only one screen, it is :1.
        if platform.system() == "Linux":
            print("default screen number used by the OS: %s" % os.environ["DISPLAY"])

            if scrn!=None:
                # legacy option for older configs or separate Xscreens  
                if (os.environ["DISPLAY"] == ":0"): 
                    os.environ["DISPLAY"] = ":0." + str(scrn)
                else:
                    if isinstance(scrn, str):
                        os.environ["DISPLAY"] = scrn
                    elif isinstance(scrn, int):
                        os.environ["DISPLAY"] = ":" + str(scrn)

                print("display number changed to: %s" % os.environ["DISPLAY"])

            ## 11. Aug 2021
            # we add a wdth_offset to be able to run HRL in setups with a
            # single Xscreen but multiple monitors (a config with Xinerama enabled)
            os.environ["SDL_VIDEO_WINDOW_POS"] = "%d,0" % wdth_offset


		#######
        ## Load Datapixx ##

        if (graphics == "datapixx") or (inputs == "responsepixx") or (graphics == "viewpixx"):
            if graphics == "datapixx":
                from pypixxlib.datapixx import DATAPixx as DPixx
            elif graphics == "viewpixx":
                from pypixxlib.viewpixx import VIEWPixx3D as DPixx

            # Open datapixx.
            self.device = DPixx()

            # set videomode: Concatenate Red and Green into a 16 bit luminance
            # channel.
            mode = self.device.getVideoMode()
            print(mode)

            if mode != "M16":
                self.device.setVideoMode("M16")
                self.device.updateRegisterCache()

            mode = self.device.getVideoMode()
            print(mode)

            # Demonstrate successful initialization.
            # self.datapixx.blink(dpx.BWHITE | dpx.BBLUE | dpx.BGREEN
            #            | dpx.BYELLOW | dpx.BRED)
            # TODO BLINK with pypixxlib

        else:
            self.device = None

        # we force not fullscreen, even in experimental computer,
        # because in later versions of pygame
        # fullscreen on a second screen gives very weird behavior on
        # recording of keyboard events, effectively hanging the computer.
        fs = False

        ## Load Graphics Device ##
        if graphics in ("gpu", "gpu_grey", "grey", "gray", "gray8"):
            from .graphics.gpu import GPU_grey

            self.graphics = GPU_grey(
                width=wdth,
                height=hght,
                background=bg,
                fullscreen=fs,
                double_buffer=db,
                lut=lut,
                mouse=mouse,
            )
        elif graphics in ("viewpixx_RGB", "gpu_RGB", "RGB"):
            from .graphics.gpu import GPU_RGB

            self.graphics = GPU_RGB(
                width=wdth,
                height=hght,
                background=[bg, bg, bg],
                fullscreen=fs,
                double_buffer=db,
                lut=lut,
                mouse=mouse,
            )

        elif graphics == "datapixx" or graphics == "viewpixx":
            from .graphics.datapixx import DATAPixx

            self.graphics = DATAPixx(
                width=wdth,
                height=hght,
                background=bg,
                fullscreen=fs,
                double_buffer=db,
                lut=lut,
                mouse=mouse,
            )

        else:
            self.graphics = None

        ## Load Input Device ##

        if inputs == "keyboard":
            from .inputs.keyboard import Keyboard

            self.inputs = Keyboard()

        elif inputs == "responsepixx":
            from .inputs.responsepixx import RESPONSEPixx

            self.inputs = RESPONSEPixx(self.device)

        else:
            self.inputs = None

        ## Load Photometer ##

        if photometer == "optical":
            from .photometer.optical import OptiCAL
            self.photometer = OptiCAL("/dev/ttyUSB0", timeout=10)
            
        elif photometer == "minolta":
            from .photometer.minolta import Minolta
            self.photometer = Minolta("/dev/ttyUSB0")

        else:
            self.photometer = None

        ## Results file ##
        self._rfl = None
        if rfl != None:
            # check if the file exists,,, if so then check how many trials have been made,
            # then opens file in 'a' mode, and do not write the header
            if os.path.exists(rfl):
                # checks how many trials have been run
                r = open(rfl, "r")
                reader = csv.DictReader(r, delimiter=" ")
                l = list(reader)
                r.close()
                # length of list is the number of rows that has been written (without counting the header)
                self.starttrial = len(l)

                self._rfl = open(rfl, "a")
                self._rwtr = csv.DictWriter(self._rfl, rhds, delimiter=" ")

            # if it doesnt exist, open in 'wb' mode and write the header
            else:
                self._rfl = open(rfl, "w")
                self._rwtr = csv.DictWriter(self._rfl, rhds, delimiter=" ")
                self._rfl.write(" ".join(rhds) + "\r\n")  # writes header
                self.starttrial = 0

            # initalizing empty results dict (for trial-based saving)
            self.results = {}

        ## Design matrix file ##
        self._dfl = None
        if dfl != None:
            self._dfl = open(dfl, "r")
            self.designs = csv.DictReader(self._dfl, delimiter=" ", skipinitialspace=True)
            # skip trials already done
            for i in range(self.starttrial):
                self.designs.next()

    def close(self):
        """
        Closes all the devices and systems maintained by the HRL object.
        This should be called at the end of the program.
        """
        if self.device != None:
            self.device.close()
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
