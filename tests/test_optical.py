import pytest

pytestmark = [pytest.mark.photometer]


def test_initialization():
    from hrl.photometer.optical import OptiCAL

    OptiCAL(dev="/dev/ttyUSB0")


def test_read_luminance():
    from hrl.photometer.optical import OptiCAL

    OptiCAL(dev="/dev/ttyUSB0").readLuminance(n=5, slp=5)
