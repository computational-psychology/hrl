import pytest

pytestmark = [pytest.mark.photometer]


def test_initialization(photometer_dev):
    from hrl.photometer.minolta import Minolta

    Minolta(dev=photometer_dev)


def test_read_luminance(photometer_dev):
    from hrl.photometer.minolta import Minolta

    Minolta(dev=photometer_dev).readLuminance(n=5, slp=5)
