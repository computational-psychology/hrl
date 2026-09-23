"""Tests for how each graphics device turns image values into integer channel values.

These run without the hardware: `channels_from_img` only needs the class's bit depth,
so it is called on an instance that skips `__init__`.

The values must be rounded to the nearest level, not truncated. Truncating puts every
value up to one level too low -- on a CLUT-corrected ViewPixx in 8-bit color, enough to
move a neutral background by dE 1.6 in CIELUV and darken everything by about 0.25 L*.
"""

import numpy as np
import pytest

from hrl.graphics.datapixx import DATAPixx
from hrl.graphics.gpu import GPU_grey, GPU_RGB
from hrl.graphics.viewpixx import VIEWPixx_grey, VIEWPixx_RGB


def _device(cls):
    return cls.__new__(cls)


def _level(channels, cls):
    """The single integer level a device's channels encode, per pixel."""
    red, green, blue = (np.asarray(channel) for channel in channels[:3])
    if cls in (VIEWPixx_grey, DATAPixx):  # 16 bit, R high byte and G low byte
        return red * 2**cls.bitdepth + green
    if cls is GPU_grey:  # the same 8-bit value in all three
        return red
    return np.stack([red, green, blue], axis=-1)  # 8 bits per color channel


GREY = [VIEWPixx_grey, DATAPixx, GPU_grey]
RGB = [VIEWPixx_RGB, GPU_RGB]


def _maximum(cls):
    return 2 ** (2 * cls.bitdepth) - 1 if cls in (VIEWPixx_grey, DATAPixx) else 2**cls.bitdepth - 1


@pytest.mark.parametrize("cls", GREY + RGB)
def test_values_round_to_the_nearest_level(cls):
    top = _maximum(cls)
    wanted = np.array([0.0, 100.4, 100.5, 100.6, 101.0, top])
    img = wanted / top
    if cls in RGB:
        img = np.stack([img, img, img], axis=-1)[None]

    got = _level(_device(cls).channels_from_img(img), cls)

    expected = np.round(wanted).astype(int)
    if cls in RGB:
        expected = np.stack([expected] * 3, axis=-1)[None]
    np.testing.assert_array_equal(got, expected)


@pytest.mark.parametrize("cls", GREY + RGB)
def test_black_and_white_are_the_ends_of_the_range(cls):
    img = np.array([0.0, 1.0])
    if cls in RGB:
        img = np.stack([img, img, img], axis=-1)[None]

    got = np.asarray(_level(_device(cls).channels_from_img(img), cls)).reshape(-1)

    assert got.min() == 0
    assert got.max() == _maximum(cls)


def test_color_channels_are_rounded_independently():
    top = 2**VIEWPixx_RGB.bitdepth - 1
    img = np.array([[[10.6, 20.4, 30.5]]]) / top

    got = _level(_device(VIEWPixx_RGB).channels_from_img(img), VIEWPixx_RGB)

    np.testing.assert_array_equal(got, [[[11, 20, 30]]])
