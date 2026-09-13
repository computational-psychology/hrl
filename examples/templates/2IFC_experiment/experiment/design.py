import itertools
import random

import data_management
import numpy as np
import pandas as pd

DEBUG = True

# EXPERIMENTAL DESIGN

spatial_frequencies = [0.5, 2, 8]
contrast_values = np.logspace(-0.5, -1, 2) # from 0.001 to 0.01, logspaced
print(contrast_values)

# In this design we do not care about orientation and phase of the Gabor,
# but we randomly pick one orientation and phase for each trial from 
# the following possible values 
orientations = [0, 30, 60, 90, 120, 150]  # 6 possible orientations
phases = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]  # 12 possible phase shifts

Nrepeats = 5  # n repeats per contrast level
FEEDBACK = 0 # 1: with or 0: without feedback

## 
SIGNIFIER = "2IFC"

def generate_session():
    """Generates design files for one session

    We think of one session corresponding to several blocks of trials.
    Here we follow a blocked design. That means that in one block 
    only one spatial frequency and one contrast increment will be tested.
    So in one block we have just n repeats of the same values, just
    randomly assigned to left/right or 1st/2nd interval.
    
    Different contrast values and spatial frequencies are tested
    on different blocks.
        
    """
    i=0 # counter
    for sf in spatial_frequencies:
        for c in contrast_values:
            block = generate_block(sf, c, pedestal=0, Nrepeats=Nrepeats)
            block_id = f"{SIGNIFIER}-{i}"

            # Save to file
            filepath = data_management.design_filepath(block_id)
            block.to_csv(filepath)
            if DEBUG:
                print(block)

            i+=1


def generate_block(sf, delta, pedestal=0, Nrepeats=10):
    """Experimental design for one block of trials.
    
    In this case all trials are the same, just repeated Nrepeats
    and randomly swapped 1st or 2nd interval.
    """

    trials = []
    for i in range(Nrepeats):
        # Randomly choose if 1st or 2nd interval has contrast increment
        if random.randint(0, 1)==0:
            first = pedestal
            second = pedestal + delta
            correct = 2
        else:
            first = pedestal + delta
            second = pedestal
            correct = 1

        ori = random.choice(orientations)
        phase = random.choice(phases)
        # Flatten
        line = [sf, ori, phase, pedestal, delta, first, second, correct, FEEDBACK]
        trials.append(line)

    # creates dataframe with all trials
    block = pd.DataFrame(
        trials,
        columns=[
            "sf",
            "orientation",
            "phase",
            "pedestal",
            "delta",
            "contrast_interval1",
            "contrast_interval2",
            "correct",
            "feedback"
        ],
    )
    
    # Shuffle trial order
    block = block.reindex(np.random.permutation(block.index))
    block.reset_index(drop=True, inplace=True)
    block.index.name = "trial"

    return block


if __name__ == "__main__":
    generate_session()
