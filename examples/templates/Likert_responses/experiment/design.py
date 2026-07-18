import numpy as np
import pandas as pd

import data_management
import stimuli

stim_names = stimuli.stims.keys()


def generate_session(Nrepeats=2):
    for i in range(Nrepeats):
        block = generate_block()
        block_id = f"direction-{i}"

        # Save to file
        filepath = data_management.design_filepath(block_id)
        block.to_csv(filepath)


def generate_block():
    # Combine all variables into full design
    trials = [(name) for name in stim_names]

    # Convert to dataframe
    block = pd.DataFrame(
        trials,
        columns=["stim"],
    )

    # Shuffle trial order
    block = block.reindex(np.random.permutation(block.index))
    block.reset_index(drop=True, inplace=True)
    block.index.name = "trial"

    return block
