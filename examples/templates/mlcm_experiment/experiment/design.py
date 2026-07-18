import itertools
import random

import data_management
import numpy as np
import pandas as pd

DEBUG = False

n_luminances = 8
luminances = np.linspace(0.1, 0.9, n_luminances).round(3)
surrounds = (0.0, 1.0)


def generate_session(Nrepeats=5):
    """Generates design files for one session

    We think of one session corresponding to several blocks of trials.
    You set up how many repeats you do per session with the argument
    Nrepeats
    """

    for i in range(Nrepeats):
        block = generate_block()
        block_id = f"mlcm-{i}"

        # Save to file
        filepath = data_management.design_filepath(block_id)
        block.to_csv(filepath)


def generate_block():
    """Experimental design for one block of trials

    Here you define how many trials one block will contain, which
    will depend on the number of conditions you have.
    """

    targets = [(lum, surr) for surr in surrounds for lum in luminances]
    stimuli_design = list(itertools.combinations(targets, 2))

    trials = []
    for trial in stimuli_design:
        trial = list(trial)
        # Randomly shuffle order L-R-Down
        random.shuffle(trial)

        # Flatten
        target_left, target_right = trial
        line = [target_left[0], target_left[1], target_right[0], target_right[1]]
        trials.append(line)

    # creates dataframe with all trials
    block = pd.DataFrame(
        trials,
        columns=[
            "target_intensity_left",
            "surround_intensity_left",
            "target_intensity_right",
            "surround_intensity_right",
        ],
    )

    # Shuffle trial order
    block = block.reindex(np.random.permutation(block.index))
    block.reset_index(drop=True, inplace=True)
    block.index.name = "trial"

    return block


if __name__ == "__main__":
    generate_session()
