"""
This is the HRL submodule for handling graphics devices and OpenGL. Graphics
devices in HRL instantiate the 'Graphics' abstract class, which defines the
common functions required for displaying greyscale images.

Image presentation in HRL can be understood as a multi step process as follows:

    Bitmap (The image written in an 8 bit, 4 channel format)
    -> Greyscale Array (A numpy array of doubles between 0 and 1)
    -> Processed Greyscale Array (A Gresycale Array remapped with a lookup table)
    -> Display List (An index to a stored texture in graphical memory)
    -> Texture (A python class instance which can be drawn)

i) The conversion of Bitmaps to Greyscale arrays is handled by functions in
'hrl.extra' Where possible, it is recommended to bypass this step and work
directly with numpy arrays.

ii) The conversion of Greyscale Arrays to Processed Greyscale Arrays is handled by
the base 'hrl' class, and consists primarily of gamma correction and contrast
range selection.

iii) Saving a Processed Greyscale Array into graphics memory and interacting
with it as a Texture object is handled in this module.

The 'Texture' class is a wrapper for certain OpenGL functions designed to
simplify the display of individual 2d images.  The sole method of the Texture
class is 'draw'.

Texture objects are not meant to be created on their own, but are instead
created via the 'newTexture' method of Graphics. Graphics.newTexture will take
a given Processed Greyscale Array (with other optional arguments as well), and
return it as Texture object designed to be shown on the particular Graphics
object.

The openGL code was based largely on a great tutorial by a mysterious tutor
here: http://disruption.ca/gutil/introduction.html
"""

from abc import ABC, abstractmethod

import numpy as np
import OpenGL.GL as opengl
import pygame

from hrl.graphics.texture import Texture


class Graphics(ABC):
    """
    The Graphics abstract base class. New graphics hardware must instantiate
    this class. The key method is 'greyToChannels', which defines how to
    represent a greyscale value between 0 and 1 as a 4-tuple (r,g,b,a), so that
    the given grey value is correctly on the Graphics backend.
    """

    @abstractmethod
    def greyToChannels(self, gry):
        """
        Converts a single greyscale value into a 4 colour channel representation
        specific to self (the graphics backend).

        Parameters
        ----------
        gry : The grey value

        Returns
        -------
        (r,g,b,a) the grey represented as a corresponding 4-tuple
        """
        ...

    def __init__(
        self,
        width,
        height,
        background,
        fullscreen=False,
        double_buffer=True,
        lut=None,
        mouse=False,
    ):
        """
        The Graphics constructor predefines the basic OpenGL initializations
        that must be performed regardless of the specific backends.

        Parameters
        ----------
        width : The width (in pixels) of the openGL window
        height : The height (in pixels) of the openGL window
        background : The default background grey value (between 0 and 1)
        fullscreen : Enable fullscreen display (Boolean) Default: False
        double_buffer : Enable double buffering (Boolean) Default: True
        lut : filepath to lookup table to use
        mouse: Enable mouse cursor to be visible. Default: False

        Returns
        -------
        Graphics object
        """

        # Process options
        dbit = pg.OPENGL
        if double_buffer:
            dbit = dbit | pg.DOUBLEBUF
        if fullscreen:
            dbit = dbit | pg.FULLSCREEN | pg.NOFRAME

        # Initialize screen
        self.screen = pg.display.set_mode((width, height), dbit, vsync=1)
        self.width = width
        self.height = height

        # Hide mouse cursor
        if not mouse:
            pg.mouse.set_visible(False)

        # Disables this thing
        gl.glDisable(gl.GL_DEPTH_TEST)

        # Set Matrix style coordinate system.
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0, width, height, 0, -1, 1)
        gl.glMatrixMode(gl.GL_MODELVIEW)

        # Enable texturing
        gl.glEnable(gl.GL_TEXTURE_2D)

        # Enable blending
        gl.glEnable(gl.GL_BLEND)
        # Blend settings. Blending is unrelated to e.g. magnification.
        # Blending is how the colours from transluscent objects are
        # combined, and is therefore largely irrelevant.
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        # Gamma Function Correction
        self._lut = None
        self._gammainv = lambda x: x
        if lut != None:
            print("..using look-up table: %s" % lut)
            self._lut = np.genfromtxt(lut, skip_header=1)
            self._gammainv = lambda x: np.interp(x, self._lut[:, 0], self._lut[:, 1])

        # Here we change the default color
        self.changeBackground(background)
        self.flip()

    def newTexture(self, grys0, shape="square"):
        """
        Given a numpy array of values between 0 and 1, returns a new
        Texture object. The texture object comes equipped with the draw
        method for obvious purposes.

        NB: Images in HRL are represented in matrix style coordinates. i.e. the
        origin is in the upper left corner, and increases to the right and
        downwards.

        Parameters
        ----------
        grys : The greyscale numpy array
        shape : The shape to 'cut out' of the given greyscale array. A square
            will render the entire array. Available: 'square', 'circle'
            Default: 'square'

        Returns
        -------
        Texture object
        """
        grys = np.flipud(grys0)  # flipping up-down necessary
        grys = self._gammainv(grys)  # added gamma correction

        byts = channelsToInt(self.greyToChannels(grys[::-1,])).tostring()
        wdth = len(grys[0])
        hght = len(grys[:, 0])

        return Texture(byts, wdth, hght, shape)

    def flip(self, clr=True):
        """
        Flips in the image backbuffer. In general, one will want to draw
        a set of Textures and then call flip to display them all at once.

        Takes a clr argument which causes the back buffer to clear after
        the flip. When off, textures will be drawn on top of the current back
        buffer. By default the back buffer will be cleared automatically, but in
        performance sensitive scenarios it may be worth turning this off.

        Parameters
        ----------
        clr : Whether to clear the back buffer after flip. Default: True
        """
        pg.display.flip()
        if clr:
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    def changeBackground(self, bg):
        """
        Changes the current background grey value.

        Parameters
        ----------
        bg : The new gray value (between 0 and 1)
        """
        mx = float(2**8 - 1)
        (r, g, b, a) = self.greyToChannels(self._gammainv(bg))
        gl.glClearColor(r / mx, g / mx, b / mx, a / mx)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)


def channelsToInt(t):
    """
    Takes a channel representation and returns a corresponding unsigned 32 bit
    int.  Running the tostring method on a 2d array which has had this function
    applied to it will produce a bytestring appropriate for use as a texture
    with openGL.
    """
    r, g, b, a = t
    R = 2**0
    G = 2**8
    B = 2**16
    A = 2**24
    return r * R + g * G + b * B + a * A
