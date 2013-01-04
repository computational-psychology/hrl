def dpxFloatToChans(flt):
    """
    Takes a floating point number between 0 and 1 and returns a
    4-channel * 8-bit representation in the datapixx R-G concatenated
    format.
    """
    return dpxIntToChans(np.uint32(flt * (2**16 - 1)))

def dpxIntToChans(n):
    """
    Takes a 16-bit integer and returns a 4-channel * 8-bit
    representation in the datapixx R-G concatenated format.
    """
    return (n / (2**8),n % (2**8),0,2**8 - 1)


