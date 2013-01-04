# Differences between GPU and Datapixx: Channel representation, initialization
# (datapixx must be initialized as well)

def nodpxFloatToChans(flt):
    """
    Takes a floating point number and returns a 4 channel representation
    in a normal, 8 bit, greyscale format.
    """
    return nodpxIntToChans(np.uint32(flt * (2**8 - 1)))

def nodpxIntToChans(n):
    """
    Takes an 8-bit integer and returns the 4-channel representation for a normal monitor
    (i.e. R=G=B=x)
    """
    return (n,n,n,2**8 - 1)

