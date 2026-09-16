# HRL: High Resolution Luminance

[![Test](https://github.com/computational-psychology/hrl/actions/workflows/test.yml/badge.svg)](https://github.com/computational-psychology/hrl/actions/workflows/test.yml)
[![Docs](https://github.com/computational-psychology/hrl/actions/workflows/build-deploy-docs.yml/badge.svg)](https://computational-psychology.github.io/hrl/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://github.com/computational-psychology/hrl/blob/master/pyproject.toml)
[![License: LGPL v2](https://img.shields.io/badge/license-LGPL%20v2-blue)](LICENSE)

HRL is a light-weight Python library for running psychophysical experiments. It
displays images with precise, frame-synchronized timing and records the
participant's responses, on anything from a laptop to specialized vision
research hardware.

HRL was built to drive VPixx devices (DataPixx and ViewPixx) in their 16-bit
greyscale mode, which divides the luminance range into 65536 steps instead of the
256 of a standard display. That is where its name comes from. It has since grown
to support color presentation, and it runs on ordinary hardware without the
high-resolution mode. The same experiment code runs on your laptop and in the
lab: you only change the arguments that select the hardware.

**Documentation:** <https://computational-psychology.github.io/hrl/>


## Features

- **16-bit greyscale luminance** on DataPixx and ViewPixx devices, and 8-bit
  presentation on any standard graphics card.
- **Develop anywhere, run in the lab.** Graphics, input and calibration devices
  are selected by name when HRL starts, and hardware drivers are only imported
  when they are used.
- **Gamma correction** from measured LookUp Tables (LUTs), applied to every image
  you display.
- **Monitor calibration tools.** The `hrl-util` command line tool measures a
  display with a photometer and builds a linearized LUT from the measurements.
- **Responses and reaction times** from the keyboard or a ResponsePixx button box.
- **Few, low-level dependencies**: NumPy, pygame, PyOpenGL and Matplotlib. Fewer
  moving parts make experiments less likely to break in the future, which helps
  keep them reproducible.


## What HRL does not do

HRL is deliberately minimal. It does **not** generate stimuli: you create them
yourself, as NumPy arrays, with whatever tools you prefer. It does not analyze
your data. It is designed for experiments that can be broken down into a
sequence of static images; for complex, dynamic stimuli, other libraries are a
better fit.


## Installation

HRL requires Python 3.8 or newer, and is tested on Python 3.10 to 3.13.

HRL is not on PyPI yet. Install it from GitHub:

```bash
pip install https://github.com/computational-psychology/hrl/archive/master.zip
```

This also installs the required dependencies: `numpy`, `pygame`, `pyopengl` and
`matplotlib`.

### Hardware support

Everything beyond a standard display and keyboard is optional, and needs an
extra package only when you use it.

| Device | Selected with | Extra package |
| ------ | ------------- | ------------- |
| Standard graphics card, 8-bit greyscale | `graphics="gpu"` | none |
| DataPixx, 16-bit greyscale | `graphics="datapixx"` | `pypixxlib` |
| ViewPixx, 16-bit greyscale (M16 mode) | `graphics="viewpixx"` | `pypixxlib` |
| ViewPixx, color (C24 mode) | `graphics="viewpixx_color"` | `pypixxlib` |
| Keyboard | `inputs="keyboard"` | none |
| ResponsePixx button box | `inputs="responsepixx"` | a DataPixx or ViewPixx graphics device |
| Konica Minolta LS-100 photometer | `photometer="minolta"` | `pyserial` |
| CRS OptiCAL photometer | `photometer="optical"` | `pyoptical` |
| X-Rite i1Pro spectrophotometer | `photometer="i1pro"` | `pypixxlib` |

`pypixxlib` is the proprietary library from VPixx Technologies. It is not on PyPI:
download it from the
[VPixx website](https://docs.vpixx.com/python/introduction-to-vpixx-python-documentation)
and install the downloaded file with `pip`. `pyserial` is on PyPI
(`pip install pyserial`); `pyoptical` is not.

See the [installation guide](https://computational-psychology.github.io/hrl/getting-started/installation.html)
for details.


## Quick start

Show a random texture in the middle of an 800 by 600 window, wait for the
participant to press Left or Right, and report the reaction time:

```python
import numpy as np
from hrl import HRL

ihrl = HRL(graphics="gpu", inputs="keyboard", wdth=800, hght=600, bg=0.5)

# A stimulus is a NumPy array of intensities between 0.0 and 1.0
stimulus = np.random.uniform(low=0.0, high=1.0, size=(256, 256))

texture = ihrl.graphics.newTexture(stimulus)
texture.draw(pos=((800 - texture.wdth) // 2, (600 - texture.hght) // 2))
ihrl.graphics.flip(clr=True)  # make what was drawn visible

button, reaction_time = ihrl.inputs.readButton(btns=("Left", "Right"))
print(f"Pressed {button} after {reaction_time:.3f} s")

ihrl.close()
```

To run the same experiment in the lab, change only the arguments that select the
hardware, and point HRL at the monitor's calibration file:

```python
ihrl = HRL(graphics="viewpixx", inputs="responsepixx", lut="lut.csv",
           wdth=1920, hght=1080, scrn=1, fs=True, bg=0.5)
```

The [minimal example](https://computational-psychology.github.io/hrl/getting-started/minimal-usage-example.html)
walks through this code step by step.


## Monitor calibration

To present known luminances, the display has to be measured and linearized. HRL
does this with a photometer and the `hrl-util` command line tool, which is
installed with the package:

```bash
hrl-util lut measure     # display intensities, read the photometer  --> measure.csv
hrl-util lut smooth      # remove outliers, average, smooth         --> smooth.csv
hrl-util lut linearize   # sample equal luminance steps             --> lut.csv
hrl-util lut verify      # measure again with the LUT applied       --> lut_verification.csv
```

Pass the resulting `lut.csv` to HRL with `lut="lut.csv"`. The
[gamma correction guide](https://computational-psychology.github.io/hrl/calibration/gamma-correction-linearization.html)
explains each step and its options. Run `hrl-util --help` for a summary.


## Examples and experiment templates

The [`examples/`](examples/) folder contains:

- **tutorials** that build an experiment step by step: displaying stimuli, text,
  method of adjustment, and managing design and results files;
- **experiment templates**, complete runnable experiments for common paradigms:
  asymmetric and mutual matching, MLDS and MLCM scaling, two-interval forced
  choice, Likert ratings, and an MLCM experiment with an EyeLink eyetracker.

Each is narrated in the [documentation](https://computational-psychology.github.io/hrl/).


## Development

The project uses [uv](https://docs.astral.sh/uv/). To set up a development
environment with the test, documentation and linting tools:

```bash
git clone https://github.com/computational-psychology/hrl
cd hrl
uv sync --group dev
```

Run the tests that need no hardware, as continuous integration does:

```bash
uv run pytest tests/ -m "not graphics and not photometer"
```

Tests that need a display or lab hardware are marked `graphics`, `inputs`,
`interactive`, `pixx` or `photometer`, and are excluded by the command above.
Photometer tests accept `--photometer-dev=/dev/ttyUSBx`.

Lint and format the code, and build the documentation:

```bash
uv run ruff check . && uv run ruff format .
uv run jb build docs/
```

Bug reports and questions are welcome on the
[issue tracker](https://github.com/computational-psychology/hrl/issues).


## License

HRL is distributed under the GNU Library General Public License, version 2. See
[LICENSE](LICENSE).


## Authors

HRL is developed by Sacha Sokoloski, Guillermo Aguilar and Joris Vincent, and
maintained by Guillermo Aguilar.
