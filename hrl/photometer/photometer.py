"""
This is the HRL submodule for coordinating photometers. Photometers must
implement the Photometer abstract base class, which simply defines a common
function for reading luminance.
"""

from abc import ABC



### Classes ###


class Photometer(ABC):
    """
    The Photometer abstract base class. New photometers must instantiate
    this class. The only method is 'readLuminance', which returns a luminance
    reading from the device.
    """

    __metaclass__ = abc.ABCMeta

    # Abstract Methods #

    def readLuminance(self, n, slp):
        """
        Reads a value from the photometer, returning a real value in candela/m^2.

        (Some decisions need to be made about this interface still wrt arguments.)
        """
        return
