#!/usr/bin/env python
"""
Example experiment with HRL.

This is the main file that needs to be called from the command line.
It imports other modules and during the entry point (in function 
experiment_main()

@authors: Guillermo Aguilar, Joris Vincent
"""

from socket import gethostname

import pandas as pd
from hrl import HRL

import data_management
import design
import experiment_logic
import text_displays

SETUP = {
    "graphics": "gpu",
    "inputs": "keyboard",
    "scrn": 1,
    "lut": None,
    "fs": False,
    "wdth": 800,
    "hght": 600,
    "bg": 0.5
    }



def run_block(ihrl, block, block_id):
    """Routine that runs a block of trials. 
    It iterates thorough the list of trials in this block,
    and calls run_trial() for each of them.
    """
    
    print(f"Running block {block_id}")
    # Get start, end trial
    start_trial = block["trial"].iloc[0]
    end_trial = block["trial"].iloc[-1] + 1

    # loop over trials in block
    for idx, trial in block.iterrows():
        trial_id = trial["trial"]
        print(f"TRIAL {trial_id}")

        # show a break screen automatically after so many trials
        if (end_trial - trial_id) % (end_trial // 2) == 0 and (trial_id - start_trial) > 1:
            text_displays.block_break(ihrl, trial_id, (start_trial + (end_trial - start_trial)))

        # current trial design variables (convert from pandas row to dict)
        trial = trial.to_dict()

        # run trial
        t1 = pd.Timestamp.now().strftime("%Y%m%d:%H%M%S.%f")
        trial_results = experiment_logic.run_trial(ihrl, **trial)
        trial.update(trial_results)
        t2 = pd.Timestamp.now().strftime("%Y%m%d:%H%M%S.%f")

        # Record timing
        trial["start_time"] = t1
        trial["stop_time"] = t2

        # Save trial
        data_management.save_trial(trial, block_id)

    print(f"Block {block_id} all trials completed.")
    return block


def experiment_main(ihrl):
    """Main experimental function, entry point."""
    
    # Get all blocks for this session
    incomplete_blocks = data_management.get_incomplete_blocks()
    if len(incomplete_blocks) == 0:
        # No existing blocks for this session. Generate using the design.py
        design.generate_session()
        incomplete_blocks = data_management.get_incomplete_blocks()
        
    print(f"{len(incomplete_blocks)} incomplete blocks")


    # Run the experiment
    try:
        # Iterate over all blocks that need to be presented
        for block_num, (block_id, block) in enumerate(incomplete_blocks.items()):
            # Run block
            print(f"Running session block {block_num+1}: {block_id}")
            block = run_block(ihrl, block=block, block_id=block_id)

            if block_num + 1 < len(incomplete_blocks):
                text_displays.block_end(ihrl, block_num + 1, len(incomplete_blocks))
    
    except SystemExit as e:
        # Cleanup
        print("Exiting...")
        ihrl.close()
        raise e

    # Close session
    ihrl.close()
    print("Session complete")


if __name__ == "__main__":
    # Create HRL interface object with parameters that depend on the setup
    ihrl = HRL(
        **SETUP,
        photometer=None,
        db=True,
    )

    experiment_main(ihrl)

    ihrl.close()
