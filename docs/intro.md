# Welcome to the HRL documentation

This is the documentation of the package HRL. 
HRL is a library for running high resolution luminance experiments for 
psychophysics in Python. It is primarily a wrapper for a number of 
python libraries (e.g. OpenGL, pygame) and hardware drivers, and serves to 
coordinate them in a purpose built, user friendly way.

As opposed to other python libraries in psychophysics, HRL is designed 
to be light-weight, minimalistic, and modular. 
Its dependencies are minimal, so that it is less likely that your experiment
code breaks in the future. 
Importantly, HRL requires that you, the experimenter, create your 
stimuli yourself (the input to HRL are numpy arrays).


This documentation covers how to install HRL in your system and how to 
create a simple psychophysical experiment. 
It also reviews the theoretical basis of monitor calibration 
(and why it is senseful to do it) and how this is implemented in HRL.


**Table of contents**

```{tableofcontents}
```
