import os
import pytest


pytestmark = [pytest.mark.graphics]


SETUP = {
    "graphics": "datapixx",
    "wdth": 1920,
    "hght": 1080,
    "scrn": 1,
    # "lut": Path(__file__).parent / "lut_datapixx.csv",
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
    import pypixxlib.datapixx
    from hrl.graphics.datapixx import DATAPixx


def test_connect():
    import pypixxlib.datapixx

    device = pypixxlib.datapixx.DATAPixx()
    try:
        device.getInfo()
    finally:
        device.close()


def test_modes():
    import pypixxlib.datapixx

    device = pypixxlib.datapixx.DATAPixx()
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
    import pypixxlib.datapixx
    from hrl.graphics.datapixx import DATAPixx
    import hrl.hrl

    device = pypixxlib.datapixx.DATAPixx()
    try:
        device.setVideoMode('M16')
        device.updateRegisterCache()

        igraphics = DATAPixx(
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
    import pypixxlib.datapixx
    from hrl.graphics.datapixx import DATAPixx
    from hrl.inputs.keyboard import Keyboard

    device = pypixxlib.datapixx.DATAPixx()
    try:
        device.setVideoMode('M16')
        device.updateRegisterCache()

        igraphics = DATAPixx(
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
    import pypixxlib.datapixx
    from hrl.graphics.datapixx import DATAPixx
    from hrl.inputs.responsepixx import RESPONSEPixx

    device = pypixxlib.datapixx.DATAPixx()
    try:
        device.setVideoMode('M16')
        device.updateRegisterCache()

        igraphics = DATAPixx(
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
