"""
This is the root of the HRL module hierarchy. In order to use HRL, most users
will simply need to include 'from hrl import HRL' amongst their imports and
instantiate the HRL class. The HRL class wraps all the functionality provided by
the HRL librariers. 

Nevertheless, in order to understand how to use the various components of HRL,
it is best to consult the documentation of the submodules in the hierarchy.
Documentation about the various parts of HRL can be accessed via the following
commands:

pydoc hrl - This file
pydoc hrl.hrl - Help for the general HRL class
pydoc hrl.graphics.graphics - Help for graphics devices in general
pydoc hrl.graphics.gpu - Help for using a normal video card for display
pydoc hrl.graphics.datapixx - Help for using the DATAPixx DAC
pydoc hrl.inputs.inputs - Help for input devices in general
pydoc hrl.inputs.keyboard - Help for using a normal PC keyboard as input
pydoc hrl.inputs.responsepixx - Help for using a RESPONSEPixx device as input
pydoc hrl.photometer.photometer - Help for photometers in general
pydoc hrl.photometer.optical - Help for using an OptiCAL device
"""
from hrl import HRL
