# Welcome

HRL is a Python library for running high-resolution luminance experiments in
psychophysics. It is primarily a wrapper around OpenGL, pygame and a set of
hardware drivers, and it coordinates them in a purpose-built, user-friendly
way.

Unlike other psychophysics libraries in Python, HRL is designed to be
*light-weight*, *minimalistic*, and *modular*. Its dependencies are few and
low-level, so your code is less likely to break in the future. That supports
the reproducibility of your experiments.

Note that HRL requires you, the experimenter, to create your stimuli yourself
(as 2-D numpy arrays) and to process the data you acquire. How you do that is
up to you. We do provide several utilities and templates developed over the
years in our lab, which you can use as a starting point.


This documentation is organized as follows:

- **Getting started with HRL** explains how to install HRL on your system and
how to create a simple psychophysical experiment. This section covers the
core functionality of HRL. From there you can, if you wish, develop your own
python code for your experiment.

- **Useful examples** shows various utilities: how to show stimuli for
 inspection before an experiment, how to show text for instructions, and how
 to manage experimental design files and acquired data.
 
- **Experiment templates** showcases experimental paradigms
frequently used in psychophysics. You can use these templates as a starting
point in building your own experiment.

- **Monitor calibration** explains how high-resolution luminance is achieved
in the hardware we use (Vpixx), the theory behind gamma correction and how
to apply it with HRL, and various other aspects of monitor calibration.


