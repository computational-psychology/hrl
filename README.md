## HRL: High Resolution Luminance ##


### Introduction ###


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
DATAPixx digital to analogue converter. With an appropriate analogue monitor,
a DATAPixx box can convert digital signals into 16 bit luminance values.
Datapixx also includes functionality for high precision temporal control.

Another component of HRL is that it is designed to work with certain luminance
measurement devices. HRL comes with a suite of calibration scripts designed to
help tune scientific hardware using these measurement devices.

Our lab also makes use of the EyeLink 1000 Desktop Mount in parallel with HRL.
We currently have alpha scripts implementing our desired scenarios, and we will
publish them when they have been thoroughly tested.


### Installation ###


HRL uses distutils for installation. First clone the repository via
'git clone https://github.com/TUBvision/hrl.git'. Then run 'sudo python setup.py install' at the root
of the repository. Note that HRL is currently python 2 compatible only.
  

##### Dependencies #####

- Required: pygame, pyopengl
- Optional: pydatapixx, pyoptical, pyserial


### Usage ###


Installing HRL installs both the libraries for developing experiments, as well as scripts
for running calibrations, tests, and other features. The libraries are installed under the
base module 'hrl'. The scripts can be accessed by running 'hrl-util' at the command line.

##### Documentation #####

- HRL docstrings can be accessed via pydoc. Running 'pydoc hrl' will display an
  introductory help file which in turn will explain where exactly to find the rest of the
  documentation.
- Running 'hrl-util' at the command line without any arguments will display another
  introductory help file, overviewing the various scripts that can be run via hrl-util.
- A heavily documented example experiment is available under examples/sacha. Beginning
  with a copy of examples/sacha is recommended for first time users who wish to code a new
  experiment.

##### Calibration #####

- HRL comes with scripts for developing a gamma correction Lookup Table (LUT) as well as
  various tests for calibrating the scientific hardware. Currently these are deprecated
  and will be updated soon.

