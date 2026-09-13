# Standalone tutorial scripts

Self-contained versions of the tutorials. They require only `HRL`, `numpy` and,
for the text displays, `Pillow`. `full_experiment/` additionally needs `pandas`. No stimulus-generation library and
no calibration file are needed, so they run as-is on a laptop.

These are the scripts narrated in the documentation:

| script | documentation page |
| ------ | ------------------ |
| `minimal_usage_example.py`  | Getting started, "Minimal example" |
| `show_stimuli.py`           | Useful examples, "Show stimuli"    |
| `text_displays_experiment.py` (with `text_displays.py`) | Useful examples, "Text displays" |
| `full_experiment/` | Useful examples, "Managing data" and "Structure of an experiment" |

The numbered tutorial folders next to this one (`0_basics/`, `1_show_stimuli/`,
`2_display_text/`, `4_managing_design_results/`) cover the same steps, but the way the lab actually runs them:
stimuli come from [stimupy](https://github.com/computational-psychology/stimupy),
text comes from `stimupy.components.texts`, and a `lut.csv` calibration file is
loaded. Read the standalone scripts first if you just want to see `HRL` work;
read the numbered folders when you start building a real experiment.

Both variants are kept on purpose. They are not copies of each other.

`full_experiment/` was originally written for the documentation and kept on the
unmerged `docs` branch. Run it from inside its `experiment/` folder:

```
cd full_experiment/experiment
python run_experiment.py
```

It asks for participant initials (press Enter for `DEMO`) and writes design and
results files to `full_experiment/data/`. Set `inlab = True` in
`run_experiment.py` to run it on the lab setup. `lut_viewpixx.csv` and
`lut_jvc.csv` show the LUT format; they are not calibrations of your display.
