# Others

Two further properties of a display matter for luminance experiments, and
neither is covered by the `hrl-util lut` pipeline. This page records what exists
in the repository today and what is still missing.

```{note}
Unlike the preceding calibration pages, this one is not a procedure you can
follow end to end. The tooling described below exists but is not wired into the
`hrl-util` command line interface, and the measurement protocols have not been
written up. Treat this page as a pointer, and see the "status" notes.
```


## Temporal response

The [gamma correction](gamma-correction-linearization) pipeline measures the
monitor in a *static* state: a patch is displayed, the system waits, and then
the photometer is read. That tells you nothing about what the display does when
the image *changes*.

Two things can go wrong.

**The pixel does not reach its target luminance within a frame.** A liquid
crystal takes time to switch. If a pixel is still on its way from one value to
the next when the frame ends, the luminance actually presented is not the one in
your LUT. This matters for any stimulus that changes from frame to frame, and it
is worst for large luminance excursions.

**The luminance of a pixel depends on what surrounds it.** On some displays the
luminance of a patch changes when the rest of the screen changes, even though
the patch itself was not asked to change. This is a failure of independence
between pixels, and it invalidates the assumption that a LUT measured on a
uniform patch applies to a patterned stimulus.

### Existing tooling

Three older scripts under `hrl/util/calibration/` were written for exactly these
questions. They are standalone, and predate the `hrl-util` interface.

| Script | What it does |
| ------ | ------------ |
| `fixedpatch.py` | Holds a central square at a fixed luminance while oscillating the background luminance. Luminance is measured at the central square. Ideally the reading does not change; in practice it usually does, and by how much is the answer. |
| `rotatesin.py` | Displays a square wave in a central patch and rotates it by 90 degrees at a given frequency, with a fixed background. |
| `shiftsin.py` | Displays a sine wave in a central patch and shifts it back and forth by 180 degrees of phase. Superimposed, the two phases have exactly the luminance of the background, so at a high refresh rate the patch should look uniform to the naked eye. Any visible structure means frames are being dropped or pixels are not settling. |

All three write their measurements to a `.csv` and can be interrupted with
Escape, keeping what has been collected so far.

`shiftsin.py` is the most immediately useful of the three, because it needs no
photometer: it is a purely visual check, and a strikingly sensitive one. If the
patch is not uniform, something in the display chain is wrong. Compare with the
software and photodiode measurements on the
[refresh rate](refresh-rate) page.

```{note}
**Status.** These four scripts (the three above plus `gamma.py`, which sweeps
the full luminance range and can be run forward, reversed and randomized to
measure hysteresis) are **not** registered as `hrl-util` subcommands, and are run
directly as scripts. They have not been updated alongside the rest of the
library. Before relying on their output, check that they still run against the
current `HRL` API.
```


## Homogeneity

A monitor is not equally bright everywhere. Luminance typically falls off
towards the edges and corners, and the fall-off can be several percent. The
[LUT](gamma-correction-linearization) is measured at one place on the screen,
normally a patch at the center, so it describes the center and nowhere else.

This matters whenever a stimulus is not centered, and in particular for any
experiment that compares two patches at different screen positions, such as
[mutual matching](../templates/mutual-matching) or the two-sided displays in
[MLCM](../templates/MLDS-MLCM). An apparent difference between left and right
may be a property of the monitor rather than of the observer.

There are two ways around it, neither of which is currently automated here:

- **Measure and correct.** Map the luminance across the screen with a
  photometer on a grid of positions, and either restrict stimuli to the region
  that is uniform enough, or apply a position-dependent correction.
- **Counterbalance.** Present each condition equally often at each position, so
  that any inhomogeneity averages out across the design rather than loading onto
  one condition. This is what the templates that swap left and right between
  trials are doing, and it is the cheaper option.

```{note}
**Status.** There is no homogeneity measurement utility in this repository. The
`hrl-util lut measure` command draws its patch at the center of the screen
(`draw_uniform_square`), with a `--patch_size` option but no position argument,
so it cannot currently be pointed at a corner without modification. Documenting
a homogeneity protocol, and a utility to support it, is open work.
```


## Related

- [Gamma correction](gamma-correction-linearization), which measures the static
  luminance response at one screen position.
- [Refresh rate](refresh-rate), for the timing side of the temporal question.
