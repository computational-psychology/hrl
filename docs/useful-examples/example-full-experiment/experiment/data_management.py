"""Manage data (design and results) for experiments

Broadly, _experimental data_ fall into two categories:
- _design_, the parameter values and variables set by the experiment(er)
- _results_, the data corresponding to participant responses

Design will include all kinds of variables,
most of which will be set before the start of the experiment.
Moreover, the experimental design may require a specific order trials,
or at least that trials are randomized in some specific way.
Thus, we cannot always generate the design online, i.e., during the experiment.
Instead, we want to be able to generate the design beforehand,
and load it when the participant is ready.

An additional advantage of pre-generating the design for a whole block & session (see below),
is that it makes the experiment _interruptible_.
Although not recommended,
if the participant needs to take a break and continue later,
the experiment can be stopped.
Preliminary results should have be stored so far.
Upon resuming, the experiment can load the design, compare which trials have been completed,
and continue where the participant left off.

The functions in this file are *only* for managing blocks, sessions, files.
The actual design of a trial/block/session should be defined in a separate module.


## Data structures
Generally while the experiment is running, then, we should have 3 datastructures:
- To store the current trial design & results:
    - a `dict`ionary seems like a good structure for this,
      because it can be expanded to contain any information we want to store.
      Additionally, it can be the arguments to a function like `run_trial(**trial_dict)`.
- To keep track of all the trials in a block (and which are completed)
    - a `list` -- of dictionaries, where each entry is a trial-dictionary --
      because of the sequential ordering of lists
- To keep track of the blocks in a session (and which are completed)

## File structure
To save data, we **only** use `.csv`-files.
Ideally, we want to _append_ new trial results to an exsiting file:
we don't want to accidentally overwrite previous trials.

We use **1 (one)** `<>.results.csv` _per block_,
which thus contains all trials from that block.
Subdirectories (`<..>/<session>/<block>/...csv`) are very annoying to work with;
searching over filenames is easier.
Thus, we use the _filename_ to make clear which participant, session, task, block, etc.
these results belong to:
`f"{participant}_{session_id}_{block_id}.results.csv"`, e.g. `jxv_20230626_matching-2_results.csv`

Similarly, there is a corresponding `<>.design.csv`-file for every results file.
The design is generated before data collection
 -- usually all design files for a _session_ are generated at once,
 at the start of that session (see below).

## Folder structure
Typically, we keep all experiment _data_
separate from the code, in `data` subdirectory.
Within this subdirectory, the `<>.results.csv` files
are further subdivided by participant:
```
top_level_repository
  /data
    /results
      /jxv
        /jxv_20230626_matching-1_results.csv
        /jxv_20230626_matching-2_results.csv
        /jxv_20230630_matching-1_results.csv
        /...
      /mxm
        /mxm_20230620_matching-1_resuls.csv
        ...
    /design
      /jxv
        /jxv_20230626_matching-1.design.csv
        /jxv_20230626_matching-2.design.csv
        /jxv_20230630_matching-1.design.csv
        /...
      /mxm
        ...
  /experiment
    data_management.py
    design.py
    experiment.py
    stimuli.py
    ...
  /analysis
    ...
```
"""
import csv
import glob
from datetime import datetime
from pathlib import Path

import pandas as pd

LANG = "en"
if LANG == "de":
    participant = input("Bitte geben Sie Ihre Initialen ein (ex.: DEMO): ") or "DEMO"
if LANG == "en":
    participant = input("Please enter participant initials (ex.: DEMO): ") or "DEMO"

# Experiment path:
experiment_path = Path().absolute()

# Overall datapath
datapath = experiment_path.parent / "data"
datapath.mkdir(parents=True, exist_ok=True)  # create datapath + parents, if does not exist
print(f"Saving and loading data in {datapath}")

# Designs
designs_dir = datapath / "design" / participant
designs_dir.mkdir(parents=True, exist_ok=True)

# Results
results_dir = datapath / "results" / participant
results_dir.mkdir(parents=True, exist_ok=True)

# Current session (today's date)
session_id = datetime.today().strftime("%Y%m%d")


def design_filepath(block_id):
    """Construct filepath to design file for given block

    Will generally be in the form of "<designs_dir>/<participant>_<session_id>_<block_id>.design.csv"

    Parameters
    ----------
    block_id : str
        identifier-string for block

    Returns
    -------
    Path
        filepath to block design file
    """

    # Design filename for this block
    filename = f"{participant}_{session_id}_{block_id}.design.csv"

    # Full filepath design file
    return designs_dir / filename


