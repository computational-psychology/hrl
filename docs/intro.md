# Welcome

HRL is a Python library for running psychophysical experiments. 

It is primarily a wrapper around OpenGL, pygame and a set of
hardware drivers, and it coordinates them in a purpose-built, user-friendly
way. 

Unlike other psychophysics libraries in Python, HRL is designed to be
*light-weight*, *minimalistic*, and *modular*. Its dependencies are few and
low-level, so your code is less likely to break in the future. That supports
the reproducibility of your experiments.

HRL was born out of the necessity to run experiments with devices that offer modes of
displaying high resolution luminance (Viewpixx devices), and hence its name, HRL. 
However, we have expanded the library to also run color experiments, and 
it can run in unspecialized hardware without the high-resolution ability.


Note that HRL requires you, the experimenter, to create your stimuli yourself
(as 2-D numpy arrays) and to process the data you acquire. How you do that is
up to you.

We do provide several utilities and experiment templates developed over the
years in our lab, which you can use as a starting point for your own experiment.


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
in the hardware we use (Viewpixx displays), the theory behind gamma correction and how
to apply it with HRL, and various other aspects of monitor calibration.


