#!/usr/bin/env python
"""
MLCM experiment on simultaneous brightness contrast,
with disk-and-annulus stimuli

Uses HRL on python 3

@authors: G. Aguilar, July 2023.
"""

from socket import gethostname

import data_management
import design
import experiment_logic
import pandas as pd
import text_displays
from hrl import HRL

if "vlab" in gethostname():
    SETUP = {
        "graphics": "datapixx",
        "inputs": "responsepixx",
        "scrn": 1,
        "lut": "lut.csv",
        "fs": True,
        "wdth": 1024,
        "hght": 768,
        "bg": 0.1,  # corresponding to 50 cd/m2 approx
    }
elif "viewpixx" in gethostname():
    SETUP = {
        "graphics": "viewpixx",
        "inputs": "responsepixx",
        "scrn": 1,
        "lut": "lut_viewpixx.csv",
        "fs": True,
        "wdth": 1920,
        "hght": 1080,
        "bg": 0.27,  # corresponding to 50 cd/m2 approx
    }
else:
    SETUP = {
        "graphics": "gpu",
        "inputs": "keyboard",
        "scrn": 1,
        "lut": None,
        "fs": False,
        "wdth": 1920,
        "hght": 1080,
        "bg": 0.3,
    }


def run_block(ihrl, block, block_id):
    print(f"Running block {block_id}")
    # Get start, end trial
    start_trial = block["trial"].iloc[0]
    end_trial = block["trial"].iloc[-1] + 1

    # loop over trials in block
    for idx, trial in block.iterrows():
        trial_id = int(trial["trial"])
        print(f"TRIAL {trial_id}")

        # show a break screen automatically after so many trials
        if (end_trial - trial_id) % (end_trial // 2) == 0 and (trial_id - start_trial) > 1:
            text_displays.block_break(
                ihrl,
                trial_id,
                (start_trial + (end_trial - start_trial)),
                intensity_background=SETUP["bg"],
            )

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
    # Get all blocks for this session
    incomplete_blocks = data_management.get_incomplete_blocks(block_signifier="mlcm")
    if len(incomplete_blocks) == 0:
        # No existing blocks for this session. Generate.
        design.generate_session()
        incomplete_blocks = data_management.get_incomplete_blocks(block_signifier="mlcm")
    print(f"{len(incomplete_blocks)} incomplete blocks")

    # Run
    try:
        # Display instructions and wait to start
        experiment_logic.display_instructions(ihrl)
        btn, _ = ihrl.inputs.readButton(btns=["Space", "Escape"])
        if btn == "Escape":
            sys.exit("Participant terminated experiment.")

        # Iterate over all blocks that need to be presented
        for block_num, (block_id, block) in enumerate(incomplete_blocks.items()):
            # Run block
            print(f"Running session block {block_num+1}: {block_id}")
            block = run_block(ihrl, block=block, block_id=block_id)

            if block_num + 1 < len(incomplete_blocks):
                text_displays.block_end(
                    ihrl,
                    block_num + 1,
                    len(incomplete_blocks),
                    intensity_background=SETUP["bg"],
                )
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
