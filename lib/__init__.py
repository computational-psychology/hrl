"""
This is the base of the HRL program structure. In order to use HRL, most users
will simply wish to use 'from hrl import HRL' to loaded the HRL class which
incorporates the functionality of all the various submodules.

Documentation about the various parts of HRL can be accessed via the following
commands:

pydoc hrl - This file
pydoc hrl.hrl - HRL class help
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
