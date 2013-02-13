# Qualified Imports
import Image as im
import numpy as np
import datapixx as dpx


# Initializing Datapixx

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

# Bitmap Conversion

def fileToGreyArray(fl):
    """
    fileToGreyArray uses PIL to convert an image into a numpy array of floats between 0
    and 1. Note that we assume that the colour resolution is 3*8-bit.
    """
    pic = im.open(fl)
    div = 255.0
    pix = np.array(pic.getdata())
    pix = pix.reshape(pic.size[1], pic.size[0], pix.shape[1])
    return np.mean(pix[:,:,:3],2)/div
