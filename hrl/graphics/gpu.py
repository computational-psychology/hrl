from functools import partial

import numpy as np

from hrl.luts import gamma_correct_grey, gamma_correct_RGB

from .graphics import Graphics

## Class ##


class GPU_grey(Graphics):
    """Graphics interface for 1-channel, 8-bit greyscale representation on standard GPUs"""

    bitdepth = 8  # bit depth per physical channel

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Enable gamma correction
        if self._lut is not None:
            # TODO: validate LUT shape
            self.gamma_correct = partial(gamma_correct_grey, LUT=self._lut)

        # Set the background intensity
        self.changeBackground(np.array(kwargs.get("background", 0.5)))
        self.flip()

    def channels_from_img(self, img):
        """Convert greyscale image in [0.0, 1.0] to 4-channel, 8-bit integer representation

        The 32 bit channel representation is simply an 8-bit integer n
        equal across the red, green, and blue channels,
        with the alpha channel set to the max int.

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

        # Discretize to 8-bit integers, single channel
        arr = img * (2**self.bitdepth - 1)
        arr = np.uint32(arr)

        # Duplicate to 4 channels, with max alpha
        channels = (
            arr,  # R channel
            arr,  # G channel
            arr,  # B channel
            2**self.bitdepth - 1,  # Alpha channel (max intensity)
        )

        return channels


class GPU_RGB(Graphics):
    """Graphics interface for standard 3-channel, 8-bit RGB representation on standard GPUs"""

    bitdepth = 8  # bit depth per channel

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Enable gamma correction
        if self._lut is not None:
            # TODO: validate LUT shape
            self.gamma_correct = partial(gamma_correct_RGB, CLUT=self._lut)

        # Set the background color
        self.changeBackground(np.array(kwargs.get("background", [0.5, 0.5, 0.5])).reshape(1, 1, 3))
        self.flip()

    def channels_from_img(self, img):
        """Converts an HxWx3 RGB image in [0.0, 1.0] to 4-channel, 8-bit integer representation

        The 32 bit channel representation is simply the 8-bit integer discretization
        for each of the R, G, and B channels,
        with the alpha channel set to the max int.

        Parameters
        ----------
        img : Array[float]
            Input RGB image with values in [0.0, 1.0]

        Returns
        -------
        Tuple[Array[uint8]]
            4-channel representation as tuple of 8-bit integer arrays (R, G, B, Alpha)

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
