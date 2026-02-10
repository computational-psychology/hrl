import pytest

from hrl.photometer.minolta import Minolta

pytestmark = [pytest.mark.photometer]


def test_initialization():
    Minolta(dev="/dev/ttyUSB0")


def test_read_luminance():
    Minolta(dev="/dev/ttyUSB0").readLuminance(n=5, slp=5)
