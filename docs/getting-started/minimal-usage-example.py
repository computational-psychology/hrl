import numpy as np
from hrl import HRL

# 0. SET-UP  
# Define window parameters
SHAPE = (600, 800)  # Desired shape of the drawing window (height, width)
CENTER = (SHAPE[0] // 2, SHAPE[1] // 2)  # Center of the drawing window

# Create HRL interface object
ihrl = HRL(
    graphics="gpu",  # Use the default GPU as graphics device driver
    inputs="keyboard",  # Use the keyboard as input device driver
    hght=SHAPE[0],  # Height of the window, in pixels
    wdth=SHAPE[1],  # Width of the window, in pixels
    scrn=1,   # Which screen (monitor) to use
    fs=False,  # Fullscreen or not
    bg=0.5,  # background intensity (black=0.0; white=1.0)
)


# 1. DEFINE STIMULUS 
rng = np.random.default_rng()
stim_image = rng.standard_normal(size=(256, 256))


# 2. DISPLAY THE STIMULUS
# Convert the stimulus image(matrix) to an OpenGL texture
stim_texture = ihrl.graphics.newTexture(stim_image)

# Determine position: we want the stimulus in the center of the frame
pos = (CENTER[1] - (stim_texture.wdth // 2), CENTER[0] - (stim_texture.hght // 2))

# Create a display: draw texture on the frame buffer
stim_texture.draw(pos=pos, sz=(stim_texture.wdth, stim_texture.hght))

# Display: flip the frame buffer
ihrl.graphics.flip(clr=True)  # also `clear` the frame buffer


# 3. COLLECT A  RESPONSE  
button, t = ihrl.inputs.readButton()
print(f"Participant pressed {button} after {t}s")


# 4. "PROCESS" RESPONSE
# Assign responses to correct/incorrect
response_correct = {"Right": True, "Left": False, "Escape": False}

if response_correct[button]:
    print(f"Participant pressed {button}, which is correct")
else:
    print(f"Participant pressed {button}, which is incorrect")

# CLEANUP 
ihrl.close()
