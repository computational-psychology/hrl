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

`tutorials/standalone/` holds self-contained versions of the first three steps
that need only `HRL`, `numpy` and `Pillow`. Those are the scripts narrated in
the "Getting started" and "Useful examples" pages of the documentation. The
numbered folders above are the lab-realistic counterparts: they use `stimupy`
for stimuli and text, and load a `lut.csv`. See
`tutorials/standalone/README.md`.

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

and press Enter when asked for the observer initials, to accept the default
`DEMO`. The `asymmetric_matching/` template ships its demo stimuli under
`stimuli/DEMO/`, so that name in particular has to match.

The templates are written to run in the lab, so they select a graphics device
based on the hostname and load a `lut.csv` calibration file. On a machine
without the lab hardware they fall back to the standard GPU backend.

## Utilities and older examples

Besides the two trees above, `examples/` holds a few standalone scripts that
predate the migration:

- `check_monitor_rate/` measures the refresh rate of the experimental monitor,
  in software (`check_monitor_rate.py`) or with a photodiode
  (`check_monitor_rate_photodiode.py`). Narrated in the "Refresh rate"
  documentation page.
- `luminance_to_intensity.py` converts a desired luminance in candela per
  square metre into the input intensity to put in a stimulus array, using a
  measured `lut.csv`.
- `templates/show_maxmin.py` displays a folder of stimulus images on the
  experimental monitor, with their minimum and maximum luminance, so that they
  can be checked before an experiment is run.
- `minimal_example_mouse.py` reads the mouse instead of the keyboard.
- `template_experiment_stimuli.py` is unrelated to `templates/` despite its
  name: it is a standalone script using the external `stimuli` package.
- `sacha/` and `lut.csv` are older lab material, kept for reference.

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
