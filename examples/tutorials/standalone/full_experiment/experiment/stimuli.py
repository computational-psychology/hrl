"""This module defines the stimuli to be used in this experiment """

import numpy as np

# constants
TARGET_SIZE = (25, 25) # size of middle target, in pixels
SIZE = (200, 200)   # size of one half of SBC, in pixels


def sbc(intensity_left, 
	    intensity_right, 
	    intensity_bg_left, 
	    intensity_bg_right):
    """ A basic simultaneous brightness contrast (SBC)
    Two-sided SBC with variable background and target intensities

    Parameters
    ----------
    intensity_target_left : float
        intensity value for the left target
    intensity_target_right : float
        intensity value for the right target
    intensity_bg_left : float
        intensity value for the left context
    intensity_bg_right : float
        intensity value for the right context
        
    Returns
    -------
    numpy array:
       stimulus
    """
        
    # set up backgrounds
    leftside = np.ones(SIZE)*intensity_bg_left
    rightside = np.ones(SIZE)*intensity_bg_right
    
    # set-up targets
    leftside[int(SIZE[0]/2 - TARGET_SIZE[0]):int(SIZE[0]/2 + TARGET_SIZE[0]), 
             int(SIZE[1]/2 - TARGET_SIZE[1]):int(SIZE[1]/2 + TARGET_SIZE[1])] = intensity_left
    
    rightside[int(SIZE[0]/2 - TARGET_SIZE[0]):int(SIZE[0]/2 + TARGET_SIZE[0]), 
             int(SIZE[1]/2 - TARGET_SIZE[1]):int(SIZE[1]/2 + TARGET_SIZE[1])] = intensity_right

    # concatenate them horizontally and return
    return np.hstack((leftside, rightside))
    


if __name__ == "__main__":
    # This part only gets executed when this file is called from the
    # command line. We used it for testing
    
    import matplotlib.pyplot as plt
    
    plt.imshow(sbc(0.5, 0.5, 0.0, 1.0), cmap='gray')
    plt.show()
    
    plt.imshow(sbc(0.5, 0.5, 1.0, 0.0), cmap='gray')
    plt.show()

    plt.imshow(sbc(0.75, 0.25, 1.0, 0.0), cmap='gray')
    plt.show()


