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


- Set the desired build path for the libraries in make.inc with the BUILDDIR
  variable, and the desired path for the python libraries with the PYDIR. By
  default the python libraries will be installed in /usr/local/lib for all users,
  but this requires sudo access to install.
- Run make at the base of the hrl directory with sudo access if required, and
  with a 'nodpx' argument if no datapixx is module is required
- If you modified PYDIR, add PYDIR to your PYTHONPATH. Otherwise the default
  path should allow python to detect the libraries automatically.
- Move misc/hrlrc to ~/.hrlrc and edit it to comply with your system.


### Usage ###


#### Finding Documentation ####

- Start IPython
- Import HRL: from hrl import *
- Create and hrl instance: hrl = HRL(...)
- Examine module documentation: hrl?
- Access HRL method documentation: hrl.method?
- Using IPython to interact with an hrl instance can be very helpful
  while designing an experiment.

#### Developing an Experiment ####

- A demonstration experiment is available under scripts/experiments/sacha and is a good reference for how
  to design an experiment with HRL. You may want to copy it as a
  starting point for your experiment.
- If you want to use gamma correction, generate lut.txt with the hrl.lut module
(see below), and pass it to an hrl instance with hrl = HRL(...,lut='LUT.txt')

#### Calibrating Hardware ####

- The directory scripts/calibration 

#### Building a Lookup Table ####

- 'from hrl import lut'
- Read the lookup table documentation with 'lut?' and follow them. The end
  result is a file 'lut.txt'.
