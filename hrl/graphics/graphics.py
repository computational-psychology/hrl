"""Graphics device interfaces for HRL psychophysics displays.

This module provides abstract and concrete classes for interfacing with various
display hardware devices through OpenGL. The class hierarchy is organized by
display mode (greyscale vs. RGB) and device type (GPU, DataPixx, ViewPixx).

Class Hierarchy
---------------
Graphics (ABC)
    Base abstract class defining common OpenGL initialization and texture
    creation pipeline.

Device Classes
--------------
GPU_grey, GPU_RGB
    Standard GPU displays with 8-bit per channel resolution.

DATAPixx
    VPixx DataPixx device in M16 mode for 16-bit greyscale (R-G concatenation).

VIEWPixx_grey, VIEWPixx_RGB
    VPixx ViewPixx 3D device in M16 mode (greyscale) or C24 mode (RGB).

Image Processing Pipeline
--------------------------
The image presentation pipeline consists of:

1. Input array: numpy array with values in [0.0, 1.0]
   - Greyscale: shape (H, W)
   - RGB: shape (H, W, 3)

2. Gamma correction: optional LookUp Table (LUT) or Color LookUp Table (CLUT)
   application for linearization

3. Channel encoding: conversion to device-specific RGBA representation
   - GPU: 8-bit per channel
   - DataPixx/ViewPixx M16: 16-bit via R-G concatenation

4. Texture creation: OpenGL texture object ready for display

Notes
-----
The coordinate system follows matrix conventions: origin at top-left,
increasing rightward and downward. This matches numpy array indexing.

Texture objects are created via Graphics.newTexture() and come equipped with
a draw() method for rendering to the display.
"""

from abc import ABC, abstractmethod

import numpy as np
import OpenGL.GL as opengl
import pygame

from hrl.graphics.texture import Texture, deleteTexture, deleteTextureDL


class Graphics(ABC):
    """Abstract base class for all graphics display devices.

    Provides common OpenGL initialization, window management, and texture
    creation pipeline. Subclasses must implement device-specific channel
    encoding via the channels_from_img() method.

    This class handles:
    - OpenGL context and window initialization
    - Display buffer management (flip, clear)
    - LookUp Table (LUT) loading for gamma correction
    - Texture object creation from numpy arrays
    - Background color management

    Attributes
    ----------
    screen : pygame.Surface
        the OpenGL display surface
    width : int
        window width in pixels
    height : int
        window height in pixels
    background : float or ndarray
        current background value(s)
    bitdepth : int
        bit depth per physical channel (set by subclasses)

    Notes
    -----
    Do not instantiate this class directly. Use concrete subclasses like
    GPU_grey, GPU_RGB, DATAPixx, VIEWPixx_grey, or VIEWPixx_RGB.
    """

    @abstractmethod
    def channels_from_img(self, img):
        """Convert image array to device-specific RGBA channel representation.

        Device-specific method that encodes image values as 4-channel RGBA
        tuples according to the hardware's requirements (e.g., 8-bit per
        channel for GPU, 16-bit via R-G concatenation for DataPixx).

        Parameters
        ----------
        img : ndarray
            input image array with values in [0.0, 1.0].
            - For greyscale devices: shape (H, W)
            - For RGB devices: shape (H, W, 3)

        Returns
        -------
        tuple of ndarray or int
            4-channel RGBA representation as (R, G, B, Alpha).
            Format is device-specific (e.g., uint8 arrays, scalars).
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
        """Initialize OpenGL context and display window.

        Parameters
        ----------
        width : int
            window width in pixels
        height : int
            window height in pixels
        background : float or array-like
            initial background value. Interpretation depends on subclass:
            - Greyscale: float in [0.0, 1.0]
            - RGB: float or (r, g, b) tuple in [0.0, 1.0]
        fullscreen : bool, optional
            enable fullscreen display mode, by default False
        double_buffer : bool, optional
            enable double buffering for smooth rendering, by default True
        lut : str, optional
            path to LookUp Table (LUT) or Color LookUp Table (CLUT) file
            for gamma correction, by default None
        mouse : bool, optional
            show mouse cursor, by default False
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
        """Pack RGBA channels into 32-bit bytestring for OpenGL.

        Combines separate R, G, B, Alpha channel arrays into a single
        packed 32-bit integer representation suitable for OpenGL texture upload.

        Parameters
        ----------
        R : ndarray or int
            red channel values
        G : ndarray or int
            green channel values
        B : ndarray or int
            blue channel values
        Alpha : ndarray or int
            alpha channel values

        Returns
        -------
        bytes
            packed 32-bit RGBA bytestring for OpenGL texture data
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
        """Create OpenGL texture from image array.

        Applies gamma correction (if LUT provided), converts to device-specific
        channel encoding, and creates an OpenGL texture object ready for display.

        Parameters
        ----------
        arr0 : ndarray
            input image array with values in [0.0, 1.0].
            - For greyscale: shape (H, W)
            - For RGB: shape (H, W, 3)
        shape : {'square', 'circle'}, optional
            shape mask to apply to texture, by default 'square'.
            'circle' creates a circular aperture.

        Returns
        -------
        Texture
            texture object with draw() method for rendering

        Notes
        -----
        Images use matrix-style coordinates: origin at top-left, increasing
        rightward (x) and downward (y). This matches numpy array indexing.
        """
        arr = self.gamma_correct(arr0)

        byts = self.bytestring_from_channels(*self.channels_from_img(arr))

        return Texture(byts, arr0.shape[1], arr0.shape[0], shape)

    def flip(self, clr=True):
        """Swap display buffers to show rendered content.

        Swaps the back buffer (where drawing occurs) with the front buffer
        (what is displayed). This is the standard way to present stimuli
        after drawing textures.

        Parameters
        ----------
        clr : bool, optional
            clear the back buffer after flipping, by default True.
            Set to False to accumulate drawings across frames (useful for
            performance-sensitive scenarios).
        """
        pygame.display.flip()
        if clr:
            opengl.glClear(opengl.GL_COLOR_BUFFER_BIT)

    def changeBackground(self, background):
        """Change display background color or intensity.

        Parameters
        ----------
        background : float or ndarray
            new background value(s) in [0.0, 1.0].
            Interpretation depends on subclass:
            - Greyscale: float intensity
            - RGB: float (grey) or shape (1, 1, 3) array (r, g, b)
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
