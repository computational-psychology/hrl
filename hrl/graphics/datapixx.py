from functools import partial

import numpy as np

from hrl.luts import gamma_correct_grey

from .graphics import Graphics

## Class ##


class DATAPixx(Graphics):
    """Graphics interface for 6-bit high-resolution greyscale for DataPixx devices"""

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
        """Close connection to DataPixx device"""
        self.device.close()

    def channels_from_img(self, img):
        """Convert greyscale image in [0.0, 1.0] to 4-channel, 8-bit integer representation

        The four channel representation concatenates two 8-bit channels (R & G)
        to form a 16-bit resolution, single-channel image.
        This is the format required by the DataPixx DAC for high bit-depth greyscale output.

        Parameters
        ----------
        img : Array[float]
            Input greyscale image with values in [0.0, 1.0]

        Returns
        -------
        Tuple[Array[uint8]]
            4-channel representation as tuple of 8-bit integer arrays (R, G, B, Alpha)
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