def results_filepath(block_id):
    """Construct filepath to results file for given block

    Will generally be in the form of "<results_dir>/<participant>_<session_id>_<block_id>.results.csv"

    Parameters
    ----------
    block_id : str
        identifier-string for block

    Returns
    -------
    Path
        filepath to block results file
    """

    # Results filename for this block
    filename = f"{participant}_{session_id}_{block_id}.results.csv"

    # Full filepath resultsfile
    return results_dir / filename


def save_block(block, block_id):
    """Save (append) whole block data to results.csv file

    Parameters
    ----------
    block : List[dict]
        block data structure: a list of dicts, where each dict is a trial
    block_id : str
        string-identifier for this block
    """
    filepath = results_filepath(participant, block_id)
    with filepath.open(mode="a") as results_file:
        writer = csv.DictWriter(results_file, fieldnames=block[0].keys())
        writer.writeheader()
        writer.writerows(block)


def save_trial(trial, block_id):
    """Save (append) whole block data to results.csv file

    Parameters
    ----------
    trial : dict
        trial data structure
    block_id : str
        string-identifier for this block
    """

    # Get filepath
    filepath = results_filepath(block_id)

    # Create, if it does not exist
    if not filepath.exists():
        print(f"creating results file {filepath}")
        with filepath.open(mode="w") as results_file:
            header_writer = csv.writer(results_file)
            header_writer.writerow(trial.keys())

    # Save
    print(f"saving trial to {filepath}")
    with filepath.open(mode="r") as results_file:
        reader = csv.DictReader(results_file)
        headers = reader.fieldnames
    with filepath.open(mode="a") as results_file:
        writer = csv.DictWriter(results_file, fieldnames=headers)
        print(trial)
        writer.writerow(trial)


def get_incomplete_trials(block_id):
    """Get not-yet completed trials for given block_id

    Compares block design.csv to results.csv (if exists)
    to find incomplete trials.

    Parameters
    ----------
    block_id : str
        string-identifier for this block

    Returns
    -------
    pandas.DataFrame
        block data structure (list of dicts, where each dict is a trial),
        containing only incomplete trials
    """

    # Load block design: all trials in the block
    design = pd.read_csv(design_filepath(block_id))

    # Read completed_trials from results file, if it exists
    block_results = results_filepath(block_id)
    if block_results.exists():
        # Load block results
        completed_trials = pd.read_csv(results_filepath(block_id))

        # Anti-join
        uncompleted_trials = pd.merge(
            design,
            completed_trials,
            how="outer",
            indicator=True,
        )
        uncompleted_trials = uncompleted_trials.loc[
            uncompleted_trials["_merge"] == "left_only"
        ].drop(
            columns=["_merge", "response", "start_time", "stop_time"],
            errors="ignore",
        )
    else:
        uncompleted_trials = design

    return uncompleted_trials


def get_incomplete_blocks(block_signifier=""):
    """Find not-yet completed blocks for this session

    Compares block design.csv's to results.csv's (if exists)
    to find incomplete trials.
    Any block with incomplete trials, is considered an incomplete block
    (only the incomplete trials are returned)

    Parameters
    ----------
    block_signifier : str, optional
        block signifier (e.g., task, condition) to check for.
        If no block signifier provided, will return any incomplete blocks

    Returns
    -------
    dict[str, pandas.DataFrame]
        incomplete blocks, in a dict of `block_id: block` (DataFrame)
    """

    block_designs = sorted(designs_dir.glob(f"{participant}_{session_id}_{block_signifier}*.csv"))

    incomplete_blocks = {}
    for block_path in block_designs:
        filename = Path(Path(block_path).stem).stem
        block_id = filename.split("_")[2]

        incomplete_trials = get_incomplete_trials(block_id)
        if len(incomplete_trials) > 0:
            incomplete_blocks[block_id] = incomplete_trials

    return incomplete_blocks


def get_next_block(block_signifier=""):
    """Get next (incomplete) block to run

    Compares block design.csv's to results.csv's (if exists)
    to find incomplete trials.
    Any block with incomplete trials, is considered an incomplete block.

    Parameters
    ----------
    block_signifier : str, optional
        block signifier (e.g., task, condition) to check for.
        If no block signifier provided, will return any incomplete blocks

    Returns
    -------
    block_id : str
        block identifier string, combining a signifier (e.g., task, condition) and number,
        e.g. "matching-2"
    block : pandas.DataFrame
        block data structure (dataframe, where each row is a trial),
        containing only incomplete trials
    """
    incomplete_blocks = get_incomplete_blocks(block_signifier)

    if incomplete_blocks:
        block_id, block = incomplete_blocks.popitem()
    else:
        block_id, block = None, None

    return block_id, block
