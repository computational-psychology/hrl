"""This module defines the actual experimental design of this experiment.

It needs to _at least_ define a function called generate_session().
This function generates the CSV files for one sitting --a session-- of
our experiment. As usually a session consist of more than one block,
we also define a function generate_block(), and repeatedly call it
as needed.

It can define additional functions to help manage the control flow.

"""

import numpy as np
import pandas as pd
import stimuli

# constants
LUMINANCES = [0.1, 0.25, 0.5, 0.75, 0.9]
NREPEATS = 3
LUM_BG_WHITE = 1.0
LUM_BG_BLACK = 0.0


def generate_session():
    """ Generates the design files for a session 
    
    We think of a session as a sitting in the lab, usually in just one day.
    This function will call generate_block() for each block we want in one
    session 
    """
    import data_management
    
    for i in range(NREPEATS):
        block = generate_block()
        block_id = f"sbc-{i}"

        # Save to file
        filepath = data_management.design_filepath(block_id)
        block.to_csv(filepath)


def generate_block():
    """ Generates one block of trials 
    
    Here is where you decide your design file, 
    i.e. how your experimental design translates into
    the variables for the stimuli you are going to present
    """
    
    # In this case, we are going to do a design to measure the 
    # point of subjective equality.
    # We will have two fixed backgrounds (black and white)
    # in one side we will have a target, which is fixed to 0.5
    # on the other we have a probe, with 5 different possible intensities.
    # We present the probe in black and the target in white, AND vice-versa
    # and we repeat this for left and right positions
    
    # probe on black, on the left
    trials1 = [("left", "on-black", t, 0.5, LUM_BG_BLACK, LUM_BG_WHITE) for t in LUMINANCES]
    
    # probe on white, on the right
    trials2 = [("right", "on-white", 0.5, t, LUM_BG_BLACK, LUM_BG_WHITE) for t in LUMINANCES]

    # probe on black, on the right
    trials3 = [("right", "on-black", 0.5, t, LUM_BG_WHITE, LUM_BG_BLACK) for t in LUMINANCES]
    
    # probe on white, on the left
    trials4 = [("left", "on-white", t, 0.5, LUM_BG_WHITE, LUM_BG_BLACK) for t in LUMINANCES]
    
    trials = trials1 + trials2 + trials3 + trials4

    # Convert to dataframe
    block = pd.DataFrame(
        trials,
        columns=["probe-position", "probe-context", "intensity_target_left", "intensity_target_right", 
                 "intensity_bg_left", "intensity_bg_right"],
    )

    # Shuffle trial order
    block = block.reindex(np.random.permutation(block.index))
    block.reset_index(drop=True, inplace=True)
    block.index.name = "trial"

    return block



if __name__ == "__main__":
    # This part only gets executed when this file is called from the
    # command line. We used it for testing and sanity checking that 
    # our function works as expected
    
    b = generate_block()
    print(b.sort_values(by=['probe-position', "probe-context", 'intensity_target_left', 'intensity_target_right']))
    print(len(b))


