import pytest

pytestmark = [pytest.mark.photometer]


def test_initialization(photometer_dev):
    from hrl.photometer.i1pro import i1Pro

    i1Pro()


def test_read_luminance(photometer_dev):
    from hrl.photometer.i1pro import i1Pro

    device = i1Pro()
    device.readLuminance(n=1, slp=5)
