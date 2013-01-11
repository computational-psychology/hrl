from graphics import Graphics
import numpy as np

## Class ##

class GPU(Graphics):

    def greyToChannels(self,gry):
        """
        Converts a single normalized greyscale value (i.e. between 0 and 1)
        into a 4 colour channel representation specific to the particular graphics
        backend.
        """
        return nodpxIntToChans(np.uint32(gry * (2**8 - 1)))

## Additional Functions ##

def nodpxIntToChans(n):
    """
    Takes an 8-bit integer and returns the 4-channel representation for a normal monitor
    (i.e. R=G=B=x)
    """
    return (n,n,n,2**8 - 1)

