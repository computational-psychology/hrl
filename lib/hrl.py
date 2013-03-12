### Imports ###

import numpy as np
import pygame as pg
import os
import csv


### HRL Class ###

class HRL:
    """
    HRL (High Resoultion Luminance) is a class which interfaces with a set of
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


    def __init__(self
                ,graphics='gpu'
                ,inputs='keyboard'
                ,photometer=None
                ,wdth=1024,hght=768,bg=0.0
                ,fs=False,db=True,scrn=0
                ,dfl=None,rfl=None,rhds=None):
        """
        Initialize an HRL object.

        Parameters
        ----------

        graphics : The graphics device to use. Available: 'gpu','datapixx',
            None. Default: 'gpu'
        inputs : The input device to use. Available: 'keyboard', 'responsepixx',
            None. Default: 'keyboard'
        photometer : The graphics device to use. Available: 'optical', None.
            Default: None
        wdth : The desired width of the screen. Default: 1024
        hght : The desired height of the screen. Default: 768
        bg : The background luminance on a scale from 0 to 1. Default: 0.0
        fs : Whether or not to run in Fullscreen.Default: False
        db : Whether or not to use double buffering. Default: True
        scrn: Which monitor to use. Numbered 0,1... Default: 0
        dfl : The read location of the design matrix. Default: None
        rfl : The write location of the result matrix. Default: None
        rhds : A list of the string names of the headers for the Result
            Matrix. The string names should be without spaces, e.g.
            'InputLuminance'. If rfl != None, rhds must be provided.
            Default: None
        
        Returns
        -------
        hrl instance. Comes with a number of methods required to run an
        experiment.
        """

        ### Load Config ###
        #data_files=[(os.path.expanduser('~/.config'), ['misc/hrlrc'])]
        #cfg = cp.RawConfigParser()
        #cfg.read([os.path.expanduser('~/.config/hrlrc')])
        os.environ['DISPLAY'] = ':0.' + str(scrn)

        ## Load Datapixx ##

        if (graphics == 'datapixx') or (inputs == 'responsepixx'):

            import datapixx as dpx

            # Open datapixx.
            self.datapixx = dpx.open()

            # set videomode: Concatenate Red and Green into a 16 bit luminance
            # channel.
            self.datapixx.setVidMode(dpx.DPREG_VID_CTRL_MODE_M16)

            # Demonstrate successful initialization.
            self.datapixx.blink(dpx.BWHITE | dpx.BBLUE | dpx.BGREEN
                        | dpx.BYELLOW | dpx.BRED)

        else:

            self.datapixx = None


        ## Load Graphics Device ##
        
        if graphics == 'gpu':

            from graphics.gpu import GPU
            self.graphics = GPU(wdth,hght,bg,fs,db)

        elif graphics == 'datapixx':

            from graphics.datapixx import DATAPixx
            self.graphics = DATAPixx(wdth,hght,bg,fs,db)

        else:

            self.graphics = None


        ## Load Input Device ##

        if inputs == 'keyboard':

            from inputs.keyboard import Keyboard
            self.inputs = Keyboard()

        elif inputs == 'responsepixx':

            from inputs.responsepixx import RESPONSEPixx
            self.inputs = RESPONSEPixx(self.datapixx)

        else:

            self.inputs = None


        ## Load Photometer ##

        if inputs == 'optical':

            from photometer.optical import OptiCAL
            self.photometer = OptiCAL('/dev/ttyUSB0')

        else:

            self.photometer = None


        ## Design and Result matrices ##

        self._dfl = None
        if dfl != None:
            self._dfl = open(dfl,'rb')
            self.designs = csv.DictReader(self._dfl,delimiter=' ',skipinitialspace=True)
        
        self._rfl = None
        if rfl != None:
            self._rfl = open(rfl,'wb')
            self._rwtr = csv.DictWriter(self._rfl,rhds,delimiter=' ')
            self.results = {}
            #self._rwtr.writeheader() - requires Python 2.7
            self._rfl.write(' '.join(rhds) + '\r\n')

        # Gamma Function Correction
        #self._lut = None
        #self._gammainv = lambda x: x
        #if lut != None:
            #self._lut = np.genfromtxt(lut,skip_header=1)
            #self._gammainv = lambda x: np.interp(x,self._lut[:,0],self._lut[:,1])

    def close(self):
        """
        Closes all the devices and systems maintained by the HRL object.
        This should be called at the end of the program.
        """
        if self.datapixx != None: self.datapixx.close()
        if self._rfl != None: self._rfl.close()
        if self._dfl != None: self._dfl.close()
        pg.quit()


    ## File methods ##


    def writeResultLine(self,dct=None):
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
