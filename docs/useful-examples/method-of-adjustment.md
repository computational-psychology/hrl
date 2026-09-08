# Method of adjustment

In a *method of adjustment* task the participant is in control of the stimulus.
Instead of choosing between alternatives that the experimenter has fixed
beforehand, the participant changes some value of the stimulus (typically the
intensity of a target patch) step by step, until it satisfies a criterion, and
then accepts it. The accepted value is the measurement.

This differs from the forced-choice task in the
[minimal example](../getting-started/minimal-usage-example) in one important
way: a single trial now involves *many* button presses and *many* displays, but
produces only *one* result. Every press that is not an accept leads to a new
stimulus being drawn, not to a new trial.

Adjustment is the building block behind the matching templates
([asymmetric matching](../templates/asymmetric-matching) and
[mutual matching](../templates/mutual-matching)), so it is worth understanding
on its own.

The full example is at
[`examples/tutorials/3_adjustment/`](https://github.com/computational-psychology/hrl/tree/master/examples/tutorials/3_adjustment).
It consists of `experiment.py` (the experiment itself), `adjustment.py` (the
adjustment logic), `stimuli.py` (the stimulus) and `text_displays.py`
(instructions and messages).


## Overview

```{mermaid}
graph LR;
    setup --> define --> start
    start --> display --> capture --> adjust --> display
    capture --> accept --> exit

    subgraph HRL
        display
        capture[capture participant response]
    end

    subgraph adjustment.py
        adjust[adjust stimulus value]
    end

    subgraph text_displays.py
        texturize[text to texture]
    end

    subgraph stimuli.py
        define[define stimuli]
    end

    subgraph experiment.py
        setup

        start
        accept

        exit[cleanup & exit]
    end
```

Note the loop in the middle: display, capture, adjust, display again. The trial
only ends when `capture` returns an accept.


## Install requirements

Besides `HRL`, this example uses
[stimupy](https://github.com/computational-psychology/stimupy) to generate the
stimulus, and [Pillow (PIL)](https://pillow.readthedocs.io/en/stable/) to draw
the text:

```
pip install stimupy Pillow
```


## The `adjust` function

All of the adjustment logic lives in one short function in `adjustment.py`.
It waits for a single button press, changes the value accordingly, and reports
back whether the participant accepted.

```{code-block} python
def adjust(ihrl, value, step_size=(0.05, 0.01)):
    """Allow participant to adjust (stimulus)value

    Parameters
    ----------
    ihrl : hrl-object
        hrl-interface object to use for display
    value : float
        value to adjust, e.g., target intensity
    step_size : tuple, optional
        step sizes of adjustment, big (Up/Down) and small (Left/Right),
        by default (0.05, 0.01)

    Returns
    -------
    float
        value after adjustment
    bool
        flag for whether value has been accepted
    """

    # Wait for key
    key, _ = ihrl.inputs.readButton(btns=("Escape", "Up", "Down", "Left", "Right", "Space"))

    # Process
    accept = False
    if key == "Escape":
        sys.exit("Participant terminated experiment")
    elif key == "Space":
        accept = True
    elif key == "Up":
        value += step_size[0]
    elif key == "Right":
        value += step_size[1]
    elif key == "Down":
        value -= step_size[0]
    elif key == "Left":
        value -= step_size[1]

    # Stay in gamut
    if value > 1:
        value = min(1, value)
        warning_max(ihrl)
    if value < 0:
        value = max(0, value)
        warning_min(ihrl)

    return value, accept
```

Three things are worth pointing out.

**Two step sizes.** Up and Down change the value by the *big* step, Left and
Right by the *small* step. This gives the participant a coarse and a fine
control without needing more than four keys. The defaults here are `0.05` and
`0.01`; the matching templates use much smaller ones, `(0.02, 0.002)`, because
they are matching to a fixed reference and need the extra precision.

**Accept is a button, not a state.** The function returns a tuple of the
(possibly changed) value and a boolean. It does not know or care how many times
it has been called before. Keeping it stateless like this is what makes it
reusable across the templates.

```{note}
The buttons accepted during adjustment are Up, Down, Left, Right, Space and
Escape. Space accepts the current value; Escape terminates the experiment by
raising `SystemExit`, which the main loop catches in order to close `HRL`
cleanly.
```

**Values stay in gamut.** The value being adjusted is an intensity, so it must
stay inside `[0.0, 1.0]`. If the participant tries to go past either end, the
value is clamped and a message is shown. Without this the intensity would keep
increasing invisibly, and the participant would press Down many times before
seeing anything change again.


## Gamut warnings

`warning_min` and `warning_max` are two small functions that clear the screen,
display a message, and wait. They accept a `lang` argument so the same
experiment can be run with English or German instructions, which matters when
testing participants who are not comfortable in English:

```{code-block} python
def warning_max(ihrl, lang="en"):
    ihrl.graphics.flip(clr=True)

    if lang == "de":
        lines = [...]      # German text
    elif lang == "en":
        lines = [
            "Reached maximum!",
            " ",
            "To continue, decrease, or press the middle button.",
        ]
    else:
        raise NotImplementedError(f'Language "{lang}" not available')

    display_text(ihrl, lines)
    ihrl.inputs.readButton(btns=("Down", "Left", "Space"))
```

The final `readButton` only accepts the buttons that make sense at the maximum:
decrease with Down or Left, or accept with Space. Pressing Up again does
nothing, so the participant cannot get stuck in a loop of warnings.

Displaying the message uses `display_text` from the
[text displays](text-displays) example.


## The adjustment loop

With `adjust` in place, a trial in `experiment.py` is a short `while` loop. Note
that the stimulus is redrawn on every pass, with the current value:

```{code-block} python
def experiment_main(ihrl):
    # Display instructions
    display_instructions(ihrl)
    ihrl.inputs.readButton(btns="Space")

    while True:
        # Main loop
        try:
            # Random starting value
            intensity_target = rng.random()

            # Run adjustment
            accept = False
            while not accept:
                display_stim(ihrl, intensity_target=intensity_target)
                intensity_target, accept = adjust(ihrl, value=intensity_target)

            # Show accept response screen
            display_accept(ihrl, intensity_target=intensity_target)
            ihrl.inputs.readButton(btns="Space")

        except SystemExit as e:
            # Cleanup
            print("Exiting...")
            ihrl.close()
            raise e
```

The starting value is drawn at random on every trial. This is deliberate: if
adjustment always started from the same value, the participant could learn how
many presses it takes to get to their answer, and the number of presses rather
than the appearance of the stimulus would determine the result.

`display_stim` is the usual `HRL` sequence, wrapped in a function so that the
loop above stays readable. The stimulus is a White's illusion display generated
by `stimupy`, whose target intensity is the value being adjusted:

```{code-block} python
def display_stim(ihrl, intensity_target=0.5):
    stim = whites(intensity_target=intensity_target)

    # Convert the stimulus image(matrix) to an OpenGL texture
    stim_texture = ihrl.graphics.newTexture(stim["img"])

    # Determine position: we want the stimulus in the center of the frame
    pos = (CENTER[1] - (stim_texture.wdth // 2), CENTER[0] - (stim_texture.hght // 2))

    # Create a display: draw texture on the frame buffer
    stim_texture.draw(pos=pos, sz=(stim_texture.wdth, stim_texture.hght))

    # Display: flip the frame buffer
    ihrl.graphics.flip(clr=True)  # also `clear` the frame buffer
```

```{important}
Regenerating and re-uploading the texture on every button press is fine for a
stimulus of this size, but it is work done between the press and the new
display. If your stimulus is expensive to generate, generate the variants ahead
of the trial and only call `newTexture` and `draw` inside the loop.
```


## Where to go next

- [managing data](managing-data) shows how to record the accepted values, one
  row per trial, and how to lay out design and results files.
- [asymmetric matching](../templates/asymmetric-matching) and
  [mutual matching](../templates/mutual-matching) are complete experiments
  built around this `adjust` function.
