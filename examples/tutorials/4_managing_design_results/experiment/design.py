"""This module defines the actual experimental design of [this] experiment.

It needs to _at least_ define these functions, which are called by `run_experiment.py`
- run_trial: how to run a single trial of this experiment
- generate_session: how to generate a new session's worth of design (files)

It can define additional functions to help manage the control flow.

"""

import data_management
import numpy as np
import pandas as pd
import stimuli

LUMINANCES = [0, 0.25, 0.75, 1]

STIM_NAMES = stimuli.__all__


def generate_session(Nrepeats=2):
    for i in range(Nrepeats):
        for stim_name in STIM_NAMES:
            block = generate_block(stim_name)
            block_id = f"{stim_name}-{i}"

            # Save to file
            filepath = data_management.design_filepath(block_id)
            block.to_csv(filepath)


def generate_block(stim_name):
    # Combine all variables into full design
    trials = [
        (stim_name, int_target, int_left, int_right)
        for int_target in LUMINANCES
        for int_left in LUMINANCES
        for int_right in LUMINANCES
    ]

    # Convert to dataframe
    block = pd.DataFrame(
        trials,
        columns=["stim", "intensity_target", "intensity_left", "intensity_right"],
    )

    # Shuffle trial order
    block = block.reindex(np.random.permutation(block.index))
    block.reset_index(drop=True, inplace=True)
    block.index.name = "trial"

    return block
