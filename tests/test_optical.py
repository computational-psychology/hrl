import pytest

from hrl.photometer.optical import OptiCAL

pytestmark = [pytest.mark.photometer]


def test_initialization():
    OptiCAL(dev="/dev/ttyUSB0")


def test_read_luminance():
    OptiCAL(dev="/dev/ttyUSB0").readLuminance(n=5, slp=5)
