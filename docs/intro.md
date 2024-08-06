# Welcome

This is the documentation of the package HRL. 
HRL is a library for running high resolution luminance experiments for 
psychophysics in Python. It is primarily a wrapper for a number of 
python libraries (e.g. OpenGL, pygame) and hardware drivers, and serves to 
coordinate them in a purpose built, user friendly way.

As opposed to other python libraries in psychophysics, HRL is designed 
to be *light-weight*, *minimalistic*, and *modular*. 
Because its dependencies are minimal and low-level, with HRL it is less likely that 
your code breaks in the future (supporting future reproducibility).

Importantly, HRL requires that you, the experimenter, create your 
stimuli yourself (as 2-D numpy arrays) and process the data
you acquire. It's up to you how you do that; however, we do provide
several utilities and templates that we have developed 
over the years in our lab. These you can use as a starting point.


This documentation is organized as follows:

- **Getting started with HRL** covers how to install HRL in your system and how to 
create a simple psychophysical experiment. This section covers the 
core functionality of HRL and from here you can (if you wish) 
develop you own python code for your experiment.

- **Useful examples** shows various utilities: how to 
 show stimuli for inspection (before an experiment), how to show text 
 (for instructions) and how to manage experimental design files and 
 acquired data
 
- **Experiment templates** showcases experimental paradigms
frequently used in psychophysics. You can use these templates as a starting
point in building your own experiment.

- **Monitor calibration** explains how high resolution luminance is achieved
in the hardware we use (Vpixx), the theory behind gamma correction and how 
to use HRL to do so, and various other aspects of monitor calibration.


