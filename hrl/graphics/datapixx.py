import numpy as np

from .graphics import Graphics

## Class ##


class DATAPixx(Graphics):
    """
    A Graphics implementation for a DataPixx DAC.  The four channel
    representation has a 16 bit resolution in the  datapixx R-G concatenated
    format.
    """

    def greyToChannels(self, gry):
        return dpxIntToChans(np.uint32(gry * (2**16 - 1)))


## Additional Functions ##


def dpxIntToChans(n):
    """
    Takes a 16-bit integer and returns a 4-channel * 8-bit representation in the
    datapixx R-G concatenated format.
    """
    return (n // (2**8), n % (2**8), 0, 2**8 - 1)
