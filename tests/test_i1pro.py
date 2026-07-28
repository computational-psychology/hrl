import pygame
import pytest
from hrl.photometer.i1pro import i1Pro

pytestmark = [pytest.mark.photometer]
pygame.init()


def test_initialization():
    i1Pro(timeout=1)


def test_read_luminance():
    device = i1Pro(timeout=1)
    device.readLuminance(n=1, slp=5)
