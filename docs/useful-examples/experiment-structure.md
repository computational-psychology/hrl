# Structure of an experiment

The previous examples each fit in one script. A real experiment does not: it has a
design to generate, results to save, trials to run and a session to sequence.
Putting all of that in one file makes it hard to change one part without breaking
another.

This page shows how the complete experiment from [managing data](managing-data)
is split into modules, and how those modules call each other. Every
[experiment template](../templates/templates-intro) in the next section uses the
same split, so this is the structure to understand before reading those.

The full example is at
[`examples/tutorials/standalone/full_experiment/`](https://github.com/computational-psychology/hrl/tree/master/examples/tutorials/standalone/full_experiment).


## Overview

```{mermaid}
graph LR;
    setup --> incomplete_blocks
    incomplete_blocks -->|none found| generate_session --> incomplete_blocks
    incomplete_blocks --> run_block
    run_block --> run_trial --> define --> display --> capture --> run_trial
    run_trial --> save_trial --> run_block
    run_block --> exit

    subgraph run_experiment.py
        setup
        run_block
        exit[cleanup & exit]
    end

    subgraph data_management.py
        incomplete_blocks[get_incomplete_blocks]
        save_trial
    end

    subgraph design.py
        generate_session
    end

    subgraph experiment_logic.py
        run_trial
    end

    subgraph stimuli.py
        define[sbc]
    end

    subgraph HRL
        display
        capture[capture participant response]
    end
```

Read it from the left. `run_experiment.py` starts by asking `data_management.py`
for the blocks still to be run, and only generates a session with `design.py`
when there are none. Each block is a loop over trials; each trial is run by
`experiment_logic.py`, which draws the stimulus from `stimuli.py` with `HRL` and
captures the response; each finished trial is saved before the next begins.


## The six modules

| Module | Responsibility |
| ------ | -------------- |
| `run_experiment.py` | Entry point. Chooses the hardware setup, sequences blocks, runs the trial loop, saves each trial. |
| `design.py` | What the experiment tests. Defines the variables and combines them into blocks of trials. |
| `experiment_logic.py` | What happens in one trial. Displays, waits for a response, returns the result. |
| `data_management.py` | Where things go. Participant, session, filepaths, saving, and finding incomplete trials. |
| `stimuli.py` | Generates or loads the stimulus images. |
| `text_displays.py` | Instructions, break screens and other text. |

The split follows the reasons you would have to change the code. A new
experiment means a new `design.py`, `experiment_logic.py` and `stimuli.py`;
`data_management.py` and most of `run_experiment.py` usually stay as they are.


## Running the example

```
cd examples/tutorials/standalone/full_experiment/experiment
python run_experiment.py
```

It must be run from inside `experiment/`, because `data_management.py` places the
`data/` directory next to that folder, at `full_experiment/data/`. The first
thing it does is ask for the participant initials; press Enter to accept the
default, `DEMO`.


## Choosing the setup

The top of `run_experiment.py` collects everything that differs between your
laptop and the lab into one dictionary, and a single flag picks which:

```{code-block} python
inlab = False

if inlab:
    SETUP = {
        "graphics": "viewpixx",   # 'datapixx' for using the old DataPixx 1 device
        "inputs": "responsepixx",
        "scrn": 1,
        "lut": "lut_viewpixx.csv", # 'lut_jvc.csv' for the JVC monitor
        "fs": True,
        "wdth": 1920,
        "hght": 1080,
        "bg": 0.27,
    }
else:
    SETUP = {
        "graphics": "gpu",
        "inputs": "keyboard",
        "scrn": 0,
        "lut": None,
        "fs": False,
        "wdth": 1920,
        "hght": 1080,
        "bg": 0.3,
    }
```

and the bottom of the file passes that dictionary to `HRL`:

```{code-block} python
if __name__ == "__main__":
    # Create HRL interface object with parameters that depend on the setup
    ihrl = HRL(
        **SETUP,
        photometer=None,
        db=True,
    )

    experiment_main(ihrl)

    ihrl.close()
```

Set `inlab = True` on the lab machine. The rest of the experiment never mentions
hardware. See [deploying your code in the lab](../getting-started/deploying-in-lab)
for what each parameter does.

The example ships two calibration files, `lut_viewpixx.csv` for the ViewPixx
setup and `lut_jvc.csv` for a JVC monitor. They show the format; they are not a
calibration of your display. Replace them with a current measurement from the
machine you run on, as described in
[gamma correction](../calibration/gamma-correction-linearization).

The [experiment templates](../templates/templates-intro) do the same thing, but
choose the dictionary from the machine's hostname instead of a flag, so that one
file runs unchanged on both machines.


## The entry point

`experiment_main` asks for the incomplete blocks, generates a session if there
are none, and runs the blocks one by one:

```{code-block} python
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
```

Note that the first thing the experiment does is look for existing design files,
not generate new ones. Generation only happens when nothing is found. This is
what makes resuming the default behavior rather than an option.

Any `SystemExit` raised during a block, which is how the participant or
experimenter quits, is caught here so that `HRL` is closed before the program
ends. Every trial completed up to that point has already been saved.


## Running a block

`run_block` is the trial loop. Each row of the block dataframe is converted to a
dictionary, handed to `run_trial` as keyword arguments, updated with whatever
that returns, stamped with start and stop times, and saved:

```{code-block} python
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
```

`trial.update(trial_results)` merges the results into the same dictionary that
held the design. One dictionary goes to `save_trial`, and one row is written
containing both design and result. That is what lets
[managing data](managing-data) find the incomplete trials by comparing design
files against results files: the design columns are present in both.

`run_block` also shows a break screen halfway through a block, using
`text_displays.block_break`.


## Running a trial

`run_trial` lives in `experiment_logic.py` and knows nothing about files. It
receives the design variables as arguments, shows the stimulus, waits for a
response, and returns a dictionary:

```{code-block} python
def run_trial(ihrl, intensity_target_left, intensity_target_right,
              intensity_bg_left, intensity_bg_right, **kwargs):
    display_stim(ihrl, intensity_target_left, intensity_target_right, intensity_bg_left, intensity_bg_right)
    response = respond(ihrl)

    if response == "Left":
        result = 'left' # or a number, for example 0
    elif response == "Right":
        result = 'right' # or a number, for example 1

    return {"response": response, "result": result}
```

The response is converted into a result, here which side the participant chose,
as the string `'left'` or `'right'`. A number would do as well. What matters is
that the conversion happens in one place, and that the raw button is returned
alongside it, so that the data can be re-scored later.

The `**kwargs` matters. The trial dictionary contains every column of the design
file: the four intensities that `run_trial` needs, but also `trial`,
`probe-position` and `probe-context`, which it has no use for. Swallowing the
extra keys means you can add a descriptive column to the design without touching
the trial logic. Python accepts keys such as `probe-position` here even though
they are not valid argument names, because they only ever land in `kwargs`.

Capturing the response is a separate function:

```{code-block} python
def respond(ihrl):
    press, _ = ihrl.inputs.readButton(btns=("Left", "Right", "Escape", "Space"))

    if press in ("Escape", "Space"):
        # Raise SystemExit Exception
        sys.exit("Participant terminated experiment.")
    else:
        return press
```

Both Escape and Space end the experiment, by raising the `SystemExit` that
`experiment_main` catches.


## The stimulus

`stimuli.py` builds the display with plain numpy, without a stimulus library:

```{code-block} python
# constants
TARGET_SIZE = (25, 25) # size of middle target, in pixels
SIZE = (200, 200)   # size of one half of SBC, in pixels

def sbc(intensity_left,
        intensity_right,
        intensity_bg_left,
        intensity_bg_right):

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
```

Each half is a 200 by 200 pixel background with a square target in its middle,
and the two halves are placed side by side with `np.hstack`, giving a 200 by 400
pixel image. Note that `TARGET_SIZE` is applied on both sides of the center, so
the target is 50 by 50 pixels. Run `python stimuli.py` to see three example
displays.


## Who does what

When adapting this example, or any of the templates, keep this division of labor
in mind: `design.py` decides *what* is tested, `experiment_logic.py` decides what
*happens* in a trial, `stimuli.py` decides what it *looks like*,
`data_management.py` decides *where things go*, and `run_experiment.py` only
sequences them.


## Where to go next

The [experiment templates](../templates/templates-intro) are complete experiments
built on exactly this structure. Each one changes `design.py`,
`experiment_logic.py` and `stimuli.py`, and leaves `data_management.py`
essentially untouched.
