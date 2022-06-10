from .graphics import Graphics
import numpy as np

## Class ##

class GPU(Graphics):
    """
    A Graphics implementation for standard GPUs. The 32 bit channel
    representation is simply an 8-bit integer n equal across the red, green, and
    blue channels, with the alpha channel set to the max int.
    """
    def greyToChannels(self,gry):
        return nodpxIntToChans(np.uint32(gry * (2**8 - 1)))

## Additional Functions ##

def nodpxIntToChans(n):
    """
    Takes an 8-bit integer and returns the 4-channel representation for a normal monitor
    (i.e. R=G=B=x)
    """
    return (n,n,n,2**8 - 1)

