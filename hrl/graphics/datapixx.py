from functools import partial

import numpy as np

from hrl.luts import gamma_correct_grey

from .graphics import Graphics

## Class ##


class DATAPixx(Graphics):
    """VPixx DataPixx in M16 mode for 16-bit greyscale resolution.

    Uses M16 video mode which concatenates the R and G channels to achieve
    16-bit (65536 level) greyscale resolution. This enables high-precision
    luminance control for psychophysics experiments.

    The device connection is established automatically during initialization
    and closed via the close() method.

    Attributes
    ----------
    bitdepth : int
        bit depth per physical channel (8, but combined to 16-bit)
    device : DATAPixx
        pypixxlib device instance for hardware communication

    See Also
    --------
    GPU_grey : standard 8-bit greyscale
    VIEWPixx_grey : 16-bit greyscale for VPixx ViewPixx hardware
    """

    bitdepth = 8  # bit depth per physical channel
    device = None

    def __init__(self, *args, **kwargs):
        # Open hardware connection
        from pypixxlib.datapixx import DATAPixx as device

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

    def close(self):
        """Close connection to DataPixx hardware device.

        Should be called when finished with the device to properly release
        hardware resources.
        """
        self.device.close()

    def channels_from_img(self, img):
        """Convert greyscale image to 16-bit R-G concatenated representation.

        Encodes greyscale values by concatenating two 8-bit channels (R and G)
        to form a 16-bit (65536 level) resolution. This is the format required
        by DataPixx M16 video mode for high-precision greyscale output.

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
