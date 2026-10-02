"""Tests for `hrl-util clut show`: the images it draws, and stepping through its screens."""

import types
from unittest.mock import patch

import numpy as np
import pytest

from hrl.cluts import RGB_to_XYZ, achromatic_RGB
from hrl.util.clut import show
from tests.cluts.conftest import DISPLAY_CLUT

CLUT = DISPLAY_CLUT
WHITE_Y = RGB_to_XYZ(np.ones(3), CLUT, per_level=True)[1]
LUMINANCE = WHITE_Y / 2
GREY = achromatic_RGB(CLUT, LUMINANCE, per_level=True)


def _xy(xyz):
    return xyz[:, :2] / xyz.sum(axis=1, keepdims=True)


def test_gamut_shows_each_chromaticity_at_its_brightest():
    image, extent, (row, column) = show.gamut_image(CLUT, GREY, size=60, samples=120)

    shown = np.any(image != GREY, axis=2)
    rgb = image[shown]
    assert 0.2 < shown.mean() < 0.8
    assert np.all(rgb.max(axis=1) == 1.0), "the brightest color has a channel at full input"

    xy = _xy(RGB_to_XYZ(rgb, CLUT, per_level=True))
    assert np.all((xy[:, 0] >= extent[0]) & (xy[:, 0] <= extent[1]))
    assert np.all((xy[:, 1] >= extent[2]) & (xy[:, 1] <= extent[3]))
    assert shown[row, column], "white is inside the gamut"


@pytest.mark.parametrize("name,screen", show.SCREENS)
def test_every_screen_fits_on_the_screen(name, screen):
    width, height = 1024, 768
    state = {"luminance": LUMINANCE, "stripe_width": 2}

    items, background, text = screen(CLUT, state, GREY, width, height)

    assert items and text and background.shape == (3,)
    for image, (x, y) in items:
        assert image.ndim == 3 and image.shape[2] == 3
        assert 0 <= x and x + image.shape[1] <= width
        assert 0 <= y and y + image.shape[0] <= height
        assert image.min() >= 0.0 and image.max() <= 1.0


def test_keys_step_through_the_screens_and_their_settings(tmp_path, capsys):
    clut_file = tmp_path / "clut.csv"
    np.savetxt(clut_file, CLUT, delimiter=",", header="clut", comments="")

    shown = []
    textures = []

    def new_texture(image):
        texture = types.SimpleNamespace(draw=lambda position: None, deleted=False)
        texture.delete = lambda: setattr(texture, "deleted", True)
        textures.append(texture)
        return texture

    keys = iter(["Right", "Left", "Escape"])
    graphics = types.SimpleNamespace(
        width=1024,
        height=768,
        newTexture=new_texture,
        flip=lambda: shown.append(None),
        changeBackground=lambda background: None,
    )
    ihrl = types.SimpleNamespace(
        graphics=graphics,
        inputs=types.SimpleNamespace(readButton=lambda btns: (next(keys), 0.0)),
        close=lambda: None,
    )

    args = show.parser.parse_args(["--lut", str(clut_file)])
    with patch("hrl.util.clut.show.HRL", return_value=ihrl):
        show.command(args)

    output = capsys.readouterr().out
    screens = [
        line.split("] ")[1].split(" --")[0] for line in output.splitlines() if line.startswith("[")
    ]
    assert screens == [
        "gamut",
        "gamut",
        "gamut",
    ]
    assert all(texture.deleted for texture in textures), "every texture was freed"
