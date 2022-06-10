# Qualified Imports
import Image as im
import numpy as np

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
