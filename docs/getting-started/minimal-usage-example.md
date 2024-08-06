# Minimal example

Here we show a basic example of how to show a stimulus
and collect responses. 
First we go step by step explaning on how to use HRL,
at the bottom you can find the code for the full working example.


## Step-by-step

### Set-up

The first step is to import and initialize `HRL`. 

```{code-block} python
from hrl import HRL

# Define window parameters
SHAPE = (600, 800)  # Desired shape of the drawing window (height, width)

# Create HRL interface object
ihrl = HRL(
    graphics="gpu",     # Use the default GPU as graphics device driver
    inputs="keyboard",  # Use the keyboard as input device driver
    hght=SHAPE[0],      # Height of the window, in pixels
    wdth=SHAPE[1],      # Width of the window, in pixels
    scrn=0,             # Which screen (monitor) to use
    fs=False,           # Fullscreen or not
    bg=0.5,             # background intensity (black=0.0; white=1.0)
)
```

`ihrl` is an `HRL` instance which is our main point of interaction with
the library. 

```{note}
 `HRL` is designed with the idea that you can develop your code in your own
local machine, and by just a change in the arguments you can deploy it in
the lab. For now we keep the default parameters, in the next section
we will show how to deploy it in the lab.
```


### Define a stimulus

In order to display a stimulus,
we first have to define/load/create a stimulus.
There are many ways to do so, e.g., load an image from a file.
Here, create an image-matrix ({py:class}`numpy.ndarray`) with 256x256 random values


```{code-block} python
import numpy as np

stim_image = np.random.uniform(low=0.0, high=1.0, size=(256, 256))
```


### Display the stimulus

To display on the screen `HRL`  we first create a texture containing 
the image information using the method `hrl.graphics.newTexture`.
The input is a input array with values between 0 and 1.

```{code-block} python
# Convert the stimulus image(matrix) to an OpenGL texture
stim_texture = ihrl.graphics.newTexture(stim_image)
```

We then draw this texture on the buffer with the method `draw` of a 
texture object. 
Here we decide also where to draw it (its position).


```{code-block} python
# Determine position: we want the stimulus in the center of the frame
pos = (CENTER[1] - (stim_texture.wdth // 2), CENTER[0] - (stim_texture.hght // 2))

# Create a display: draw texture on the frame buffer
stim_texture.draw(pos=pos, sz=(stim_texture.wdth, stim_texture.hght))
```

Finally, we need to *flip* the buffers. At this point is where 
what you have drawn before becomes visible. 
More on what the buffers are in 
[our documentation on measuring the refresh-rate](../calibration/refresh-rate) 


```{code-block} python
# Display: flip the frame buffer
ihrl.graphics.flip(clr=True)  # also clr=True means that the screen will be cleared before showing
```

The stimulus display will then stay on the screen
until either another `.flip()` is called (with `clr=True`),
or the hrl instance is closed.


### Collect a response

After displaying some stimulus, we often want some response from the participant.
This generally requires two steps:
- capturing the response via some input hardware (e.g., keyboard, button box)
- processing the response,  i.e., deciding what to do with it
  (record to disk directly, determine next stimulus, etc.)

HRL also provides functionality to interact with input hardware.
The high-level interface is `<hrl_object>.inputs.readButton()` and 
it waits for a (single) button press.

By default, `readButton` waits until one of the following buttons is pressed:
"Up", "Down", "Right", "Left", "Space", "Escape"

```{code-block} python
ihrl.inputs.readButton()
print("Participant pressed a button")
```
"Up", "Down", "Left" and "Right" refers to the arrows in the keyboard,


You can also ask `readButton`to wait for only some buttons
and ignore all others:


```{code-block} python
ihrl.inputs.readButton(btns=("Right", "Space", "Left", "Escape"))
print("Participant pressed a button")
```

The method `readButton` also returns the time passed
since it was called. 

```{code-block} python
button, t = ihrl.inputs.readButton()
print(f"Participant pressed {button} after {t}s")
```


### Process the response

Having captured a response, we need to process it.
This can include all kinds of steps, for instance
deciding if the response is "correct" or not (in tasks where this is possible);
storing the response (and additional information) as results data;
deciding what the next trial and stimulus will be.

```{code-block} python
# Assign responses to correct/incorreect
response_correct = {"Right": True, "Left": False, "Escape": False}

if response_correct[button]:
    print(f"Participant pressed {button}, which is correct")
else:
    print(f"Participant pressed {button}, which is incorrect")
``` 

    
How exactly the response is mapped to some action
depends heavily on the experiment and task.
For example, in most forced choice experiment,
the response is converted to correct/incorrect,
recorded as a result, and a new trial is presented.

In an adjustment task the response leads to increasing 
or decreasing some stimulus parameter.
In these experiments, a button press will lead to a new *stimulus*,
but not immediately to recording a new result.
Only when some other button is pressed to *accept* a match,
then the result is recorded and a new trial is started.

You can find templates for these and many other tasks in 
section [experiment templates](../intro)


### Clean-up


After the whole experiment is done 
(or if the participant/experimenter wants to terminate earlier),
some cleanup is required:
the connection to display and input hardware should be closed.
This is done using the `.close()` method of the HRL-object.

```{code-block} python
ihrl.close()
```


## Full example

This is the same code as above but put together in a single script.
In this example HRL opens a window, shows a randomly generated texture
and waits for any allowed key press. Finally it closes the window.


```{code-block} python
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


# 4. PROCESS RESPONSE
# Assign responses to correct/incorrect
response_correct = {"Right": True, "Left": False, "Escape": False}

if response_correct[button]:
    print(f"Participant pressed {button}, which is correct")
else:
    print(f"Participant pressed {button}, which is incorrect")

# CLEANUP 
ihrl.close()

```
