# MLDS/MLCM

This page covers two related scaling paradigms, each with its own template:

- **MLDS**, Maximum Likelihood Difference Scaling, recovers a perceptual scale
  from judgments about *differences* between stimuli along one dimension.
- **MLCM**, Maximum Likelihood Conjoint Measurement, recovers how *two*
  dimensions jointly determine appearance, from judgments comparing stimuli
  that differ on both.

Both are forced choice: on every trial the participant presses one of two
buttons and the trial ends. There is no adjustment loop, so a trial here is much
simpler than in the [matching templates](asymmetric-matching). What makes them
interesting is the design: the trials are combinations produced by
{py:mod}`itertools`, and the analysis afterwards fits a scale to the pattern of
choices.

Full sources:
[`examples/templates/mlds_experiment/`](https://github.com/computational-psychology/hrl/tree/master/examples/templates/mlds_experiment)
and
[`examples/templates/mlcm_experiment/`](https://github.com/computational-psychology/hrl/tree/master/examples/templates/mlcm_experiment).

Both use the module layout described in the
[templates overview](templates-intro) and the data management described in
[managing data](../useful-examples/managing-data). Only `design.py`,
`stimuli.py` and `experiment_logic.py` differ, and those are what this page
narrates.


## Install requirements

```
pip install pandas stimupy
```


## MLDS: difference scaling with triads

### The task

The participant sees three stimuli at once, arranged in a triangle: one at the
top, referred to as the *middle* stimulus, and two below it, left and right.
The two pairs to compare are left-with-middle and middle-with-right, and the
question is which of those two pairs differs more:

```
Triads paradigm
Please select the stimulus pair that is
MOST DIFFERENT in BRIGHTNESS
LEFT-MIDDLE or MIDDLE-RIGHT

Press either:
LEFT or RIGHT
```

Repeated over many triads, the pattern of choices constrains where each
luminance must sit on a perceptual scale, which is what the MLDS analysis
recovers.

### The design

Ten luminances are sampled linearly, and every combination of three of them is
a trial:

```{code-block} python
nl = 10
luminances = np.linspace(0.1, 0.9, nl).round(3)


def generate_block(shuffle=True):
    stimuli_design = list(itertools.combinations(luminances, 3))

    trials = []
    for t in stimuli_design:
        t = list(t)

        # Randomy shuffle order L-R-Down
        if random.randint(0, 1):
            t1, t2, t3 = t
        else:
            t3, t2, t1 = t

        line = [t1, t2, t3]
        trials.append(line)

    # creates dataframe with all trials
    block = pd.DataFrame(trials, columns=['l1', 'l2', 'l3'])

    if shuffle:
        # Shuffle trial order
        block = block.reindex(np.random.permutation(block.index))
    block.reset_index(drop=True, inplace=True)
    block.index.name = "trial"

    return block
```

{py:func}`itertools.combinations` with `r=3` over ten luminances gives 120
triads, each an ordered ascending triple. Presenting them all in ascending order
would mean the middle stimulus is always the middle luminance, so each triple is
randomly either kept or reversed. The ordering *within* the triple is preserved
in both cases, which is what the difference judgment requires; only the
direction flips.

`generate_block` takes a `shuffle` argument because `design.py` is also runnable
on its own, to write out an unshuffled design used for measuring the luminances
of the stimuli:

```
python design.py
```

### The stimulus

The stimuli are circular simultaneous brightness contrast displays: a disk
surrounded by rings, built with `stimupy`:

```{code-block} python
def sbc_circular(intensity_target, intensity_background, bg):
    return stimupy.bullseyes.circular(
        **resolution,
        intensity_target=intensity_target,
        intensity_background=bg,
        intensity_rings=[intensity_background, intensity_background, intensity_background],
        n_rings=3,
    )
```

Running `python stimuli.py` renders the whole set into `../stimuli.pdf`, which
is committed in the template folder as
[`mlds_experiment/stimuli.pdf`](https://github.com/computational-psychology/hrl/blob/master/examples/templates/mlds_experiment/stimuli.pdf).
It is worth generating that figure whenever you change the stimulus parameters:
it is much faster than starting the experiment to see what a change did.

### A trial

```{code-block} python
def run_trial(ihrl, l1, l2, l3, **kwargs):
    """ Function that runs sequence of events during one trial"""

    # Fixation cross
    display_fixation_cross(ihrl)

    # sleeps for 250 ms # using system time (inaccurate)
    time.sleep(0.25)

    # Display stimuli
    display_stim(ihrl, l1=l1, l2=l2, l3=l3)

    # Wait for answer
    btn, t1 = ihrl.inputs.readButton(btns=['Left', 'Right', 'Escape', 'Space'])

    # Raise SystemExit Exception
    if (btn == "Escape") or (btn == 'Space'): sys.exit("Participant terminated experiment.")

    # end trial
    return {"response": btn, 'resp.time': t1}
```

The trial is: fixation cross, brief pause, three stimuli, one button press. The
returned dictionary holds the raw button and the time until it was pressed;
`run_block` adds the timestamps and the design variables around it.

```{note}
Both `Escape` and `Space` terminate the experiment here, so the participant has
no accept button and no way to skip a trial. That is intentional in a
forced-choice task, but it is worth knowing when adapting the template: if you
add a "no difference" option, it needs its own button.
```

The layout is computed from the resolution in degrees, not in pixels:

```{code-block} python
ppd = stimuli.resolution['ppd']

# Determine position: we want the stimulus around the center
center = (ihrl.width // 2, ihrl.height // 2)

R = 4 # deg
offset_x = int(ppd * R * 0.866) # cos(30) = 0.866
offset_y = int(ppd * R * 0.5)   # sin(30) = 0.5
```

The three stimuli sit on a circle of radius 4 degrees around the center of the
screen, at 90, 210 and 330 degrees. Expressing the offsets in degrees times
pixels-per-degree, rather than in pixels, means the geometry stays correct if
the same experiment is run on a monitor with a different pixel density.

```{note}
Timing here uses {py:func}`time.sleep`, which is not frame-accurate. For a
paradigm where the stimulus stays up until the participant responds, that is
fine. If your trial depends on exact presentation durations, count frames with
`flip()` instead, and see [refresh rate](../calibration/refresh-rate).
```


## MLCM: conjoint measurement with pairs

### The task

The participant sees two stimuli side by side and chooses the brighter one:

```
Paired comparisons task
Please select the stimulus that is
BRIGHTER
Press either:
LEFT or RIGHT
```

What makes it conjoint measurement rather than a plain paired comparison is the
design: the two stimuli differ on **two** dimensions at once, the intensity of
the target and the intensity of its surround. The analysis then estimates the
contribution of each dimension separately.

### The design

```{code-block} python
n_luminances = 8
luminances = np.linspace(0.1, 0.9, n_luminances).round(3)
surrounds = (0.0, 1.0)


def generate_block():
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
```

The two-step construction is worth reading carefully. First, `targets` is the
full crossing of 8 luminances with 2 surrounds, giving 16 distinct stimuli.
Then {py:func}`itertools.combinations` with `r=2` pairs each of those with each
other, giving 120 trials. Each pair is then shuffled, so that which member
appears on the left is random. Finally the trial order itself is shuffled.

The design file has one column per parameter per side, four in total. That flat
layout is what lets `run_trial` be called as `run_trial(ihrl, **trial)`.

### The stimulus

One two-sided display is generated per trial, containing both stimuli:

```{code-block} python
def sbc(
    ppd=PPD,
    intensity_targets=(0.5, 0.5),
    intensity_contexts=(0.0, 1.0),
    target_size=TARGET_SIZE,
    intensity_background=INTENSITY_BACKGROUND,
):
    visual_size = np.array((7, 10)) * target_size

    return stimupy.stimuli.sbcs.circular_two_sided(
        ppd=ppd,
        visual_size=visual_size,
        target_radius=target_size / 2,
        surround_radius=target_size,
        intensity_target=intensity_targets,
        intensity_surround=intensity_contexts,
        intensity_background=intensity_background,
    )
```

Generating both sides as a single image, rather than two images drawn side by
side, guarantees they are aligned and separated by exactly the intended
distance.

### A trial

```{code-block} python
def run_trial(
    ihrl,
    target_intensity_left,
    surround_intensity_left,
    target_intensity_right,
    surround_intensity_right,
    **kwargs
):
    """Function that runs sequence of events during one trial"""

    # Fixation cross
    display_fixation_cross(ihrl)

    # sleeps for 250 ms # using system time (inaccurate)
    time.sleep(0.25)

    # Display stimuli
    display_stim(
        ihrl,
        target_intensity_left=target_intensity_left,
        surround_intensity_left=surround_intensity_left,
        target_intensity_right=target_intensity_right,
        surround_intensity_right=surround_intensity_right,
    )

    # Wait for answer
    btn, t1 = ihrl.inputs.readButton(btns=["Left", "Right", "Escape", "Space"])

    # Raise SystemExit Exception
    if (btn == "Escape") or (btn == "Space"):
        sys.exit("Participant terminated experiment.")

    # end trial
    return {"response": btn, "resp.time": t1}
```

Identical in shape to the MLDS trial. That is the point of the shared layout:
once you have read one template, the next one is only a `design.py` and a
`stimuli.py` away.

Both templates draw a fixation marker before and with the stimulus:

```{code-block} python
def draw_fixation_cross(ihrl):
    # draws fixation dot in the middle
    # TODO: use stimupy to actually draw a cross and not a square.
    fix = ihrl.graphics.newTexture(np.ones((5, 5)) * 0.0)
    fix.draw((ihrl.width // 2, ihrl.height // 2))
```

It is a 5 by 5 black square rather than a cross, as the comment in the source
admits. It is drawn without a flip, so it composes with whatever is drawn next
into the same frame.


## Selecting blocks per paradigm

Both templates pass a `block_signifier` when looking for work to do:

```{code-block} python
incomplete_blocks = data_management.get_incomplete_blocks(block_signifier="mlcm")
```

and name their blocks accordingly, `f"mlcm-{i}"` and `f"mlds-{i}"`. This is how
you run more than one paradigm for the same participant on the same day without
either experiment picking up the other's design files. If you combine paradigms
in one study, give each its own signifier.


## Related

- [Eyetracking](eyetracking) is this MLCM experiment extended with an EyeLink
  eyetracker.
- [2-AFC/2-IFC](2-AFC-2-IFC) is the other forced-choice template, with timed
  intervals.
- [managing data](../useful-examples/managing-data) explains the design and
  results plumbing both templates rely on.
