# Eyetracking

```{important}
This is an **advanced, lab-specific template**. It requires an SR Research
EyeLink eyetracker and its proprietary driver, and it will not run without them.
Read the other templates first: this page assumes you already know the module
layout and the design and results machinery they share.
```

This template is the [MLCM experiment](MLDS-MLCM) extended with eye tracking. It
records where the participant looked while they made each conjoint measurement
judgment, so that the choices can afterwards be related to fixation behavior.

The full example is at
[`examples/templates/eyetracking_example/`](https://github.com/computational-psychology/hrl/tree/master/examples/templates/eyetracking_example).

The reason this template is worth reading even if you have no EyeLink is that it
shows how `HRL` coexists with another piece of hardware that also wants to draw
on the screen. The eyetracker needs to display its own calibration targets, in
the same window, without `HRL` losing control of it.


## Dependencies

Beyond `numpy`, `pandas` and `Pillow`, this template requires **`pylink`**, the
Python interface to the EyeLink.

```{important}
`pylink` is **not** installable from PyPI, and `pip install pylink` will install
an unrelated package. It ships with the **EyeLink Developers Kit** from SR
Research, which you have to download and install from their support site. The
package is then installed from the copy that comes with the kit. See SR
Research's own documentation for the current procedure.

There is no substitute and no fallback: if `pylink` is missing, the very first
import in the script fails.
```


## Structure

Unlike the other templates, this one is a **single script**,
`mlcm_experiment_with_eyetracker.py`, plus three supporting files:

| File | Purpose |
| ---- | ------- |
| `mlcm_experiment_with_eyetracker.py` | The whole experiment: design reading, trial logic, eyetracker setup, main loop. |
| `CalibrationGraphicsPygame.py` | Draws the eyetracker's calibration targets, using the `HRL` graphics device. |
| `join_stimuli.py` | Offline utility: combines two rendered checkerboard images into one full-screen stimulus. |
| `qbeep.wav`, `type.wav`, `error.wav`, `fixTarget.bmp` | Sounds and target image used during calibration. |

It predates the `run_experiment.py` / `design.py` / `experiment_logic.py` split,
so it does its own design reading and its own resume logic. Keep that in mind if
you use it as a starting point: the parts specific to the eyetracker are worth
copying, the file handling around them is better taken from
[managing data](../useful-examples/managing-data).


## Stimuli

The stimuli are pre-rendered images, as in
[asymmetric matching](asymmetric-matching), loaded with the same
`image_to_array` helper. They live in `stimuli/<observer>/` and are named by
block and trial:

```{code-block} python
stim_name = 'stimuli/%s/block_%d_%d' % (vp_id, block, thistrial)

# Preloading images before we start eyetracking recording
# load stimlus image and convert from png to numpy array
curr_image = image_to_array(stim_name)

# texture creation in buffer : stimulus
checkerboard = hrl.graphics.newTexture(curr_image)
```

Note the comment: the image is loaded and uploaded **before** recording starts.
Anything slow that happens after the tracker starts recording lands in the data
as a gap.

`join_stimuli.py` is the offline step that produced these files. It takes the
two separately rendered checkerboards of an MLCM trial and pastes them into one
image the size of the whole screen, separated by a fixed gap. Combining them
offline rather than drawing two textures per trial means the displayed image is
byte-for-byte the same as the one handed to the eyetracker as a backdrop, which
matters for the analysis.


## Setting up the tracker

`prepare_eyetracker_for_recording_block` runs once per block. It opens a new EDF
file on the EyeLink host PC, tells the tracker what to record, and hooks up the
calibration display:

```{code-block} python
# Step 2: Open an EDF data file on the Host PC
edf_file = edf_fname + ".EDF"
print('Eyetracking data being saved in file: ', edf_file)

el_tracker.openDataFile(edf_file)

...

# Choose a calibration type, H3, HV3, HV5, HV13 (HV = horizontal/vertical)
el_tracker.sendCommand("calibration_type = HV9")

...

# Configure a graphics environment (genv) for tracker calibration
genv = CalibrationGraphics(el_tracker, hrl.graphics)
```

```{important}
The EDF filename is limited to **8 characters**, letters, digits and
underscores only. The script checks this and raises rather than discovering it
later on the host PC. The name is built as observer plus session number,
`'%s%.2d' % (vp_id, sess)`, which is why observer names in this template are
short.
```

The EDF file lives on the EyeLink host PC while recording, and is downloaded at
the end of each block by `terminate_task`, into `results/<observer>/EDF/`.

```{note}
`results/` is not in this repository. The demo EDF files and result CSVs were
left out of the migration. The experiment recreates the folder on startup and
handles a missing `blocks_done.csv`, so the demo runs from a clean checkout.
```


## Calibration graphics through `HRL`

This is the interesting part. Before every block the tracker enters setup mode
and draws its own calibration targets, and the participant follows them with
their eyes. Those targets must appear on the experimental monitor, which `HRL`
owns.

`CalibrationGraphicsPygame.py` solves this by subclassing the hook that `pylink`
provides for exactly this purpose, and handing it the `HRL` graphics device to
draw with:

```{code-block} python
class CalibrationGraphics(pylink.EyeLinkCustomDisplay):
    def __init__(self, tracker, win):
        pylink.EyeLinkCustomDisplay.__init__(self)

        self._disp = win  # HRL graphics
        self._tracker = tracker  # connection to the tracker

        ...

        self._bgColor = 0.2  # target color (foreground)
        self._fgColor = 0    # target color (background)
        self._targetSize = 32  # diameter of the target
        self._targetType = 'circle'  # could be 'circle' or 'picture'
```

The object is registered with `pylink`, and from then on the tracker's
calibration routine draws through `HRL` rather than opening a window of its own.
Calibration is then a single call, per block:

```{code-block} python
if not dummy_mode:
    try:
        el_tracker.doTrackerSetup()
    except RuntimeError as err:
        print('ERROR:', err)
        el_tracker.exitCalibration()
```

The colors here are intensities in the same `[0.0, 1.0]` scale as everywhere
else in `HRL`, so the calibration targets go through the same gamma correction
as the stimuli. That is the payoff of routing them through `HRL` instead of
letting `pylink` draw directly.


## A trial

Each trial follows the EyeLink protocol: go offline, put the stimulus on the
host PC's screen as a backdrop so the experimenter can see where the participant
is looking, mark the trial, drift-check, start recording, display, respond, stop.

```{code-block} python
# put the tracker in the offline mode first
el_tracker.setOfflineMode()

# clear the host screen before we draw the backdrop
el_tracker.sendCommand('clear_screen 0')

# show a backdrop image on the Host screen
el_tracker.imageBackdrop('%s.png' % stim_name,
                         0, 0, WIDTH, HEIGHT, 0, 0,
                         pylink.BX_MAXCONTRAST)

# send a "TRIALID" message to mark the start of a trial
el_tracker.sendMessage('TRIALID %d' % trl)
```

A **drift check** is done at the start of every trial, which is the recommended
practice. It measures how far the calibration has drifted since the last one and
corrects for it, and it lets the experimenter recalibrate by pressing Escape.

Recording then starts, and the display goes up:

```{code-block} python
el_tracker.startRecording(1, 1, 1, 1)

...

# draw the checkerboard
checkerboard.draw((0,0))

# flip everything
hrl.graphics.flip(clr=False)

...

el_tracker.sendMessage('image_onset')
```

Note the order: `flip` first, then the message. The message is what timestamps
the stimulus onset in the eye movement record, so it should be sent as close as
possible to the moment the image actually appears. Sending it before the flip
would put the onset marker before the stimulus.

Messages are sent for everything that happens: `image_onset`, `key_pressed`,
`blank_screen`, `time_out`, `trial_skipped_by_user`, `terminated_by_user`. In
the analysis, the eye movement record is cut into trials and events using
exactly these strings, so every event you will want to align to has to be marked
while it happens.

The response is collected with a **timeout**, unlike the other templates:

```{code-block} python
(btn,t1) = hrl.inputs.readButton(to=1) # polls every 50 ms
```

This is `HRL`'s `readButton` with a timeout, called in a loop. Waiting
indefinitely is not an option here: the tracker is recording, and a participant
who leaves without responding would produce one enormous trial. The loop also
checks whether the tracker is still connected, and terminates the task if it is
not.

Finally the trial variables are sent to the tracker, so that they appear in
SR Research's Data Viewer alongside the eye movement data:

```{code-block} python
el_tracker.sendMessage('!V TRIAL_VAR block %s' % sess)
el_tracker.sendMessage('!V TRIAL_VAR trial %s' % trl)
el_tracker.sendMessage('!V TRIAL_VAR response %s' % response)
el_tracker.sendMessage('!V TRIAL_VAR RT %d' % t1)

el_tracker.sendMessage('TRIAL_RESULT %d' % pylink.TRIAL_OK)
```

The same values are also written to the results `.csv`. Duplicating them is
deliberate: it means the behavioral data can be analyzed without the EDF files,
and the EDF files can be inspected without the CSVs.


## Dummy mode

The script has a `dummy_mode` flag near the top:

```{code-block} python
### Eyetracker
dummy_mode = False # True or False. Dummy mode=True is to debug the code without using eyetracker
```

With it set to `True`, calibration and drift checks are skipped, so the
experiment can be stepped through without a tracker attached. It still requires
`pylink` to be installed, since the import is unconditional. Use it to check
your stimuli, your design and your timing before booking the lab.


## Related

- [MLDS/MLCM](MLDS-MLCM) is the paradigm this extends, in its normal form.
- [asymmetric matching](asymmetric-matching) is the other template with
  pre-rendered stimuli.
- [deploying your code in the lab](../getting-started/deploying-in-lab) covers
  the ViewPixx setup this template is written for.
