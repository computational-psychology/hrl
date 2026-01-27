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

from hrl.graphics.texture import Texture, deleteTexture, deleteTextureDL


class Graphics(ABC):
    """
    The Graphics abstract base class. New graphics hardware must instantiate
    this class. The key method is 'greyToChannels', which defines how to
    represent a greyscale value between 0 and 1 as a 4-tuple (r,g,b,a), so that
    the given grey value is correctly on the Graphics backend.
    """

    @abstractmethod
    def channels_from_img(self, gry):
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

        # OpenGL options
        dbit = pygame.OPENGL
        if double_buffer:
            dbit = dbit | pygame.DOUBLEBUF
        if fullscreen:
            dbit = dbit | pygame.FULLSCREEN | pygame.NOFRAME

        # Initialize screen
        self.screen = pygame.display.set_mode((width, height), dbit, vsync=1)
        self.width = width
        self.height = height

        # Hide mouse cursor
        if not mouse:
            pygame.mouse.set_visible(False)

        # Disables depth test
        # not needed as we're only doing 2D rendering
        opengl.glDisable(opengl.GL_DEPTH_TEST)

        # Set Matrix style coordinate system.
        opengl.glMatrixMode(opengl.GL_PROJECTION)
        opengl.glLoadIdentity()
        opengl.glOrtho(0, width, height, 0, -1, 1)
        opengl.glMatrixMode(opengl.GL_MODELVIEW)

        # Enable texturing
        opengl.glEnable(opengl.GL_TEXTURE_2D)

        # Enable blending
        opengl.glEnable(opengl.GL_BLEND)
        # Blend settings. Blending is unrelated to e.g. magnification.
        # Blending is how the colours from transluscent objects are
        # combined, and is therefore largely irrelevant.
        opengl.glBlendFunc(opengl.GL_SRC_ALPHA, opengl.GL_ONE_MINUS_SRC_ALPHA)

        # Enable gamma correction
        if lut is not None:
            # Load specified LUT
            print(f"..using look-up table: {lut}")
            self._lut = np.genfromtxt(lut, skip_header=1)
        else:  # No LUT provided
            self._lut = None
            self._gamma_correct = lambda x: x  # By default, no gamma correction: identity function

    def bytestring_from_channels(self, R, G, B, Alpha):
        """Convert 4-channel, 8-bit integer representation to single-channel 32-bit bytestring

        Parameters
        ----------
        R, G, B, Alpha : Array[uint8]
            4-channel representation as tuple of 8-bit integer arrays (R, G, B, Alpha)

        Returns
        -------
        bytes
            Single-channel 32-bit bytestring representation
        """
        # Define bit shifts for each channel
        r = 2**0
        g = 2 ** (self.bitdepth)
        b = 2 ** (self.bitdepth * 2)
        alpha = 2 ** (self.bitdepth * 3)

        # Combine channels into single 32-bit integer representation
        bitint = (R * r) + (G * g) + (B * b) + (Alpha * alpha)
        return bitint.tobytes()

    def gamma_correct(self, img):
        return img

    def newTexture(self, arr0, shape="square"):
        """
        Given a numpy array of values between 0 and 1, returns a new
        Texture object. The texture object comes equipped with the draw
        method for obvious purposes.

        NB: Images in HRL are represented in matrix style coordinates. i.e. the
        origin is in the upper left corner, and increases to the right and
        downwards.

        Parameters
        ----------
        arr0  : The (greyscale or color) numpy array
        shape : The shape to 'cut out' of the given greyscale array. A square
            will render the entire array. Available: 'square', 'circle'
            Default: 'square'

        Returns
        -------
        Texture object
        """
        arr = self.gamma_correct(arr0)

        byts = self.bytestring_from_channels(*self.channels_from_img(arr))

        return Texture(byts, arr0.shape[1], arr0.shape[0], shape)

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
        pygame.display.flip()
        if clr:
            opengl.glClear(opengl.GL_COLOR_BUFFER_BIT)

    def changeBackground(self, background):
        """Change current background grey value.

        Parameters
        ----------
        intensity_background : float
            new grey value for background, between 0.0 and 1.0
        """
        maximum = float(2**self.bitdepth - 1)

        # Gamma correct input value(s)
        bg = self.gamma_correct(background)

        # Convert to channel representation
        (r, g, b, a) = self.channels_from_img(bg)

        # Set as OpenGL background
        opengl.glClearColor(r / maximum, g / maximum, b / maximum, a / maximum)
        opengl.glClear(opengl.GL_COLOR_BUFFER_BIT)

        self.background = background


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
