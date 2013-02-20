from graphics import Graphics
import numpy as np

## Class ##

class DATAPixx(Graphics):

    def greyToChannels(self,gry):
        """
        Converts a single normalized greyscale value (i.e. between 0 and 1)
        into a 4 colour channel representation specific to the particular graphics
        backend.
        """
        return dpxIntToChans(np.uint32(gry * (2**16 - 1)))

## Additional Functions ##

def dpxIntToChans(n):
    """
    Takes a 16-bit integer and returns a 4-channel * 8-bit
    representation in the datapixx R-G concatenated format.
    """
    return (n / (2**8),n % (2**8),0,2**8 - 1)


