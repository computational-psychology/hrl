# HRL examples

Example code for building psychophysical experiments with `HRL`.

## Tutorials

`tutorials/` walks step-by-step through the components needed to build an
experiment with `HRL`. If this is your first time using `HRL`, start with
`0_basics` and work upwards:

- `0_basics/` opens a window, draws a texture, reads a button press.
- `1_show_stimuli/` loads and displays a set of stimuli.
- `2_display_text/` renders text (instructions, feedback) as textures.
- `3_adjustment/` implements a method-of-adjustment response loop.
- `4_managing_design_results/` separates design from results, and makes an
  experiment interruptible and resumable.

Each folder contains a markdown file explaining the logic of that step.

## Experiment templates

`templates/` contains ready-to-use experiment templates, one per paradigm:

- `asymmetric_matching/` asymmetric matching with adjustment.
- `mutual_matching/` mutual matching between two patches.
- `mlds_experiment/` Maximum Likelihood Difference Scaling.
- `mlcm_experiment/` Maximum Likelihood Conjoint Measurement.
- `2IFC_experiment/` two-interval forced choice.
- `Likert_responses/` rating on a Likert scale.
- `eyetracking_example/` MLCM combined with an EyeLink eyetracker (advanced).

In each template, `run_experiment.py` is the entry point. To run one:

```
python run_experiment.py
```

and type `demo` as the observer name.

The templates are written to run in the lab, so they select a graphics device
based on the hostname and load a `lut.csv` calibration file. On a machine
without the lab hardware they fall back to the standard GPU backend.

## Provenance and license

The `tutorials/` and `templates/` code was developed over several years in the
`template_experiment` repository (Guillermo Aguilar and Joris Vincent) and was
migrated here so that the examples live alongside the library they use.

This code is distributed under the same license as the rest of `HRL`, the GNU
Library General Public License v2. See the `LICENSE` file at the root of this
repository.

## Note on the demo stimuli

The demo stimulus images under `templates/*/stimuli/` are stored as 8-bit
greyscale PNGs. The experiment code reads them with `Image.open(...).convert("L")`,
so this is exactly the data the experiments consume. The POV-Ray sources
(`.pov`) used to render the asymmetric matching stimuli are included alongside
them.
