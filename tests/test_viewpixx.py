import os
import pytest


pytestmark = [pytest.mark.graphics]


SETUP = {
    "graphics": "viewpixx",
    "wdth": 1920,
    "hght": 1080,
    "scrn": 1,
    # "lut": Path(__file__).parent / "lut_viewpixx.csv",
    "fs": False,
    "db": True,
}

scrn = 1
# In older systems or systems with separate Xscreens, the naming is still :0.0 or :0.1.
# For systems with only one screen, it is :1.
if (os.environ["DISPLAY"] == ":0"): 
    os.environ["DISPLAY"] = f":0.{int(scrn):d}"
else:
    os.environ["DISPLAY"] = f":{int(scrn):d}"


def test_imports():
    import pygame
    from pypixxlib.viewpixx import VIEWPixx3D
    from hrl.graphics.datapixx import DATAPixx


def test_connect():
    from pypixxlib.viewpixx import VIEWPixx3D

    device = VIEWPixx3D()
    try:
        device.getInfo()
    finally:
        device.close()


def test_modes():
    from pypixxlib.viewpixx import VIEWPixx3D

    device = VIEWPixx3D()
    try:
        original_mode = device.getVideoMode()
        if original_mode == 'C24':
            device.setVideoMode('M16')
            assert device.getVideoMode() == 'M16'
        else:
            device.setVideoMode('C24')
            assert device.getVideoMode() == 'C24'
    finally:
        device.close()


def test_graphics_init():
    from pypixxlib.viewpixx import VIEWPixx3D
    from hrl.graphics.datapixx import DATAPixx as VIEWPixx
    import hrl.hrl

    device = VIEWPixx3D()
    try:
        device.setVideoMode('M16')
        device.updateRegisterCache()

        igraphics = VIEWPixx(
            width=SETUP["wdth"],
            height=SETUP["hght"],
            fullscreen=SETUP["fs"],
            double_buffer=SETUP["db"],
            background=1.0,
            mouse=False,
            lut=None,
        )
        igraphics.flip()
        hrl.hrl.pygame.time.wait(250)
    finally:
        device.close()


@pytest.mark.inputs
def test_keyboard():
    from pypixxlib.viewpixx import VIEWPixx3D
    from hrl.graphics.datapixx import DATAPixx as VIEWPixx
    from hrl.inputs.keyboard import Keyboard

    device = VIEWPixx3D()
    try:
        device.setVideoMode('M16')
        device.updateRegisterCache()

        igraphics = VIEWPixx(
            width=SETUP["wdth"],
            height=SETUP["hght"],
            fullscreen=SETUP["fs"],
            double_buffer=SETUP["db"],
            background=1.0,
            mouse=False,
            lut=None,
        )
        igraphics.flip()
        inputs = Keyboard()
        inputs.readButton(to=.5)
    finally:
        device.close()


@pytest.mark.inputs
def test_responsepixx():
    from pypixxlib.viewpixx import VIEWPixx3D
    from hrl.graphics.datapixx import DATAPixx as VIEWPixx
    from hrl.inputs.responsepixx import RESPONSEPixx

    device = VIEWPixx3D()
    try:
        device.setVideoMode('M16')
        device.updateRegisterCache()

        igraphics = VIEWPixx(
            width=SETUP["wdth"],
            height=SETUP["hght"],
            fullscreen=SETUP["fs"],
            double_buffer=SETUP["db"],
            background=1.0,
            mouse=False,
            lut=None,
        )
        igraphics.flip()
        inputs = RESPONSEPixx(device)
        inputs.readButton(to=.5)
    finally:
        device.close()


@pytest.mark.inputs
def test_hrl():
    from hrl import HRL

    ihrl = HRL(
        **SETUP,
        inputs="responsepixx",
        bg= 1.0,  # corresponding to 50 cd/m2 approx
    )

    ihrl.inputs.readButton(to=.5)
    ihrl.close()
