### Imports ###


# Qualified Imports
import numpy as np
import pygame as pg
import ConfigParser as cp
import os
import csv

# Unqualified Imports
from pygame.locals import *
from OpenGL.GL import *


### Loading Config ###


# Though this isn't an elegent solution, it seems as though environment
# variables aren't properly updated if the config file is read inside a
# function. So instead it is simply loaded here when hrl is imported. I
# should probably try to improve this, but it's relatively a non issue.

cfg = cp.RawConfigParser()
cfg.read([os.path.expanduser('~/.config/hrlrc'),os.path.expanduser('~/.hrlrc')])
os.environ['DISPLAY'] = cfg.get('DataPixx','display')


### HRL Class ###


class HRL:
    """
    HRL (High Resoultion Luminance) is module which provides a set
    of tools for assembling a psychophysics experiment using OpenGL to
    control the display, and DataPixx to control the datapixx graphics
    card and the ResponsePixx input box. This technology allows the
    presentation of stimuli with high temporal accuracy and contrast
    resolution.

    HRL wraps the control of a number of devices into one object of
    class HRL, and manages hardware based on a number of initialization
    arguments. So far this includes openGL, dataPixx, responsePixx, and
    optiCAL, and gamma correction. For a general overview see the module
    description.  Ideally, all programming should be possible through
    HRL alone, without the need to import OpenGL, pygame, or any other
    such core libraries.

    One of the key features of HRL is the generation and incorporation
    of gamma function data. In order to use this functionality, a few
    things need to be done. First, the gamma.py script must be used to
    sample from the monitor's intensity-luminance function. Second, the
    functions in hrl.lut must be used to generate a look up table. Then,
    on initialization an HRL object can read the look up table, and
    based on this table automatically linearize (by inverting the gamma
    function) the intensities of new textures created with HRL.

    Another feature of HRL is the ability to define a coordinate system
    however you wish. HRL accepts a coords 4-tuple corresponding to the
    (left,right,bottom,top) of the screen, and a flipcoords argument
    which when true means coordinates are given in (y,x) coordinates as
    opposed to (x,y). By default coords=(0,1,1,0) and flipcoords is True,
    producing a matrix style coordinate system, i.e. the y axis is the
    first value in the pair, and the top left corner of the screen is
    the origin. A coordinate system with the origin at the centre of the
    screen with the x axis as the first element of the tuple can be made
    with coords=(-0.5,0.5,-0.5,0.5) and clfip=False. Note that the only
    thing that this modifies entirely are texture size and position
    arguments.  Usage of other openGL functions for example may not work
    as expected.

    An optional aspect of HRLs functionality is the ability to
    automatically read design matrices, and print out result matrices.
    While this functionality is little more than a reexportation of
    python's csv package, it can still simplify the code of many
    experiment scripts. These features can be activated with the
    appropriate hrl initializaiton arguments. When activated, the
    corresponding HRL instance has the fields dmtx, and rmtx added to
    it. hrl.dmtx is an iterator over the lines of the design matrix and
    can be used for example in a for loop - 'for dsgn in hrl.dmtx:'.
    hrl.rmtx is a dictionary which is written to the result matrix file
    when hrl.writeResultLine() is called.
    """


    ## Core methods ##


    def __init__(self,wdth=1024,hght=768,bg=0.0
                 ,coords=(0,1,1,0),flipcoords=True
                 ,pgauto=True,fs=False,db=True
                 ,dpx=False,btns=['Green','Red']
                 ,ocal=False
                 ,lut=None
                 ,dfl=None,rfl=None,rhds=None):
        """
        Initialize an HRL object.

        Parameters
        ----------

        wdth : The desired width of the screen. Default: 1024
        hght : The desired height of the screen. Default: 768
        bg : The background luminance on a scale from 0 to 1. Default: 0.0
        coords,flipcoords : Coordinate system definitions. Default:
            (0,1,1,0),True (i.e. Matrix style)
        fs : Whether or not to run in Fullscreen. Be warned that this
            prevents output outside of the program. Default: False
        db : Whether or not to use double buffering. By default this is on and
        should work as expected. However, if the animations aren't behaving as
        expected, it may be worth turning this off.
        pgauto : Whether to automatically initialize pygame. Default: True
        dpx : Boolean indicating the presence of DataPixx. Default: False
        btns : Which button presses will in fact be registered by the
            DataPixx. Default: ['Green','Red']
        ocal : Boolean indiciating the presence of OptiCAL. Default: False
        lut : The location of the gamma table. Default: None
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

        Methods
        -------

        close, newTexture, flip, readButton, readLuminance, checkEscape,
        writeResultLine

        """

        # Datapixx calls
        self._dpx = None
        self._bts = btns
        if dpx: self._dpx = initializeDPX()

        # OpenGL calls
        self._pgauto = pgauto
        if self._pgauto: pg.init()
        if flipcoords:
            self._flipper = lambda (x,y): (y,x)
        else:
            self._flipper = lambda (x,y): (x,y)
        self._coords = coords
        initializeOpenGL(wdth,hght,bg,coords,fs,db)
        self.changeBackground(bg)

        # Optics Calls
        self._ocal = None
        if ocal: self._ocal = initializeOptiCAL(cfg.get('optiCAL','dev'))

        # Design and Result matrices
        self._dfl = None
        if dfl != None:
            self._dfl = open(dfl,'rb')
            self.dmtx = csv.DictReader(self._dfl,delimiter=' ',skipinitialspace=True)
        
        self._rfl = None
        if rfl != None:
            self._rfl = open(rfl,'wb')
            self._rwtr = csv.DictWriter(self._rfl,rhds,delimiter=' ')
            self.rmtx = {}
            #self._rwtr.writeheader() Python 2.7
            self._rfl.write(' '.join(rhds) + '\r\n')

        # Gamma Function Correction
        self._lut = None
        self._gammainv = lambda x: x
        if lut != None:
            self._lut = np.genfromtxt(lut,skip_header=1)
            self._gammainv = lambda x: np.interp(x,self._lut[:,0],self._lut[:,1])

    def close(self):
        """
        Closes all the devices and systems maintained by the HRL object.
        This should be called at the end of the program.
        """
        if self._dpx != None: self._dpx.close()
        if self._rfl != None: self._rfl.close()
        if self._dfl != None: self._dfl.close()
        if self._pgauto: pg.quit()


    ## OpenGL methods ##


    def newTexture(self,txt,shape='square'):
        """
        Given a numpy array of values between 0 and 1, returns a new
        Texture object. The texture object comes equipped with the draw
        method for obvious purposes. If a gamma table has been given,
        the texture will be adjusted by inverting the gamma
        function.

        Parameters
        ----------
        txt : The numpy corresponding to the texture.
        shape : The shape 'cut out' of the texture to show. A square
            will show the whole thing. Available: 'square', 'circle'
            Default: 'square'

        Returns
        -------
        Texture object

        """
        return Texture(txt,shape,self._gammainv,self._coords,self._flipper
                       ,self._dpx != None)

    def changeBackground(self,bg):
        changeBackground(bg,self._dpx != None)

    def flip(self,clr=True,dur=None):
        """
        Flips in the image backbuffer. In general, one will want to draw
        a set of textures and then call flip to draw them all to the
        screen at once.

        Takes a clr argument which causes the back buffer to clear after
        the flip. When off, textures will be drawn on top of the
        displayed buffer.

        Also takes an optional duration (dur) argument. If dur != None,
        then the flip command will pause execution for the specified
        number of milliseconds, and then flip the empty buffer forward.
        i.e. if you don't use any other draw commands while it is
        waiting, it will blank the screen after the specified amount of
        time has elapsed.

        Parameters
        ----------
        clr : Whether to clear the back buffer after flip.
        dur : How long to wait before performing a second flip.

        Returns
        -------
        None
        """
        pg.display.flip()
        if clr: glClear(GL_COLOR_BUFFER_BIT)
        if dur != None:
            pg.time.delay(dur)
            pg.display.flip()


    ## IO methods ##


    def readButton(self,to=3600):
        """
        Reads a value from the ResponsePixx, returning a (colour,time)
        pair, where colour is the colour of the botton pressed, and time
        is the delay between the initial call and the eventual button
        press.
        
        readButton also depends on an initial list of buttons. Only the
        provided button colours will register as a button press. If an
        unlisted colour is pressed, HRL will ignore it and the delay
        clock will keep counting.

        readButton also accepts a timeout, causing readButton to return
        none if this time is exceeded.

        Parameters
        ----------
        to : How long the readButton will wait for a response in
        seconds, returning None if it fails. default = 3600.

        Returns
        -------
        (button,time) where button is the colour name of the
        button pressed, and time is the amount of time in milliseconds
        it took from the initial call to the press.
        """
        if self._dpx != None:
            (btn,tm) = buttonLoop(self._dpx,self._bts,timeout=to)
            return (btn,tm*1000.0)

        else:
            return keyboardLoop(self._bts,timeout=to*1000)

    def readLuminance(self,trs=5,slptm=200):
        """
        Attempts to read a value from the OptiCAL. Since this may
        occasionally fail, tryReadLuminance tries the reading trs times,
        with a wait time of slptm between each try.

        Parameters
        ----------
        trs : The number of reading attempts to make. Default: 5
        slptm : Delay between read attempts. Default: 200
        """
        return tryReadLuminance(self._ocal,trs,slptm)

    def checkEscape(self):
        """
        A simple function which queries pygame as to whether the Escape key
        has been pressed since the last call, and returns true if it
        has. This function be used within the core loop of the program,
        to allow the user to trigger an event which quits the loop, e.g.
        if hrl.checkEscape(): break
        """
        eventlist = pg.event.get()
        for event in eventlist:
            if event.type == QUIT \
               or event.type == KEYDOWN and event.key == K_ESCAPE:
                return True


    ## File methods ##


    def writeResultLine(self,dct=None):
        """
        Given an appropriate dicitonary of values, writes the line to
        the result file. The dictionary must include all the names given
        to the hrl instance when it was initialized. i.e. if the
        rhds=['Input','Output'] then dct must have elements dct['Input']
        and dct['Output'].

        By default, hrl uses the dictionary hrl.rmtx, but the dictionary
        can be given directly if desired.

        Parameters
        ----------
        dct : The dictionary of results in the current trial.
        """
        if dct is None:
            self._rwtr.writerow(self.rmtx)
        else:
            self._rwtr.writerow(dct)
