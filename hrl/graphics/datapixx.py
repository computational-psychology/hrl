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

def initializeDPX():
    """
    InitializeDPX performs a few DataPixx operations in order to ready
    the presentation of images. It returns the datapixx object, which
    must be maintained in order to continue using DataPixx.
    """
    # Open datapixx.
    dpixx = dpx.open()

    # set videomode: Concatenate Red and Green into a 16 bit luminance
    # channel.
    dpixx.setVidMode(dpx.DPREG_VID_CTRL_MODE_M16)

    # Demonstrate successful initialization.
    dpixx.blink(dpx.BWHITE | dpx.BBLUE | dpx.BGREEN
                | dpx.BYELLOW | dpx.BRED)
    return dpixx


