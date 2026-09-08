# Mutual matching

**Mutual matching** is a variant of [asymmetric matching](asymmetric-matching)
in which the two patches being compared are part of the same stimulus. One is
the target, at an intensity fixed by the design; the other is the match, whose
intensity the participant adjusts. Which side is which alternates from trial to
trial, so across the experiment each side is matched to the other, and neither
side is permanently the reference.

The full example is at
[`examples/templates/mutual_matching/`](https://github.com/computational-psychology/hrl/tree/master/examples/templates/mutual_matching).

Structurally it is the same experiment as the asymmetric matching template. The
difference is where the stimulus comes from: here it is generated **online**, in
code, on every button press, using
[stimupy](https://github.com/computational-psychology/stimupy). There are no
image files, no `stimuli/` folder and no rendering step. If your stimuli can be
described in code, this is the simpler of the two templates to adapt.


## Overview

```{mermaid}
graph LR;
    setup --> next_block --> run_block
    next_block <--> incomplete_blocks <--> incomplete_trials
    next_block <--> generate_design

    run_block <--> run_trial
    run_trial <--> define
    run_trial --> display --> capture --> adjust --> run_trial
    run_trial --> save_trial
    run_block --> exit

    generate_design <--> generate_block

    subgraph data_management.py
        incomplete_blocks
        incomplete_trials

        next_block

        save_trial
    end

    subgraph design.py
        generate_design
        generate_block
    end


    subgraph HRL
        display
        capture[capture participant response]
    end

    subgraph stimuli.py
        define[generate stimulus]
    end

    subgraph experiment_logic.py
        run_trial
    end

    subgraph adjustment.py
        adjust[adjust matching field value]
    end

    subgraph run_experiment.py
        setup

        run_block

        exit[cleanup & exit]
    end

```

Compare with the diagram on the [asymmetric matching](asymmetric-matching) page:
the only branch that disappears is the separate matching field. Here `define`
produces the whole display in one call.


## Install requirements

```
pip install pandas Pillow stimupy
```


## The design

Two variables are crossed: the intensity of the target, and which side of the
stimulus the target is on.

```{code-block} python
LUMINANCES = (0.25, 0.5, 0.75)
SIDES = ("Left", "Right")
STIM_NAMES = stimuli.__all__


def generate_block(stim_name):
    # Combine all variables into full design
    trials = [(stim_name, int_target, side) for int_target in LUMINANCES for side in SIDES]

    # Convert to dataframe
    block = pd.DataFrame(
        trials,
        columns=["stim", "intensity_target", "target_side"],
    )

    # Shuffle trial order
    block = block.reindex(np.random.permutation(block.index))
    block.reset_index(drop=True, inplace=True)
    block.index.name = "trial"

    return block
```

Because nothing is loaded from disk, the trial order *can* be shuffled here, and
it is. That is the practical advantage of generating stimuli online.

Crossing the target intensity with the side is what makes the matching mutual.
Over a block, each intensity is presented once on the left with the right side
adjustable, and once on the right with the left side adjustable.


## The stimulus

`stimuli.py` produces a White's illusion display in which both targets are
visible and their intensities are set independently:

```{code-block} python
def whites(intensity_target, target_side, intensity_match):
    if target_side == "Left":
        intensities = (intensity_target, intensity_match)
    elif target_side == "Right":
        intensities = (intensity_match, intensity_target)

    return stimupy.stimuli.whites.white(
        **resolution,
        bar_width=target_size,
        target_indices=(3, -2),
        target_heights=target_size,
        intensity_bars=(0.0, 1.0),
        intensity_target=intensities
    )
```

`target_indices=(3, -2)` selects the third bar from the left and the second from
the right as targets, which places them on bars of opposite polarity. The
`target_side` from the design decides which of those two gets the fixed target
intensity and which gets the value being adjusted, by ordering the tuple.


## A trial

`run_trial` is short, because all the work is in the two functions it calls:

```{code-block} python
rng = np.random.default_rng()


def run_trial(ihrl, intensity_target, target_side, **kwargs):
    # Pick random starting intensity for matching field
    intensity_match = rng.random()

    # Run adjustment
    accept = False
    while not accept:
        display_stim(
            ihrl,
            intensity_target=intensity_target,
            target_side=target_side,
            intensity_match=intensity_match,
        )
        intensity_match, accept = adjust(ihrl, value=intensity_match)

    return {"intensity_match": intensity_match}
```

This is exactly the loop from the
[method of adjustment](../useful-examples/method-of-adjustment) example, with
the design variables threaded through. The starting intensity is random on every
trial, for the same reason as there: so that the number of presses does not
become the answer.

`display_stim` regenerates the whole stimulus and uploads a new texture on every
pass of the loop:

```{code-block} python
def display_stim(ihrl, intensity_target, target_side, intensity_match):
    stimulus = stimuli.whites(
        intensity_target=intensity_target, target_side=target_side, intensity_match=intensity_match
    )

    # Convert the stimulus image(matrix) to an OpenGL texture
    stim_texture = ihrl.graphics.newTexture(stimulus["img"])

    # Determine position: we want the stimulus in the center of the frame
    center = (ihrl.height // 2, ihrl.width // 2)
    pos = (center[1] - (stim_texture.wdth // 2), center[0] - (stim_texture.hght // 2))

    # Create a display: draw texture on the frame buffer
    stim_texture.draw(pos=pos, sz=(stim_texture.wdth, stim_texture.hght))

    # Display: flip the frame buffer
    ihrl.graphics.flip(clr=True)  # also `clear` the frame buffer
```

```{important}
Regenerating the stimulus on every press is the simplest thing that works, and
for a 10 by 20 degree display at 32 pixels per degree it is fast enough. It is
also the part of this template most likely to become a problem if you scale it
up: a larger display, a more expensive stimulus, or a finer step size all mean
more work between the press and the new frame. If adjustment starts to feel
sluggish, precompute the stimulus for the possible values before the trial and
only call `newTexture` and `draw` in the loop, as
[asymmetric matching](asymmetric-matching) does for its scene.
```

Note also that `display_stim` takes the window centre from `ihrl.height` and
`ihrl.width` rather than from a module constant. The stimulus is therefore
centred correctly whichever of the setups in `run_experiment.py` was selected,
without the geometry being repeated per setup.


## Related

- [asymmetric matching](asymmetric-matching) for the pre-rendered variant, and
  for the texture management that matters when stimuli are expensive.
- [method of adjustment](../useful-examples/method-of-adjustment) for the
  `adjust` function.
- [managing data](../useful-examples/managing-data) for the design and results
  files.
