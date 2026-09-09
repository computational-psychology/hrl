# 2-AFC/2-IFC

## Two alternatives, in space or in time

In a **two-alternative forced choice** (2-AFC) task the participant is shown two
alternatives and must pick one. There is no "I cannot tell" option, which is the
point: forcing a choice on every trial means that even at levels the participant
claims not to see, their performance still carries information.

The two alternatives can be separated in space or in time.

- In a **spatial** 2-AFC task the two alternatives are shown side by side, and
  the participant indicates which side. The [MLCM](MLDS-MLCM) template is an
  example of this shape.
- In a **two-interval forced choice** (2-IFC) task the two alternatives are
  shown one after the other, in two timed intervals, at the same place on the
  screen. The participant indicates which *interval*.

2-IFC is the right choice when position on the screen could itself influence the
answer, for instance because the display is not homogeneous, or because the
stimulus is at an eccentricity where sensitivity differs between sides. The cost
is that the trial takes longer and depends on accurate timing, and that the
participant has to hold the first interval in memory.

This template implements the 2-IFC case: a contrast detection task in which one
of the two intervals contains a Gabor patch at some contrast and the other
contains the same display at the pedestal contrast.

The full example is at
[`examples/templates/2IFC_experiment/`](https://github.com/computational-psychology/hrl/tree/master/examples/templates/2IFC_experiment).

The [managing data](../useful-examples/managing-data) page describes a 2-IFC
trial conceptually; this page is about how it is actually run.


## Install requirements

```
pip install pandas stimupy
```

Sounds are produced with `pygame`, which `HRL` already requires.


## The design

The design is blocked: one spatial frequency and one contrast increment per
block. Within a block, all trials are the same, differing only in which interval
contains the increment, and in the randomly chosen orientation and phase of the
Gabor.

```{code-block} python
spatial_frequencies = [0.5, 2, 8]
contrast_values = np.logspace(-0.5, -1, 2)

# In this design we do not care about orientation and phase of the Gabor,
# but we randomly pick one orientation and phase for each trial from
# the following possible values
orientations = [0, 30, 60, 90, 120, 150]  # 6 possible orientations
phases = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]  # 12 possible phase shifts

Nrepeats = 5  # n repeats per contrast level
FEEDBACK = 0 # 1: with or 0: without feedback

SIGNIFIER = "2IFC"
```

Orientation and phase are randomized per trial rather than being design
variables. Otherwise a participant could learn the exact appearance of the
signal and detect it by pattern matching rather than by seeing it.

`generate_block` builds one block for a given spatial frequency and contrast
increment `delta`:

```{code-block} python
def generate_block(sf, delta, pedestal=0, Nrepeats=10):
    """Experimental design for one block of trials.

    In this case all trials are the same, just repeated Nrepeats
    and randomly swapped 1st or 2nd interval.
    """

    trials = []
    for i in range(Nrepeats):
        # Randomly choose if 1st or 2nd interval has contrast increment
        if random.randint(0, 1) == 0:
            first = pedestal
            second = pedestal + delta
            correct = 2
        else:
            first = pedestal + delta
            second = pedestal
            correct = 1

        ori = random.choice(orientations)
        phase = random.choice(phases)
        line = [sf, ori, phase, pedestal, delta, first, second, correct, FEEDBACK]
        trials.append(line)
    ...
```

Note the `correct` column. Which interval holds the signal is decided when the
design is generated, written to the design file, and read back at trial time.
The trial logic does not choose it and does not need a random number generator
at all. This is what makes a session reproducible from its design file.

`generate_session` then loops over the spatial frequencies and contrasts, giving
one block per combination:

```{code-block} python
def generate_session():
    i = 0 # counter
    for sf in spatial_frequencies:
        for c in contrast_values:
            block = generate_block(sf, c, pedestal=0, Nrepeats=Nrepeats)
            block_id = f"{SIGNIFIER}-{i}"

            # Save to file
            filepath = data_management.design_filepath(block_id)
            block.to_csv(filepath)

            i += 1
```


## The stimulus

A Gabor patch, with the contrast converted into a pair of intensities around the
background:

```{code-block} python
def gabor(
    sf,
    contrast,
    sigma=0.5,
    orientation=0, # in degrees
    phase=0, # in degrees
    intensity_background=INTENSITY_BACKGROUND,
):

    visual_size = IM_SIZE

    # min and max values of the sinusoid
    l1 = intensity_background - contrast/2
    l2 = intensity_background + contrast/2

    return stimupy.stimuli.gabors.gabor(
           visual_size=visual_size,
           ppd=PPD,
           frequency=sf,
           rotation=orientation,
           phase_shift=phase,
           intensities=(l1, l2),
           sigma=sigma)
```

The background intensity is `0.5` in this module, and the sinusoid is placed
symmetrically around it. At `contrast=0`, which is the pedestal used by the
design, `l1 == l2 == 0.5` and the display is uniform. So the non-signal interval
is a blank field at the background intensity, not noise.

```{important}
`INTENSITY_BACKGROUND` in `stimuli.py` and `bg` in the `SETUP` dictionary of
`run_experiment.py` are two separate numbers, and they must agree, or the patch
will sit on a visible square of a different intensity. In this template both are
`0.5` in the non-lab setup, but the two lab setups use `0.1` and `0.27` for
`bg`. Adapting this template to the lab means changing `INTENSITY_BACKGROUND`
too.
```


## Timing a trial

This is the part that distinguishes this template. A trial is a fixed sequence
of timed displays:

```{code-block} python
    time.sleep(0.5)

    ### 1st interval
    # draw and flip first interval
    gabor1_texture.draw(pos=pos, sz=(gabor1_texture.wdth, gabor1_texture.hght))
    ihrl.graphics.flip(clr=True)  # flips the frame buffer to show everything
    ihrl.sounds[0].play(loops=0, maxtime=int(0.5*1000)) # stim time in ms
    time.sleep(0.5)

    ### ISI
    display_fixation_cross(ihrl)
    time.sleep(0.25)

    ### 2nd interval
    # draw and flip second interval
    gabor2_texture.draw(pos=pos, sz=(gabor1_texture.wdth, gabor1_texture.hght))
    ihrl.graphics.flip(clr=True) # flips the frame buffer to show everything
    ihrl.sounds[1].play(loops=0, maxtime=int(0.5*1000)) # stim time in ms
    time.sleep(0.5)

    ### wait for response
    display_fixation_cross(ihrl, intensity=0)
    btn, t1 = ihrl.inputs.readButton(btns=["Left", "Right", "Escape", "Space"])
```

Half a second of first interval, a quarter second inter-stimulus interval
showing only the fixation cross, half a second of second interval, then the
response. Left means the first interval, Right the second.

Both textures are created **before** the sequence starts:

```{code-block} python
    # Convert the stimulus image(matrix) to an OpenGL texture
    gabor1_texture = ihrl.graphics.newTexture(gabor1["img"])
    gabor2_texture = ihrl.graphics.newTexture(gabor2["img"])
```

This is essential in a timed paradigm. Generating a stimulus and uploading it to
the graphics card takes an unpredictable amount of time; doing it between the
two intervals would make the inter-stimulus interval longer than 0.25 seconds by
an unknown amount. Prepare everything, then run the sequence.

```{important}
{py:func}`time.sleep` is accurate to roughly a millisecond, but it is not
synchronized to the monitor. A 0.5 second interval requested this way will be
0.5 seconds plus or minus a frame. For detection thresholds this is usually
acceptable; for experiments where duration is the manipulated variable, count
frames instead, using the measured refresh rate. See
[refresh rate](../calibration/refresh-rate).
```


## Marking the intervals with sound

The two intervals look alike, so each is marked with a tone. `HRL` does not
provide audio, but `pygame`, which it already uses, does. The template
generates four pure tones as numpy arrays and attaches them to the `HRL` object
as a plain attribute:

```{code-block} python
def make_sound(f, sampleRate=44100):
    x = np.arange(0, sampleRate)
    arr = (4096 * np.sin(2.0 * np.pi * f * x / sampleRate)).astype(np.int16)
    return arr
```

```{code-block} python
if __name__ == "__main__":
    # Sound to be played at each interval
    f1, f2, f3, f4 = 500, 600, 800, 300
    pygame.mixer.pre_init(44100, -16, 1)

    # Create HRL interface object with parameters that depend on the setup
    ihrl = HRL(**SETUP, photometer=None, db=True)

    # initializing sounds
    sound1 = pygame.sndarray.make_sound(make_sound(f1))
    sound2 = pygame.sndarray.make_sound(make_sound(f2))
    sound3 = pygame.sndarray.make_sound(make_sound(f3))
    sound4 = pygame.sndarray.make_sound(make_sound(f4))
    sounds = [sound1, sound2, sound3, sound4]

    ihrl.sounds = sounds
```

The first two tones, 500 and 600 Hz, mark the first and second interval. The
last two, 800 and 300 Hz, are the correct and incorrect feedback tones.

```{note}
`ihrl.sounds` is not part of the `HRL` interface. It is an attribute the script
attaches to the object so that `experiment_logic.run_trial` can reach the sounds
without a global. This is a convenient pattern for anything you want to carry
alongside the display and input devices, but do not expect `HRL` itself to know
about it.

Note also that `pygame.mixer.pre_init` is called *before* `HRL` is constructed.
`HRL` initializes `pygame`, and mixer settings have to be in place before that
happens.
```


## Scoring and feedback

The response is scored against the `correct` column that came from the design
file:

```{code-block} python
    if (btn=="Left" and correct==1) or (btn=="Right" and correct==2):
        response_correct = 1
        if feedback:
            ihrl.sounds[2].play(loops=0, maxtime=100)  # maxtime in ms
    else:
        response_correct = 0
        if feedback:
            ihrl.sounds[3].play(loops=0, maxtime=100)  # maxtime in ms

    # Raise SystemExit Exception
    if (btn == "Escape") or (btn == "Space"):
        sys.exit("Participant terminated experiment.")

    # end trial
    return {"response": btn, "response_correct": response_correct, "resp.time": t1}
```

Feedback is per trial and controlled by the `feedback` column, which comes from
the `FEEDBACK` constant in `design.py`. Because it travels through the design
file rather than being read from the module at trial time, a block run with
feedback stays marked as such in the results.

Both the raw button and the scored result are returned. Keep both: the raw
response lets you re-score the data later if you decide the mapping was wrong,
and it is the only record of what the participant actually did.


## Related

- [MLDS/MLCM](MLDS-MLCM) is the other forced-choice template, without timed
  intervals.
- [managing data](../useful-examples/managing-data) explains the design and
  results files, and describes the 2-IFC trial structure conceptually.
- [refresh rate](../calibration/refresh-rate) matters for any timed paradigm.
