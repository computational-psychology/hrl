import data_management
import numpy as np
import pandas as pd
import stimuli

LUMINANCES = (0.25, 0.5, 0.75)
SIDES = ("Left", "Right")
STIM_NAMES = stimuli.__all__


def generate_session(Nrepeats=2):
    for i in range(Nrepeats):
        for stim_name in STIM_NAMES:
            block = generate_block(stim_name)
            block_id = f"matching-{stim_name}-{i}"

            # Save to file
            filepath = data_management.design_filepath(block_id)
            block.to_csv(filepath)


def generate_block(stim_name):
    # Combine all variables into full design
    trials = [(stim_name, int_target, side) for int_target in LUMINANCES for side in SIDES]

    # Convert to dataframe
    block = pd.DataFrame(
        trials,
        columns=["stim", "intensity_target", "target_side"],
    )

    # Shuffle trial order
    block = block.reindex(np.random.permutation(block.index))
    block.reset_index(drop=True, inplace=True)
    block.index.name = "trial"

    return block
