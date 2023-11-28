# **HRL**: **H**igh **R**esolution **L**uminance #

(Python 3 version)

HRL is a library for running high resolution luminance experiments for
psychophysics in Python. It is primarily a wrapper for a number of python
libraries and hardware drivers, and serves to coordinate them in a purpose
built, user friendly way.

HRL's core purpose is the presentation of static, greyscale images and
the recording of subject responses with a high degree of temporal precision. If
your experiment can be reduced broadly to this scenario, HRL could be the
library for you.

HRL does not provide tools for generating stimuli, nor is it designed to deal
with colour in any way. HRL is not designed to handle complex, dynamic stimuli, and
if a stimulus cannot be easily broken down into a series of static images, HRL
may be ill suited to the task. If any of these capabilites are essential, than
other libraries may be called for.

HRL is designed to work with a number of optional hardware components. The
inclusion of these hardware components is handled in a modular fashion, and HRL
is designed so that experiments could be written on a home computer, and then
transfered to a lab computer with scientific hardware as required.

The most important component to achieving HRL's full functionality is a
DATAPixx device or ViewPixx device. The first version of HRL was designed to 
work with an CRT analogue monitor, so that the DATAPixx box could use the full
16-bit resolution by converting digital signals into 16 bit luminance values.
In the current version we have also adapted HRL to work with the newest ViewPixx 
LCD monitor, which also allows achromatic 16-bit luminance presentation.
ViewPixx and Datapixx also includes functionality for high precision temporal control.

Another component of HRL is that it is designed to work with certain luminance
measurement devices. HRL comes with a suite of calibration scripts designed to
help tune scientific hardware using these measurement devices.


## Installation ##

HRL is a full Python 3 package, and can be installed using pip or conda.
It is not (yet) on PyPI, so first clone the repository via

```
git clone https://github.com/computational-psychology/hrl
```

Then install (from the root of the repository) using

```
pip install .
```

or

```
pip install -e .
```

for an editable installation.

### Dependencies ###

- Required: `pygame`, `pyopengl`, `numpy`
- Optional: `pyoptical`, `pyserial`, and `pypixxlib`, [the propertary library from VPixx Technologies](https://www.vpixx.com/manuals/python/html/index.html).

```pip install .``` will automatically install the *required* dependencies.


## Usage ##

Installing HRL installs both the libraries for developing experiments, as well as a CLI utility for running calibrations, tests, and other features. The libraries are installed under the
base Python module `hrl`. The scripts can be accessed by running `hrl-util` at the command line.

### Documentation ###

- HRL docstrings can be accessed via `pydoc`. Running `pydoc hrl` will display an
  introductory help file which in turn will explain where exactly to find the rest of the
  documentation.
- Running `hrl-util` at the command line without any arguments will display another
  introductory help file, overviewing the various scripts that can be run via `hrl-util`.
- Example experiments using HRL can be found in the [templates repository](https://github.com/computational-psychology/template_experiment). This is a good place to start for beginners using HRL.
- A heavily documented example experiment is available under examples/sacha.

### Calibration ###

HRL comes with a CLI utility `hrl-util` for developing a gamma correction Lookup Table (LUT)
as well as various tests for calibrating the scientific hardware:

```
hrl-util --help
```
