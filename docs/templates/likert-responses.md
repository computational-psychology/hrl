# Likert scale

In the templates so far, a response is either a choice between alternatives or a
value the participant adjusts. This template collects a **rating**: the
participant places the stimulus on an ordered scale of five labelled options,
from "Left target is definitely brighter" through "Targets are equally bright"
to "Right target is definitely brighter".

A rating scale is the right instrument when you want a graded judgement rather
than a binary one, and when an "equal" response is a meaningful answer rather
than a failure to choose. Note the difference from
[2-AFC](2-AFC-2-IFC): there, forcing a choice is the whole design; here, the
middle option is deliberately available.

The full example is at
[`examples/templates/Likert_responses/`](https://github.com/computational-psychology/hrl/tree/master/examples/templates/Likert_responses).


## Install requirements

```
pip install pandas stimupy
```

Text here is drawn with `stimupy.components.texts` rather than with `Pillow`
directly.


## The scale

The options are a module-level list, and their number is not hard-coded anywhere
else:

```{code-block} python
RESPONSE_OPTIONS = [
    "Left target is definitely brighter",
    "Left target is maybe brighter",
    "Targets are equally bright",
    "Right target is maybe brighter",
    "Right target is definitely brighter",
]
FONTSIZE = 25
```

To change the scale, edit this list. Five options with a labelled midpoint is a
common choice, but the code below works for any odd or even number.


## Selecting on the scale

The interaction is deliberately close to
[adjustment](../useful-examples/method-of-adjustment): Left and Right move the
selection, Space accepts, Escape quits. What is being moved is an integer index
into the options rather than a continuous intensity.

```{code-block} python
def select(ihrl, value, range):
    """Allow participant to select a value from a range of options

    Returns
    -------
    int
        currently selected option
    bool
        whether this option was confirmed
    """
    try:
        len(range)
    except:
        range = (0, range)

    accept = False

    press, _ = ihrl.inputs.readButton(btns=("Left", "Right", "Escape", "Space"))

    if press == "Escape":
        # Raise SystemExit Exception
        sys.exit("Participant terminated experiment.")
    elif press == "Left":
        value -= 1
        value = max(value, range[0])
    elif press == "Right":
        value += 1
        value = min(value, range[1])
    elif press == "Space":
        accept = True

    return value, accept
```

The `max` and `min` clamp the index so that it cannot run off either end of the
list and raise an `IndexError`. This is the same idea as the gamut clamping in
`adjust`, without the warning screens: at the end of a rating scale there is
nothing to warn about, the selection simply stops moving.

The `try: len(range)` at the top lets the caller pass either a pair of bounds or
a single maximum. This template passes a pair, `range=(1, 5)`.

```{note}
This function shadows the builtin `range`, which is legal but not a good habit.
The same function in the [show stimuli](../useful-examples/show-stimuli) example
calls the parameter `rng` instead. Prefer that name if you copy this code.
```


## Drawing the scale

The selected option is marked by intensity: every label is drawn at intensity
`0.0` except the selected one, which is drawn at `1.0`.

```{code-block} python
def draw_options(ihrl, selection, ppd=stimuli.resolution["ppd"]):
    txt_ints = [0.0] * len(RESPONSE_OPTIONS)
    txt_ints[selection - 1] = 1.0

    # Generate textures
    response_textures = []
    for i, response in enumerate(RESPONSE_OPTIONS):
        response_texture = ihrl.graphics.newTexture(
            texts.text(
                response,
                ppd=ppd,
                intensity_background=ihrl.background,
                intensity_text=txt_ints[i],
                fontsize=FONTSIZE,
            )["img"],
            "square",
        )
        response_textures.append(response_texture)

    # align top of textures, such that tallest texture has 10px bottom clearance
    max_height = 0
    for texture in response_textures:
        if texture.hght > max_height:
            max_height = texture.hght
    vertical_position = ihrl.height - max_height - 10
    width = ihrl.width // len(RESPONSE_OPTIONS)

    # Draw
    for i, texture in enumerate(response_textures):
        horizontal_position = width * i + ((width - texture.wdth) // 2)
        texture.draw((horizontal_position, vertical_position))
```

Two layout details worth reusing:

**The labels are laid out by division, not by hard-coded coordinates.** The
screen width is divided into as many columns as there are options, and each
label is centred within its column. Adding a sixth option requires no other
change.

**The baseline is aligned across labels.** The tallest of the rendered text
images determines the vertical position of all of them, leaving 10 pixels of
clearance at the bottom. Text images differ in height depending on whether the
string has descenders, so aligning by the tallest keeps the row from looking
ragged.

Note also `selection - 1`: the selection runs from 1 to 5 while the list index
runs from 0 to 4.

```{important}
`draw_options` creates one new texture per option, on every redraw, and never
deletes them. A block of trials with several presses per trial will accumulate a
large number of textures. For a short template this is tolerable, but if you
build a long experiment on this code, either call `.delete()` on the textures at
the end of the trial, or build them once per trial and redraw the existing ones.
See [asymmetric matching](asymmetric-matching) for the deletion pattern.
```


## A trial

The stimulus and the scale are drawn into the same frame, and only then flipped:

```{code-block} python
def display_stim(ihrl, stim, response_selection):
    stimulus = stimuli.stims[stim]

    # Convert the stimulus image(matrix) to an OpenGL texture
    stim_texture = ihrl.graphics.newTexture(stimulus["img"])

    # Determine position: we want the stimulus in the center of the frame
    window_center = (ihrl.height // 2, ihrl.width // 2)  # Center of the drawing window
    pos = (
        window_center[1] - (stim_texture.wdth // 2),
        window_center[0] - (stim_texture.hght // 2),
    )

    # Create a display: draw texture on the frame buffer
    stim_texture.draw(pos=pos, sz=(stim_texture.wdth, stim_texture.hght))

    # Draw Likert-scale options
    draw_options(ihrl, response_selection)

    # Display: flip the frame buffer
    ihrl.graphics.flip(clr=True)  # also `clear` the frame buffer
```

and the trial is the familiar loop, starting from the middle of the scale:

```{code-block} python
def run_trial(ihrl, stim, **kwargs):
    response_position = 3

    # Run adjustment
    accept = False
    while not accept:
        display_stim(
            ihrl,
            stim,
            response_selection=response_position,
        )
        response_position, accept = select(ihrl, value=response_position, range=(1, 5))

    return {"response": response_position}
```

Unlike the matching templates, the starting position is *not* random: every
trial starts at option 3, the neutral midpoint. That is the right choice for a
rating scale, where a random start would bias the response towards wherever the
selection happened to begin, and where the number of presses is not itself
informative.

The recorded result is the integer position on the scale. What that integer
means lives in `RESPONSE_OPTIONS`, so keep the two together when you analyse the
data, and record the option list along with your results if you ever change it.


## The stimuli

`stimuli.py` differs from the other templates: instead of functions that
generate a stimulus per trial, it builds a dictionary of ready-made stimuli when
the module is imported.

```{code-block} python
# Initialize empty dict to hold all stims
stims = {}

...

stims["bullseye"] = stimupy.utils.stack_dicts(left, right, direction="horizontal")
```

The design is then simply the list of their names:

```{code-block} python
stim_names = stimuli.stims.keys()


def generate_block():
    # Combine all variables into full design
    trials = [(name) for name in stim_names]

    # Convert to dataframe
    block = pd.DataFrame(trials, columns=["stim"])

    # Shuffle trial order
    block = block.reindex(np.random.permutation(block.index))
    block.reset_index(drop=True, inplace=True)
    block.index.name = "trial"

    return block
```

One trial per stimulus, in random order, repeated `Nrepeats` times as separate
blocks. This suits a study that compares a fixed set of displays rather than
sampling a parameter, which is the usual reason to reach for a rating scale.


## Related

- [method of adjustment](../useful-examples/method-of-adjustment) for the
  select-and-accept interaction this is built on.
- [show stimuli](../useful-examples/show-stimuli) for the same `select` function
  in its simplest form.
- [managing data](../useful-examples/managing-data) for the design and results
  files.
