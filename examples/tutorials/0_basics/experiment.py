import numpy as np
from hrl import HRL

# ------------------------------------- #
#              0. SETUP                 #
# ------------------------------------- #
# Define window parameters
SHAPE = (1024, 1024)  # Desired shape of the drawing window
CENTER = (SHAPE[0] // 2, SHAPE[1] // 2)  # Center of the drawing window

# Create HRL interface object
ihrl = HRL(
    graphics="gpu",  # Use the default GPU as graphics device driver
    # graphics='datapixx',    # In the lab, we use the datapixx device driver
    lut="lut.csv",  # filepath to (color) LookUp Table, mapping input intensity (0.0,1.0) to monitor intensities
    inputs="keyboard",  # Use the keyboard as input device driver
    # inputs="responsepixx",  # In the lab, we use the responsepixx input device
    hght=SHAPE[0],
    wdth=SHAPE[1],
    scrn=1,  # Which screen (monitor) to use
    fs=False,  # Fullscreen?
    bg=0.5,  # background intensity (black=0.0; white=1.0)
)


# ------------------------------------- #
#          1. DEFINE STIMULUS           #
# ------------------------------------- #
"""
In order to display a stimulus,
we first have to define/load/create a stimulus.
There are many ways to do so,
e.g., load an image from a file.
Here, create an image-matrix (np.ndarray) with 256x256 random values
"""
rng = np.random.default_rng()
stim_image = rng.standard_normal(size=(256, 256))


# ------------------------------------- #
#               2. DISPLAY              #
# ------------------------------------- #
"""
To display on the screen HRL uses frame buffers.
We can draw OpenGL primitives and textures on a frame buffer
and then when we want to display that on the screen,
we "flip" the buffer.

First, we convert our stimulus to an OpenGL texture,
then we place that on the frame buffer,
and then we flip the buffer
"""

# Convert the stimulus image(matrix) to an OpenGL texture
stim_texture = ihrl.graphics.newTexture(stim_image)

# Determine position: we want the stimulus in the center of the frame
pos = (CENTER[1] - (stim_texture.wdth // 2), CENTER[0] - (stim_texture.hght // 2))

# Create a display: draw texture on the frame buffer
stim_texture.draw(pos=pos, sz=(stim_texture.wdth, stim_texture.hght))

# Display: flip the frame buffer
ihrl.graphics.flip(clr=True)  # also `clear` the frame buffer

"""
The stimulus display will then stay on the screen
until either another `.flip()` is called,
or the hrl-object is `.close()`'d
"""


# ------------------------------------- #
#    3. CAPTURE PARTICIPANT RESPONSE    #
# ------------------------------------- #
"""
After displaying some stimulus, we often want some response from the participant.
This generally requires two steps:
- capturing the response via some input hardware (e.g., keyboard, button box)
- "processing" the response, i.e., deciding what to do with it
  (determine next stimulus, record to disk, etc.)

HRL also provides functionality to interact with input hardware.
The high-level interface is `<hrl_object>.inputs.readButton()`,
which waits for a (single) button press.

By default, `readButton` waits until one of the following buttons is pressed:
"Up", "Down", "Right", "Left", "Space", "Escape"
"""
ihrl.inputs.readButton()
print("Participant pressed a button")

"""
`readButton`can also be asked to respond to only some buttons
and ignore all others:
"""
ihrl.inputs.readButton(btns=("Right", "Space", "Left", "Escape"))
print("Participant pressed a button")

"""
`readButton` also returns a tuple
of a string-descriptor of the button pressed,
and the response delay (i.e., time until button was pressed).
"""
button, t1 = ihrl.inputs.readButton()
print(f"Participant pressed {button} after {t1}s")


# ------------------------------------- #
#         4. "PROCESS" RESPONSE         #
# ------------------------------------- #
"""
Having captured a response, we need to process it.
This can include all kinds of steps, for instance
deciding if the response is "correct" or not (in tasks where this is possible);
storing the response (and additional information) as results data;
deciding what the next trial & stimulus will be.
"""

# Assign responses to correct/incorreect
response_correct = {"Right": True, "Left": False, "Escape": False}

if response_correct[button]:
    print(f"Participant pressed {button}, which is correct")
else:
    print(f"Participant pressed {button}, which is incorrect")


"""
How exactly the response is mapped to some action
depends heavily on the experiment and task.
For example, in a Method of Forced Choice experiment,
the response is converted to correct/incorrect,
recorded as a result, and a new trial is presented.

In a Method of Adjustment task
the response leads to increasing/decreasing some stimulus level.
In these experiments, a button press will lead to a new _stimulus display_,
but not immediately to recording a new result.
Only when some other button is pressed to _accept_ a match,
then the result is recorded and a new trial is started.
"""

# ------------------------------------- #
#              99. CLEANUP              #
# ------------------------------------- #
"""
After the whole experiment is done 
(or if the participant/experimenter wants to terminate earlier),
some cleanup is required:
the connection to display and input hardware should be closed.
This is done using the `.close()` method of the HRL-object.
"""
ihrl.close()
