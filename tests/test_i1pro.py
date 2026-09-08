import pygame
import pytest

import hrl.photometer

pytestmark = [pytest.mark.photometer]
pygame.init()


def test_initialization():
    from hrl.photometer.i1pro import i1Pro

    i1Pro(timeout=1)


def test_alias():
    hrl.photometer.new_photometer("i1pro", timeout=1)


def test_read_luminance():
    device = hrl.photometer.new_photometer("i1pro", timeout=1)

    lum = device.readLuminance(n=1, slp=5)
    assert isinstance(lum, float)


def test_read_tristimulus():
    device = hrl.photometer.new_photometer("i1pro", timeout=1)

    xyz = device.readTristimulus(n=1, slp=5)
    assert isinstance(xyz, tuple)
    assert len(xyz) == 3
