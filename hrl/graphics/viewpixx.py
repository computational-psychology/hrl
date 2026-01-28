from functools import partial

import numpy as np

from hrl.luts import gamma_correct_grey, gamma_correct_RGB

from .graphics import Graphics

## Class ##


class VIEWPixx_grey(Graphics):
    """VPixx ViewPixx 3D in M16 mode for 16-bit greyscale resolution.

    Uses M16 video mode which concatenates the R and G channels to achieve
    16-bit (65536 level) greyscale resolution. This enables high-precision
    luminance control for psychophysics experiments.

    The device connection is established automatically during initialization.

    Attributes
    ----------
    bitdepth : int
        bit depth per physical channel (8, but combined to 16-bit)
    device : VIEWPixx3D
        pypixxlib device instance for hardware communication

    See Also
    --------
    VIEWPixx_RGB : RGB mode for ViewPixx hardware
    DATAPixx : 16-bit greyscale for DataPixx hardware
    GPU_grey : standard 8-bit greyscale
    """

    bitdepth = 8  # bit depth per physical channel
    device = None

    def __init__(self, *args, **kwargs):
        # Open hardware connection
        from pypixxlib.viewpixx import VIEWPixx3D as device

        self.device = device()

        # Set video mode to M16: concatente R & G channels for 16-bit greyscale
        mode = self.device.getVideoMode()
        print(f"Current video mode: {mode}")

        if mode != "M16":
            print("Setting video mode to M16...")
            self.device.setVideoMode("M16")
            self.device.updateRegisterCache()
            mode = self.device.getVideoMode()
            print(f"Video mode now: {mode}")

        # Call parent initializer
        super().__init__(*args, **kwargs)

        # Enable gamma correction
        if self._lut is not None:
            # TODO: validate LUT shape
            self.gamma_correct = partial(gamma_correct_grey, LUT=self._lut)

        # Here we change the default color
        self.changeBackground(np.array(kwargs.get("background", 0.5)))
        self.flip()

    def channels_from_img(self, img):
        """Convert greyscale image to 16-bit R-G concatenated representation.

        Encodes greyscale values by concatenating two 8-bit channels (R and G)
        to form a 16-bit (65536 level) resolution. This is the format required
        by ViewPixx M16 video mode for high-precision greyscale output.

        Parameters
        ----------
        img : ndarray
            input greyscale image with values in [0.0, 1.0] and shape (H, W)

        Returns
        -------
        tuple of (ndarray, ndarray, int, int)
            4-channel representation as (R, G, B, Alpha) where:
            - R = high byte (bits 8-15)
            - G = low byte (bits 0-7)
            - B = 0 (unused)
            - Alpha = 255
        """
        assert img.ndim <= 2, "Input image must be single-channel HxW array"

        # Discretize to 16-bit integers, single channel
        arr = img * (2 ** (2 * self.bitdepth) - 1)
        arr = np.uint32(arr)

        # Convert to datapixx R-G concatenated format
        channels = (
            arr // (2**self.bitdepth),  # R channel (high byte)
            arr % (2**self.bitdepth),  # G channel (low byte)
            0,  # B channel (not used)
            2**self.bitdepth - 1,  # Alpha channel (max intensity)
        )

        return channels


class VIEWPixx_RGB(Graphics):
    """VPixx ViewPixx 3D in C24 mode for RGB color display.

    Uses C24 video mode which provides standard 8-bit per channel RGB output
    with 256 levels per color channel.

    The device connection is established automatically during initialization.

    Attributes
    ----------
    bitdepth : int
        bit depth per physical channel (8)
    device : VIEWPixx3D
        pypixxlib device instance for hardware communication

    See Also
    --------
    VIEWPixx_grey : greyscale mode for ViewPixx hardware
    GPU_RGB : RGB mode for standard GPUs
    """

    bitdepth = 8  # bit depth per physical channel

    def __init__(self, *args, **kwargs):
        # Open hardware connection
        from pypixxlib.viewpixx import VIEWPixx3D as device

        self.device = device()

        # Set video mode to C24: regular 8-bit per channel RGB
        mode = self.device.getVideoMode()
        print(f"Current video mode: {mode}")

        if mode != "C24":
            print("Setting video mode to C24...")
            self.device.setVideoMode("C24")
            self.device.updateRegisterCache()
            mode = self.device.getVideoMode()
            print(f"Video mode now: {mode}")

        # Call parent initializer
        super().__init__(*args, **kwargs)

        # Enable gamma correction
        if self._lut is not None:
            # TODO: validate LUT shape
            self.gamma_correct = partial(gamma_correct_RGB, CLUT=self._lut)

        # Set the background color
        self.changeBackground(np.array(kwargs.get("background", [0.5, 0.5, 0.5])).reshape(1, 1, 3))
        self.flip()

    def channels_from_img(self, img):
        """Convert RGB image to 4-channel RGBA representation.

        Encodes each R, G, B channel independently with 8-bit resolution,
        with alpha channel at maximum.

        Parameters
        ----------
        img : ndarray
            input RGB image with values in [0.0, 1.0] and shape (H, W, 3)

        Returns
        -------
        tuple of (ndarray, ndarray, ndarray, int)
            4-channel representation as (R, G, B, Alpha) with separate
            8-bit arrays for each color channel and Alpha=255
        """

        assert img.ndim == 3 and img.shape[2] == 3, "Input image must be 3-channel HxWx3 array"

        # Discretize to 8-bit integers, single channel
        arr = img * (2**self.bitdepth - 1)
        arr = np.uint32(arr)

        # Convert to 4 channels, with max alpha
        arr = (
            arr[:, :, 0],  # R channel
            arr[:, :, 1],  # G channel
            arr[:, :, 2],  # B channel
            2**self.bitdepth - 1,  # Alpha channel (max intensity)
        )

        return arr
