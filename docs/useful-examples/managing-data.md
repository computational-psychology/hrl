# Managing data

Everything so far has thrown its results away. This page is about keeping them:
how to write down what the experiment asked, what the participant answered, and
how to arrange the files so that an interrupted session can be picked up again
the next day.

The full example is at
[`examples/tutorials/4_managing_design_results/`](https://github.com/computational-psychology/hrl/tree/master/examples/tutorials/4_managing_design_results).
It is the first example with more than one module. `run_experiment.py` is the
entry point, `design.py` defines what the experiment tests, `experiment_logic.py`
defines what one trial does, `data_management.py` handles files and folders, and
`stimuli.py` and `text_displays.py` are as in the previous examples.

Every [experiment template](../templates/templates-intro) in the next section
reuses this same layout, so it is worth reading this page before those.


## Overview

```{mermaid}
graph LR;
    setup --> next_block --> run_block
    next_block <--> incomplete_blocks <--> incomplete_trials
    next_block <--> generate_design
    generate_design <--> generate_block

    run_block --> run_trial --> define --> display --> capture --> save_trial
    save_trial --> run_block
    run_block --> exit

    subgraph HRL
        display
        capture[capture participant response]
    end

    subgraph data_management.py
        incomplete_blocks
        incomplete_trials

        next_block

        save_trial
    end

    subgraph stimuli.py
        define[define stimuli]
    end

    subgraph design.py
        generate_design
        generate_block

        run_trial
    end

    subgraph run_experiment.py
        setup

        run_block

        exit[cleanup & exit]
    end
```


## Install requirements

This example uses [pandas](https://pandas.pydata.org/) to manage tabular data,
on top of `HRL`, `stimupy` and `Pillow`:

```
pip install pandas
```


## Separating design from results

Experimental data fall into two categories:

- **design**, the parameter values and variables set by the experimenter
- **results**, the data corresponding to participant responses

Design includes all kinds of variables, most of which are set before the
experiment starts. The experimental design may also require a specific order of
trials, or at least that trials are randomized in some specific way. So we
cannot always generate the design online, that is, during the experiment.
Instead we want to generate the design beforehand, and load it when the
participant is ready.

An additional advantage of pre-generating the design for a whole block and
session is that it makes the experiment **interruptible**. Although it is not
recommended, if the participant needs to take a break and continue later, the
experiment can be stopped: the results collected so far have already been
written to disk. On resuming, the experiment loads the design, compares it
against which trials have been completed, and continues where the participant
left off.

In this template, `design.py` generates the design, and `data_management.py`
manages the files and folder structure.


## The structure of experimental data

### Trial

The smallest unit of an experiment is a **trial**. A trial usually involves
displaying a single stimulus, or a few related stimuli, and collecting some
response from the participant. A trial is usually defined by some *level*
(luminance, contrast, and so on) of the stimulus. The exact structure of a trial
depends on the experiment and the task.

In a forced-choice task, for example a
[two-interval forced-choice](../templates/2-AFC-2-IFC) detection task, a single
trial involves presenting two timed displays to the participant. One contains
the stimulus at some level, the other does not (either blank, or noise). After
both displays have been presented, the participant responds once, indicating
which interval contained the stimulus. The next trial presents two displays
again, and now the stimulus may have a different level. The **trial results**
recorded are typically the response the participant gave (and whether it was
correct), the reaction time, and the overall timing of the trial. The **trial
design** is typically recorded alongside: the stimulus level, which interval
contained the stimulus, and any additional stimulus information.

In a [matching task](method-of-adjustment), a single trial involves a single
reference level in a single stimulus, which the participant then has to match by
adjusting the luminance of a probe. The next trial may present a different
reference, a different stimulus, and so on. Note that a single trial here
involves multiple displays and multiple responses: the participant gives
responses to adjust the probe, and each adjustment is displayed. The trial
results recorded are typically the probe luminance at the perceived match and
the overall timing; the trial design is the reference level and additional
stimulus information.

### Block

Several trials together form a **block**. Usually a block consists of one trial
for each unique stimulus level, either for the whole experiment or for some
condition (stimulus, noise level, and so on). Often we wish to repeat identical
trials to account for variability and noise; this can be done by simply having
multiple blocks with the same trials.

Whether and how to block trials depends on the experimental design. There are
several additional advantages to using blocks:

- they build in natural breaks for the participant, between each block
- they can reduce order effects, by randomizing or counterbalancing within and
  between blocks
- blocking by condition can make the procedure easier for the participant

Blocks are identified by a `block_id` string, which usually combines a signifier
(the task, the condition) and a number: `matching-2` for the second block of a
matching task in some session.

A block usually has no results separate from the trial results. What we do keep
track of is the **block design**: the order in which trials appear.

### Session

A **session** is the collection of all blocks run by a single participant in a
single sitting, that is, on a single day. Blocks within a session could differ,
for example in task (scaling versus matching), or could be straight repeats. The
order of blocks within a session may differ between sessions, either randomized
or predetermined, depending on the experiment. Generally all participants should
complete the same number of sessions, with the same number of blocks per
session, and no more than one session per day. Sessions are identified by a
`session_id` datestamp, for example `20230626`.

A session usually has no results separate from the block results. What we keep
track of is the **session design**: the order in which blocks appear.

So: a session consists of one or more blocks, a block consists of one or more
trials, and a participant may do one or more sessions.


## Data structures

While the experiment is running we need three data structures:

- the current trial's design and results: a `dict`. A dictionary can be expanded
  to hold any information we want to store, and it can be passed straight to a
  function as `run_trial(**trial_dict)`.
- all the trials in a block, and which are completed: a `list` of trial
  dictionaries, because lists preserve the ordering. Once loaded from file, this
  becomes a pandas `DataFrame` with one row per trial.
- the blocks in a session, and which are completed: a `dict` of
  `block_id: block`.


## File structure

To save data we use `.csv` files, and only `.csv` files. They are easy to open
and to view across platforms and programs. After a trial is completed, its
results are appended to a `<>.results.csv` file. In this tabular data, each row
is a trial (its design and its result) and each column is a parameter, a
variable, or a result:

```
participant,start_time,stop_time,reference_lum,match_lum
JXV,20211130:110132,20211130:110208,0.01,0.0110350968097
...
```

| participant |    start_time   |    stop_time    | reference_lum |    match_lum    |
| ----------- |-----------------| --------------- | ------------- | --------------- |
|     JXV     | 20211130:110132 | 20211130:110208 |      0.01     | 0.0110350968097 |
|     ...     |        ...      |       ...       |      ...      |       ...       |

Ideally we want to *append* new trial results to an existing file: we do not
want to accidentally overwrite previous trials.

We use exactly **one** `<>.results.csv` per block, containing all trials from
that block. Subdirectories of the form `<..>/<session>/<block>/...csv` are
annoying to work with, and searching over filenames is easier. So we use the
*filename* to record which participant, session, task and block the results
belong to:

```
f"{participant}_{session_id}_{block_id}.results.csv"
```

for example `jxv_20230626_matching-2.results.csv`. There is a corresponding
`<>.design.csv` file for every results file. The design is generated before data
collection, usually all design files for a session at once, at the start of that
session.


## Folder structure

We keep all experimental data separate from the code, in a `data` subdirectory.
Within it, the results files are further subdivided by participant:

```
top_level_repository
  /data
    /results
      /jxv
        /jxv_20230626_matching-1.results.csv
        /jxv_20230626_matching-2.results.csv
        /jxv_20230630_matching-1.results.csv
        /...
      /mxm
        /mxm_20230620_matching-1.results.csv
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
    run_experiment.py
    stimuli.py
    ...
  /analysis
    ...
```

`data_management.py` builds this tree when it is imported. It asks for the
participant initials, derives the session id from today's date, and creates the
directories if they do not exist:

```{code-block} python
LANG = "en"
if LANG == "de":
    participant = input("Bitte geben Sie Ihre Initialen ein (ex.: DEMO): ") or "DEMO"
if LANG == "en":
    participant = input("Please enter participant initials (ex.: DEMO): ") or "DEMO"

# Experiment path:
experiment_path = Path().absolute()

# Overall datapath
datapath = experiment_path.parent / "data"
datapath.mkdir(parents=True, exist_ok=True)

# Designs
designs_dir = datapath / "design" / participant
designs_dir.mkdir(parents=True, exist_ok=True)

# Results
results_dir = datapath / "results" / participant
results_dir.mkdir(parents=True, exist_ok=True)

# Current session (today's date)
session_id = datetime.today().strftime("%Y%m%d")
```

```{note}
`participant` and `session_id` are module-level names, not arguments. Every
other function in `data_management.py` reads them from there, which is why the
filepath helpers below take only a `block_id`. It also means that the module
must be imported after the experimenter is at the keyboard: importing it is what
asks for the initials.
```

Two one-line functions turn a `block_id` into a filepath:

```{code-block} python
def design_filepath(block_id):
    filename = f"{participant}_{session_id}_{block_id}.design.csv"
    return designs_dir / filename


def results_filepath(block_id):
    filename = f"{participant}_{session_id}_{block_id}.results.csv"
    return results_dir / filename
```


## Generating the design

`design.py` is the module you edit when you design your experiment. It defines
the variables that are manipulated, and how they are combined into trials. In
this example there are three: which stimulus, and three intensities.

```{code-block} python
LUMINANCES = [0, 0.25, 0.75, 1]

STIM_NAMES = stimuli.__all__


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
```

The triple comprehension is the full factorial combination of the three
variables: 4 times 4 times 4 is 64 trials in a block. The shuffle happens once,
here, and is then written to file. That is the point of pre-generating: the
order the participant will see is fixed on disk before the first trial runs, so
it survives an interruption.

`generate_session` calls `generate_block` for every stimulus and every repeat,
and writes each block to its own design file:

```{code-block} python
def generate_session(Nrepeats=2):
    for i in range(Nrepeats):
        for stim_name in STIM_NAMES:
            block = generate_block(stim_name)
            block_id = f"{stim_name}-{i}"

            # Save to file
            filepath = data_management.design_filepath(block_id)
            block.to_csv(filepath)
```

With two stimuli and two repeats, that is four design files, named
`DEMO_20230626_sbc-0.design.csv` and so on.


## Saving results, one trial at a time

Results are written after every single trial, not at the end of a block. If the
session is interrupted, whatever has been completed is already on disk.

```{code-block} python
def save_trial(trial, block_id):
    """Save (append) trial data to results.csv file

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
        writer.writerow(trial)
```

The file is opened in append mode, `"a"`, so an existing file is never
truncated. The header is written only when the file is created, and on every
subsequent call the header is read back from the file and used as the
`fieldnames` of the `DictWriter`. That way the column order of the file wins,
and a trial dictionary whose keys happen to be in a different order still lands
in the right columns.

```{note}
There is also a `save_block(block, block_id)` which writes a whole list of trial
dictionaries at once. It is convenient when converting old data, but for running
an experiment prefer `save_trial`: writing after each trial is what makes the
experiment resumable.
```


## Resuming where the participant left off

This is the part that pays for all the structure above. Which trials still need
to be run is not tracked in memory or in a state file. It is derived, every
time, by comparing the design file against the results file.

```{code-block} python
def get_incomplete_trials(block_id):
    """Get not-yet completed trials for given block_id

    Compares block design.csv to results.csv (if exists)
    to find incomplete trials.
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
```

The trick is the *anti-join*. An outer merge of design against results, with
`indicator=True`, adds a `_merge` column saying where each row came from. Rows
marked `left_only` are in the design but not in the results, which is exactly
the definition of a trial that has not been run. The result columns are then
dropped, so what comes back has the same shape as a freshly generated block and
can be fed straight into the block loop.

Because the comparison is on the design columns, this works no matter how the
session was interrupted, and it never double-runs a trial.

One level up, `get_incomplete_blocks` applies the same logic to every design
file of the current session:

```{code-block} python
def get_incomplete_blocks(block_signifier=""):
    block_designs = sorted(designs_dir.glob(f"{participant}_{session_id}_{block_signifier}*.csv"))

    incomplete_blocks = {}
    for block_path in block_designs:
        filename = Path(Path(block_path).stem).stem
        block_id = filename.split("_")[2]

        incomplete_trials = get_incomplete_trials(block_id)
        if len(incomplete_trials) > 0:
            incomplete_blocks[block_id] = incomplete_trials

    return incomplete_blocks
```

A block with at least one incomplete trial counts as an incomplete block, and
only its incomplete trials are returned. The optional `block_signifier` narrows
the glob to one task or condition, which matters in experiments that interleave
several.

```{note}
The glob is restricted to the current `session_id`, which is today's date. A
session interrupted yesterday and resumed today will therefore *not* be
continued: a new session is generated instead. This is deliberate, since a
session is defined as a single sitting.
```


## Running a block

`run_experiment.py` ties it together. `experiment_main` asks for the incomplete
blocks, generates a session if there are none, and runs them one by one:

```{code-block} python
def experiment_main(ihrl):
    # Get all blocks for this session
    incomplete_blocks = data_management.get_incomplete_blocks()
    if len(incomplete_blocks) == 0:
        # No existing blocks for this session. Generate.
        design.generate_session()
        incomplete_blocks = data_management.get_incomplete_blocks()
    print(f"{len(incomplete_blocks)} incomplete blocks")

    # Run
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
what makes resuming the default behaviour rather than an option.

`run_block` is the trial loop. Each row of the block dataframe is converted to a
dictionary, handed to `run_trial` as keyword arguments, updated with whatever
that returns, stamped with start and stop times, and saved:

```{code-block} python
def run_block(ihrl, block, block_id):
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
containing both design and result. That is why the anti-join above works on the
design columns: they are present in the results file too.

`run_trial` itself lives in `experiment_logic.py` and knows nothing about files.
It receives the design variables, displays, waits for a response, and returns a
dictionary:

```{code-block} python
def run_trial(ihrl, stim, intensity_target, intensity_left, intensity_right, **kwargs):
    display_stim(ihrl, stim, intensity_target, intensity_left, intensity_right)
    response = respond(ihrl)

    if response == "Left":
        result = intensity_left
    elif response == "Right":
        result = intensity_right

    return {"response": response, "result": result}
```

The `**kwargs` matters. The trial dictionary contains everything in the design
file, including the `trial` index column, which `run_trial` has no use for.
Swallowing the extra keys means you can add a column to the design without
touching the trial logic.

This is the whole division of labour to keep in mind when adapting the
templates: `design.py` decides *what* is tested, `experiment_logic.py` decides
what *happens* in a trial, `data_management.py` decides *where things go*, and
`run_experiment.py` only sequences them.


## Where to go next

The [experiment templates](../templates/templates-intro) are complete
experiments built on exactly this structure. Each one changes `design.py` and
`experiment_logic.py` and leaves `data_management.py` essentially untouched.
