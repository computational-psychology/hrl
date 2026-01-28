from functools import partial

import numpy as np

from hrl.luts import gamma_correct_grey, gamma_correct_RGB

from .graphics import Graphics

## Class ##


class GPU_grey(Graphics):
    """Standard GPU in greyscale mode with 8-bit per channel resolution.

    Encodes greyscale values by duplicating them across R, G, B channels,
    providing standard 8-bit (256 level) intensity resolution.

    Attributes
    ----------
    bitdepth : int
        bit depth per physical channel (8)

    See Also
    --------
    GPU_RGB : RGB mode for standard GPUs
    DATAPixx : 16-bit greyscale for VPixx DataPixx hardware
    VIEWPixx_grey : 16-bit greyscale for VPixx ViewPixx hardware
    """

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
        """Convert greyscale image to 4-channel RGBA representation.

        Encodes greyscale values by setting R = G = B = intensity, with
        alpha channel at maximum. Provides 8-bit (256 level) resolution.

        Parameters
        ----------
        img : ndarray
            input greyscale image with values in [0.0, 1.0] and shape (H, W)

        Returns
        -------
        tuple of (ndarray, ndarray, ndarray, int)
            4-channel representation as (R, G, B, Alpha) where R=G=B=intensity
            and Alpha=255
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
    """Standard GPU in RGB mode with 8-bit per channel resolution.

    Provides standard 3-channel RGB output with 8-bit (256 level) resolution
    per color channel.

    Attributes
    ----------
    bitdepth : int
        bit depth per physical channel (8)

    See Also
    --------
    GPU_grey : greyscale mode for standard GPUs
    VIEWPixx_RGB : RGB mode for VPixx ViewPixx hardware
    """

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
