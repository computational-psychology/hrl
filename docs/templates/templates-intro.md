# Overview

In this section you find templates for various commonly used psychophysical
experiments.

Unlike the [useful examples](../useful-examples/useful-examples-intro), which
each demonstrate one component, these are **complete, runnable experiments**.
Each one generates its own design, runs blocks of trials, records results to
`.csv`, and can be interrupted and resumed. They are meant to be copied into a
new project folder and edited, not imported as a library.

They build on the components from the previous section, so read those first if
something in the code below is unfamiliar. In particular,
[managing data](../useful-examples/managing-data) explains the module layout and
the design/results machinery that every template here reuses without further
comment.


## The templates

| Paradigm | Folder | Page | Extra dependencies |
| -------- | ------ | ---- | ------------------ |
| Asymmetric matching, pre-rendered stimuli | `asymmetric_matching/` | [Asymmetric matching](asymmetric-matching) | `pandas`, `Pillow`, `stimupy` |
| Mutual matching, stimuli generated online | `mutual_matching/` | [Mutual matching](mutual-matching) | `pandas`, `Pillow`, `stimupy` |
| Difference scaling and conjoint measurement | `mlds_experiment/`, `mlcm_experiment/` | [MLDS/MLCM](MLDS-MLCM) | `pandas`, `stimupy` |
| Two-interval forced choice | `2IFC_experiment/` | [2-AFC/2-IFC](2-AFC-2-IFC) | `pandas`, `stimupy` |
| Rating on a Likert scale | `Likert_responses/` | [Likert scale](likert-responses) | `pandas`, `stimupy` |
| Conjoint measurement with an eyetracker | `eyetracking_example/` | [Eyetracking](eyetracking) | `pandas`, `Pillow`, `pylink` |

All of them live under
[`examples/templates/`](https://github.com/computational-psychology/hrl/tree/master/examples/templates)
in this repository.

None of these dependencies are required by `HRL` itself. `HRL` deliberately does
not generate stimuli, so the templates bring their own means of doing so:
[stimupy](https://github.com/computational-psychology/stimupy) for stimuli
generated in code, [Pillow](https://pillow.readthedocs.io/en/stable/) for text
and for loading pre-rendered images, and
[pandas](https://pandas.pydata.org/) for the design and results tables.

```
pip install pandas Pillow stimupy
```


## Running a template

The entry point is always `run_experiment.py`, and it must be run from inside
the `experiment/` folder, because `data_management.py` places the `data/`
directory next to it:

```
cd examples/templates/mlcm_experiment/experiment
python run_experiment.py
```

The first thing it does is ask for the participant initials. Press Enter to
accept the default, `DEMO`, and run through the template without creating data
for a real observer:

```
Please enter participant initials (ex.: DEMO):
```

The default matters for `asymmetric_matching/`, whose demo stimuli are stored
under `stimuli/DEMO/`: with any other name, the template will look for images
that are not there.


## The shared module layout

Every template is built from the same set of modules. They are deliberately
duplicated in each folder rather than factored into a shared package: a template
is meant to be copied whole and then edited, and a shared package would mean
that editing one experiment silently changes another.

| Module | Responsibility |
| ------ | -------------- |
| `run_experiment.py` | Entry point. Chooses the hardware setup, sequences blocks, runs the trial loop, saves each trial. |
| `design.py` | What the experiment tests. Defines the variables and combines them into blocks of trials. |
| `experiment_logic.py` | What happens in one trial. Displays, waits for a response, returns the result. |
| `data_management.py` | Where things go. Participant, session, filepaths, saving, and finding incomplete trials. |
| `stimuli.py` | Generates or loads the stimulus images. |
| `text_displays.py` | Instructions, break screens and other text. |

When adapting a template, you will mostly be editing `design.py` and
`experiment_logic.py`. `data_management.py` is usually left alone.

Two templates deviate from this. `asymmetric_matching/` adds `adjustment.py`,
`asymmetric_matching.py` and `variegate.py` for the matching field, and
`eyetracking_example/` is a single script, since it predates this layout.


## Selecting the hardware setup

Every `run_experiment.py` opens with the same idiom: a `SETUP` dictionary chosen
by hostname, which is then splatted into the `HRL` constructor.

```{code-block} python
from socket import gethostname

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
```

and then, at the bottom of the file:

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

This is the pattern to copy. Everything that differs between the laptop you
write the experiment on and the machine you run it on is collected in one
dictionary at the top of one file. The rest of the experiment never mentions
hardware. See [deploying your code in the lab](../getting-started/deploying-in-lab)
for what each of these parameters does.

The two lab entries also select a calibration file. The `lut.csv` shipped in
each template folder is an example, not a valid calibration of your monitor:
replace it with the most recent measurement from the machine you are running on.
See [gamma correction](../calibration/gamma-correction-linearization) for how
those files are produced.

```{note}
The background intensities differ per setup on purpose. `bg` is an intensity in
`[0.0, 1.0]`, and the same intensity is a different luminance on a different
monitor. The comments record what the lab actually wants, roughly
50 $cdm^{-2}$ on both.
```


## Checking stimuli before you run

Stimuli look different on a calibrated high-luminance monitor than on a laptop.
Before running participants it is worth putting the actual images on the actual
screen.
[`examples/templates/show_maxmin.py`](https://github.com/computational-psychology/hrl/blob/master/examples/templates/show_maxmin.py)
displays a folder of stimulus images one at a time on the experimental monitor,
labeled with their minimum and maximum values, so you can check size, position
and whether anything clips. The
[show stimuli](../useful-examples/show-stimuli) example is the same idea for
stimuli you generate in code, and `asymmetric_matching/experiment/show_stimuli.py`
is a version specific to that template.
