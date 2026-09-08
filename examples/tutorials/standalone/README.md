# Standalone tutorial scripts

Self-contained versions of the first three tutorials. They require only `HRL`,
`numpy` and, for the text displays, `Pillow`. No stimulus-generation library and
no calibration file are needed, so they run as-is on a laptop.

These are the scripts narrated in the documentation:

| script | documentation page |
| ------ | ------------------ |
| `minimal_usage_example.py`  | Getting started, "Minimal example" |
| `show_stimuli.py`           | Useful examples, "Show stimuli"    |
| `text_displays_experiment.py` (with `text_displays.py`) | Useful examples, "Text displays" |

The numbered tutorial folders next to this one (`0_basics/`, `1_show_stimuli/`,
`2_display_text/`) cover the same steps, but the way the lab actually runs them:
stimuli come from [stimupy](https://github.com/computational-psychology/stimupy),
text comes from `stimupy.components.texts`, and a `lut.csv` calibration file is
loaded. Read the standalone scripts first if you just want to see `HRL` work;
read the numbered folders when you start building a real experiment.

Both variants are kept on purpose. They are not copies of each other.
