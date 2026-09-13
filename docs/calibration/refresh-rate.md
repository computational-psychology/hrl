# Refresh rate

A monitor does not display a continuous image. It redraws the screen at a fixed
rate, typically 60, 100 or 120 times per second, and nothing you draw becomes
visible until the next redraw. Everything about timing in an experiment follows
from that.

Two things are worth checking on any experimental monitor:

1. that the refresh rate really is what the manufacturer claims;
2. that your graphics pipeline delivers a new frame in time, every time, and
   drops none.

The second matters more than the first. A dropped frame means a stimulus that
was on the screen for two frames instead of one, and nothing in your code will
tell you it happened unless you measure.


## Front and back buffers

`HRL` draws with **double buffering**. There are two frame buffers:

- the **front buffer**, which is what the monitor is currently displaying;
- the **back buffer**, which is where your drawing goes.

`texture.draw(...)` writes into the back buffer. Nothing appears on the screen.
Then `flip()` swaps the two: the back buffer becomes what is displayed, and the
old front buffer becomes the new drawing surface.

```{code-block} python
# Drawing: goes to the back buffer, invisible
stim_texture.draw(pos=pos, sz=(stim_texture.wdth, stim_texture.hght))

# Display: swap the buffers
ihrl.graphics.flip(clr=True)
```

This is why you can compose a display from several textures, as
[asymmetric matching](../templates/asymmetric-matching) does: draw them all,
then flip once. The participant never sees a half-drawn frame.

The `clr` argument controls whether the new back buffer is cleared after the
swap:

- `flip(clr=True)`, the default, clears it. The next frame starts blank, so you
  redraw everything you want to see.
- `flip(clr=False)` leaves the previous contents, so you can add to what is
  already there across frames.

```{code-block} python
def flip(self, clr=True):
    pygame.display.flip()
    if clr:
        opengl.glClear(opengl.GL_COLOR_BUFFER_BIT)
```

```{important}
`flip()` blocks until the monitor is ready for the next frame, provided
synchronization to the vertical refresh (VSYNC) is enabled in the graphics
driver. That blocking is what makes frame-accurate timing possible: a loop of
`flip()` calls runs at exactly the refresh rate. If VSYNC is disabled, `flip()`
returns immediately, your loop runs as fast as the CPU allows, and frames are
torn or skipped. Checking that VSYNC is on is the first thing to do if the
measurements below look wrong.
```

Counting flips is the reliable way to time a stimulus. `time.sleep(0.5)`, which
the [2-IFC template](../templates/2-AFC-2-IFC) uses, is accurate to about a
millisecond but is not synchronized to the monitor, so the actual duration is
half a second plus or minus a frame.


## Measuring in software

[`examples/check_monitor_rate/check_monitor_rate.py`](https://github.com/computational-psychology/hrl/blob/master/examples/check_monitor_rate/check_monitor_rate.py)
measures the rate from inside the experiment process, by timing the flips
themselves.

```
cd examples/check_monitor_rate
python check_monitor_rate.py
```

It works in two phases.

**Phase 1: estimate the rate.** After ten warm-up frames, it flips repeatedly
and records the interval between consecutive flips. Once the last ten intervals
agree to better than a millisecond, their mean is taken as the frame period:

```{code-block} python
    for frameN in range(nMaxFrames):
        hrl.graphics.flip()

        frameTime = now = defaultClock.getTime()
        ...
        deltaT = now - lastFrameT
        lastFrameT = now
        frameIntervals.append(deltaT)

        if len(frameIntervals) >= nIdentical and (
            np.std(frameIntervals[-nIdentical:]) < (threshold / 1000.0)
        ):
            rate = 1.0 / np.mean(frameIntervals[-nIdentical:])
```

The warm-up frames are not optional. The first few flips after a window opens
are not representative, and including them biases the estimate.

**Phase 2: count dropped frames under load.** With the rate known, a threshold
is set at 1.2 times the frame period, and the script then draws two moving
Gabor patches for a thousand frames, generating a new texture on every frame.
Any interval longer than the threshold is counted and reported as a dropped
frame:

```{code-block} python
    # setting threshold for dropped frames detection
    refreshThreshold = 1.0 / rate * 1.2
```

This second phase is the useful one. It is a realistic load: generating
stimuli, uploading textures and flipping, which is what an experiment with
online stimulus generation actually does.

The script prints the measured rate with its standard deviation, the number of
dropped frames, and writes all the frame intervals to a timestamped `.txt` file.
`plot_rate.py` in the same folder plots the distribution of those intervals.

Interpreting the result, in the script's own words:

```
To have 1 and only 1 dropped frame is NORMAL.

To have more than 1 dropped frame is NOT NORMAL.
It might mean that there is something wrong the graphic card settings or
graphic card's driver. You should check that synchronizing
to VSYNC is enabled.
```

```{important}
Run this **on the experimental monitor, fullscreen**. In a window on a normal
desktop the compositor gets between your flips and the screen, and the numbers
are meaningless. The script selects the lab setup by hostname, the same idiom
the [templates](../templates/templates-intro) use.
```


## Measuring with a photodiode

Software timing measures when `HRL` believes a frame was shown. A photodiode
measures when light actually came out of the monitor. The two can differ, and
only the second is ground truth.

[`examples/check_monitor_rate/check_monitor_rate_photodiode.py`](https://github.com/computational-psychology/hrl/blob/master/examples/check_monitor_rate/check_monitor_rate_photodiode.py)
is the same script with a different second phase. Instead of Gabors, it
alternates a white and a black square in the bottom left corner of the screen,
one frame each, for thirty seconds:

```{code-block} python
    white = np.ones(texsize)
    black = np.zeros(texsize)

    tex_white = hrl.graphics.newTexture(white)
    tex_black = hrl.graphics.newTexture(black)

    Nframes = int(30 * rate)

    for i in range(Nframes):
        if i % 2 == 0:
            # draw white
            tex_white.draw(pos=(0, hght - texsize[1]), sz=texsize)
        else:
            tex_black.draw(pos=(0, hght - texsize[1]), sz=texsize)

        # flip
        hrl.graphics.flip(clr=True)
```

Tape a photodiode over that corner, connect it to an oscilloscope or a data
acquisition device, and record. The square wave you get out is the monitor's
actual output. Its period is twice the frame period, so the refresh rate is
twice the frequency of the recorded signal. Any frame that was dropped shows up
as a pulse of double width, unambiguously and independently of anything the
computer thinks it did.

Note the two textures are created once, before the loop, and only redrawn. That
keeps the loop as cheap as possible, so that any dropped frames are attributable
to the display pipeline rather than to the measurement.

```{note}
This second method is also how you measure the **latency** of the display, that
is, how long after `flip()` returns the light actually changes. That is a
different quantity from the refresh rate, and on VPixx hardware it is documented
by the manufacturer, but it is worth confirming if your experiment synchronizes
with anything external such as an EEG trigger or an
[eyetracker](../templates/eyetracking).
```


## Related

- [Minimal luminance step](minimal-lum-step) is the equivalent question for the
  intensity axis rather than the time axis.
- [2-AFC/2-IFC](../templates/2-AFC-2-IFC) is the template most sensitive to
  timing.
