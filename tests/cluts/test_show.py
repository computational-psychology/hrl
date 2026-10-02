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


def test_isoluminant_plane_is_at_one_luminance_around_the_grey():
    image, reachable, half_width = show.isoluminant_plane_image(CLUT, LUMINANCE, GREY, size=41)

    Y = RGB_to_XYZ(image[reachable], CLUT, per_level=True)[:, 1]
    np.testing.assert_allclose(Y, LUMINANCE, rtol=1e-6)
    np.testing.assert_allclose(image[20, 20], GREY, atol=1e-9)
    assert np.all(image[~reachable] == GREY)
    assert 0.1 < reachable.mean() < 0.9, "the plane extends past what the display can show"
    assert half_width > 0


def test_plane_has_axes_through_the_grey_with_round_ticks():
    width, height = 1024, 768
    items, _, text = show.plane_screen(CLUT, {"luminance": LUMINANCE}, GREY, width, height)

    image = items[0][0]
    centre = image.shape[0] // 2
    assert np.all(image[centre, :] == 0.0) and np.all(image[:, centre] == 0.0)

    step = float(
        next(line for line in text if "ticks are every" in line).split("every ")[1].split()[0]
    )
    mantissa = step / 10 ** np.floor(np.log10(step))
    assert np.isclose(mantissa, [1, 2, 5, 10]).any(), "a round step"


def test_ramps_change_only_luminance_or_only_chromaticity():
    ramps = show.direction_ramps(CLUT, LUMINANCE, steps=32)

    name, luminance_ramp = ramps[0]
    xyz = RGB_to_XYZ(luminance_ramp, CLUT, per_level=True)
    np.testing.assert_allclose(_xy(xyz), _xy(xyz[:1]).repeat(len(xyz), axis=0), atol=1e-6)
    assert np.ptp(xyz[:, 1]) > 0.5 * WHITE_Y

    for name, ramp in ramps[1:]:
        np.testing.assert_allclose(
            RGB_to_XYZ(ramp, CLUT, per_level=True)[:, 1], LUMINANCE, rtol=1e-6
        )


def test_each_solid_patch_is_the_average_of_its_stripes():
    checks = show.stripe_pairs(CLUT, LUMINANCE)

    assert len(checks) == 8
    for name, a, b, solid, error in checks:
        average = RGB_to_XYZ(np.stack([a, b]), CLUT, per_level=True).mean(axis=0)
        assert error <= 1e-6, f"{name}: a display with fixed primaries can match every pair"
        np.testing.assert_allclose(RGB_to_XYZ(solid, CLUT, per_level=True), average, atol=1e-6)


def test_stripes_alternate_at_the_requested_width():
    a, b = np.zeros(3), np.ones(3)

    patch = show.stripe_patch(a, b, size=12, width=3)

    assert patch.shape == (12, 12, 3)
    np.testing.assert_array_equal(patch[0, :, 0], [0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1])
    assert np.all(patch == patch[:1])


def test_each_stripes_bar_runs_coarse_to_fine_into_its_solid_patch():
    items, _, _ = show.stripes_screen(CLUT, {"luminance": LUMINANCE}, GREY, 1920, 1080)

    sections = len(show.STRIPE_WIDTHS) + 1
    assert len(items) == sections * 8, "every pair of a display with fixed primaries is shown"
    for bar in range(8):
        images, positions = zip(*items[bar * sections : (bar + 1) * sections])
        size = images[0].shape[0]
        assert all(
            x == positions[0][0] + i * size for i, (x, _) in enumerate(positions)
        ), "touching"
        assert len({y for _, y in positions}) == 1, "in one row"
        assert size % (2 * max(show.STRIPE_WIDTHS)) == 0, "whole periods of the widest stripes"
        assert np.all(images[-1] == images[-1][0, 0]), "ends in a solid patch"


@pytest.mark.parametrize("name,screen", show.SCREENS)
def test_every_screen_fits_on_the_screen(name, screen):
    width, height = 1024, 768
    state = {"luminance": LUMINANCE}

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

    keys = iter(["Right", "Up", "Right", "Right", "Up", "Left", "Left", "Left", "Escape"])
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
        "isoluminant plane",
        "isoluminant plane",
        "directions",
        "stripes",
        "stripes",
        "directions",
        "isoluminant plane",
        "gamut",
    ]
    assert f"Y = {LUMINANCE + 0.05 * WHITE_Y:.1f}" in output, "Up raised the luminance"
    assert all(texture.deleted for texture in textures), "every texture was freed"
