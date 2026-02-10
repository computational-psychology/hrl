import pytest

pytestmark = [pytest.mark.photometer]


def test_initialization():
    from hrl.photometer.minolta import Minolta

    Minolta(dev="/dev/ttyUSB0")


def test_read_luminance():
    from hrl.photometer.minolta import Minolta

    Minolta(dev="/dev/ttyUSB0").readLuminance(n=5, slp=5)
