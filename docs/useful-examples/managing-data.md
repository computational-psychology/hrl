# Managing data and a complete example 


## Separating design and results
To understand experimental data management,
it is important to first clarify the building blocks of _experimental data_.
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

In this demo / template, `design.py` defines functions to generate the design for the experiment,
while `data_management.py` helps manage files and folder structure.

## Structure of experimental data
### Trial
The smallest "unit" of an experiment, is a _trial_.
A trial usually involves displaying a single stimulus
or a few related stimuli,
and collecting some response(s) from the participant.
Important is that trial is usually defined by
some _level_ (luminance, contrast, etc. value) of the stimulus.
The exact structure of a trial depend on experiment and task.

In a forced-choice task for example,
such as a 2-interval forced-choice (2IFC) detection task,
a single trial invovles presenting two (timed) displays to the participant.
One will contain the stimulus at some (luminance, contrast, etc.) value,
the other will not contain the stimulus (either blank, or noise).
After both displays have been presented, the participant responds once
indicating which interval the stimulus appeared in.
A next trial will then present again two displays,
and now the stimulus may have a different (luminance, contrast, etc.) value.
The _trial result(s)_ that would be recorded are typically:
the response the participant gave (and whether that was correct or not),
and reaction time (how long it took the participant to respond),
and overall timing (how long the total trial took).
Additionally, the _trial design_ would typically be included:
the stimulus (luminance, contrast, etc.) value,
which interval contained the stimulus,
additional stimulus information.


In a matching task for example,
a single trial involves a single reference (luminance, contrast, etc.) value in a single stimulus,
which the participant then has to match by adjusting the luminance of a probe.
A next trial may then present a different reference, a different stimulus, etc.
Note that a single _trial_ here involves multiple displays and responses:
the participant will give responses to adjust the probe luminance,
which then also gets displayed.
The _trial result(s)_ that would be recorded are typically:
the probe luminance at perceived match,
and overall timing (how long the total trial took).
Additionally, the _trial design_ would typically be included:
the reference (luminance, contrast, etc.) value,
additional stimulus information.

### Block
Several _trials_ together form a _block_.
Usually, a block consists of one trial for each unique stimulus level (luminance, contrast, etc.),
either for the whole experiment, or for some _condition_ (stimulus, noise level, etc.).
Often we wish to repeat identical trials to account for variability and noise;
this can be done by simply having multiple blocks with the same trials.
Whether and how to block trials depends on the experiment design.
There are several additional advantages to using blocks:
- builds in natural breaks for the participant (between each block)
- can reduce order-effect by randomizing and/or counterbalancing within and/or between blocks
- _block_'ing by condition can make for an easier procedure for the participant
Blocks can be identified using a `block_id`-string,
which usually combines some signifier (e.g., the task, condition, etc.) and a number:
e.g. `matching-2` to indicate the 2nd block of a matching task in some session (see next)

A _block_ (usually) has no _results_ separate from the _trial results_.
We do typically keep track of _block design_:
the order in which trials appear.

### Session
A _session_ is the collection of all _blocks_ run by a single participant in a single sitting
(i.e., on a single day).
Blocks within a session could differ, e.g., in task (scaling vs. matching),
or could be straight repeats.
The order of blocks within a session may differ between sessions,
either through randomized or predetermined design (e.g., counterbalancing)
-- depending on the experiment.
Generally, all participant should complete the same number of sessions,
with the same number of blocks per session,
and no more than one session per day.
Thus, sessions can be identified using a `session_id` _datestamp_, e.g. `20230626`.

A _session_ (usually) has no _results_ separate from the _block results_.
We do typically keep track of _session design_:
the order in which blocks appear.

## Structures
A _session_ consists of 1 or more _blocks_
and a _block_ consists of 1 or more _trials_
A participant may do 1 or more _sessions_.

### Data structures
Generally while the experiment is running, then, we should have 3 datastructures:
- To store the current trial design & results:
    - a `dict`ionary seems like a good structure for this,
      because it can be expanded to contain any information we want to store.
      Additionally, it can be the arguments to a function like `run_trial(**trial_dict)`.
- To keep track of all the trials in a block (and which are completed)
    - a `list` -- of dictionaries, where each entry is a trial-dictionary --
      because of the sequential ordering of lists
- To keep track of the blocks in a session (and which are completed)

### File structure
To save data, we **only** use `.csv`-files.
These files are easy to open and view across platforms and programs.
After a trial is completed, we save the results to a `<>.results.csv` file.
In this tabular data,
each row is a trial (design & result),
and each column is some parameter, variable, or result.
For example:
```
participant,start_time,stop_time,reference_lum,match_lum
JXV,20211130:110132,20211130:110208,0.01,0.0110350968097
...
```

| participant |    start_time   |    stop_time    | reference_lum |    match_lum    |
| ----------- |-----------------| --------------- | ------------- | --------------- |
|     JXV     | 20211130:110132 | 20211130:110208 |      0.01     | 0.0110350968097 |
|     ...     |        ...      |       ...       |      ...      |       ...       |


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

### Folder structure
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
