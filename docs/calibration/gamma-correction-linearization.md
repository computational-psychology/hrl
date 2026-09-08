# Gamma correction

## Theory and logic behind it

In vision research we usually want to be sure about exactly what light the
monitor is putting out. To know that, we take careful measurements and
*calibrate* the display. Specifically, we measure the **luminance** (in
$cdm^{-2}$) of the light coming from the monitor, as a function of the
**intensity** value we asked for. That intensity is a float between `0.0` and
`1.0`, which is what the values in your stimulus array are.

The two are not the same thing, and it is worth keeping the words apart:

- **intensity** is a scale-free number the software asks the monitor for.
- **luminance** is a physical quantity the monitor actually emits, measured
  with a photometer.

For most display devices the relationship between them is **not linear**. A step
in intensity from `0.0` to `0.25` produces a much smaller increase in luminance
than an equal step from `0.75` to `1.0`. The shape of this relationship is known
as the **gamma** of the device. It differs between monitors, and it changes over
time, so it has to be measured on the machine you are actually going to use, and
re-measured periodically.

To correct for the gamma we measure the whole function. We then work out what
the intensity steps *should be* to make luminance rise linearly with input
intensity. The result is stored in a **LookUp Table** (LUT).

### The LUT format

A greyscale LUT is a three-column `.csv` file:

| IntensityIn |  IntensityOut | Luminance ($cdm^{-2}$) |
| ----------- | ------------- | ---------------------- |
| 0.0         | 0.0           | 0.0034                 |
| 0.00024     | 0.05490       | 0.1334                 |
| 0.00049     | 0.07058       | 0.2820                 |
| ...         | ...           | ...                    |
| 0.98485     | 0.99607       | 498.88                 |
| 0.99413     | 1.0           | 501.90                 |

- `intensity_in` is what you put in your stimulus array.
- `intensity_out` is what `HRL` actually sends to the monitor for it.
- `luminance` is the luminance that was measured for that `intensity_out`.

The first and third columns are the pair that matters to you as an
experimenter: they say what luminance you get for a value in your stimulus. The
first and second columns are what `HRL` uses at run time.

Reading the table row by row: the entries are chosen so that the **luminance
column increases in equal steps**. That is what "linearized" means. The
intensity column that produces those equal luminance steps is not itself evenly
spaced, and that unevenness is exactly the gamma of the monitor, inverted.

### How `HRL` applies it

Applying a LUT is a single interpolation, in `hrl/luts.py`:

```{code-block} python
def gamma_correct_grey(img, LUT):
    return np.interp(img, LUT[:, 0], LUT[:, 1])
```

Every image passed to `newTexture` goes through this before it is encoded and
uploaded. You give the LUT to `HRL` once, at construction:

```{code-block} python
ihrl = HRL(
    graphics="datapixx",
    lut="lut.csv",     # filepath to the LookUp Table
    ...
)
```

With `lut=None`, which is the default, no correction is applied and the
intensities go to the monitor unchanged.

```{note}
For color displays there is a second format, the CLUT, with thirteen columns:
`intensity_in`, then `R_out`, `G_out`, `B_out`, then a flattened 3 by 3
RGB to XYZ matrix. It is applied per channel by `gamma_correct_RGB`. The module
docstring of `hrl/luts.py` is the authority on both formats.
```

```{important}
`hrl.luts` also has `create_lut` and `create_clut`, which build a LUT from a
gamma parameter rather than from measurements. Those exist for **testing and
simulation only**. Never use a parametric LUT to characterize a real display:
the whole point of calibration is that the real gamma is not the textbook one.
```


## How to do it with `HRL`

Calibration is done with the `hrl-util` command line tool, which is installed
with the package:

```
hrl-util lut {measure,smooth,linearize,plot,verify}
```

The pipeline is four steps, each reading the file the previous one wrote:

```{mermaid}
graph LR;
    measure -- measure.csv --> smooth
    smooth -- smooth.csv --> linearize
    linearize -- lut.csv --> verify
    linearize -- lut.csv --> plot
    verify -- lut_verification.csv --> done[check linearity]
```

The intermediate filenames are fixed, and every command is run in the directory
where you want the files to land.

```{important}
Run this on the machine and the monitor you are calibrating, with a photometer
connected, in the room lighting you will run your experiment in. A LUT is a
property of one monitor in one state, not of `HRL`.
```

### Step 1: measure

```
hrl-util lut measure
```

This displays a uniform patch at a series of intensities and reads the
photometer at each one, writing `measure.csv`.

The most important options:

| Flag | Meaning |
| ---- | ------- |
| `-gr`, `--graphics` | Graphics device: `GPU_grey`, `DATAPixx` or `VIEWPixx_grey`. Default `DataPixx`. |
| `-p`, `--photometer` | `minolta` (default) for the Minolta LS-100, or `optical` for the OptiCAL. |
| `-b`, `--bit_depth` | Resolution of the sampling: 16 by default, that is `2**16 = 65536` intensity levels. |
| `-n`, `--n_samples` | Photometer readings per intensity, 5 by default. |
| `-sl`, `--sleep_time` | Milliseconds between readings, 200 by default. |
| `-sz`, `--patch_size` | Size of the measured patch as a fraction of the screen, 0.5 by default. |
| `-mn`, `-mx` | Minimum and maximum intensity to measure, 0.0 and 1.0 by default. |
| `-rn`, `-rv` | Randomize or reverse the order in which intensities are measured. |
| `-wd`, `-hg`, `-sc`, `-bg` | Screen width, height, screen number and background intensity. |

The device names for `-gr` are class names, not the aliases used in the `HRL`
constructor. Both photometers are read over a serial connection on
`/dev/ttyUSB0`.

```{important}
The full 16 bits is 65536 measurements, which at five readings each is far too
many to measure in one sitting. In practice you sample a subset: pass a smaller
`--bit_depth`, for instance `-b 8` for 256 levels, measure that, and let the
linearization step interpolate. What matters for the algorithm is that the
sampling is **even** across the intensity range, because the smoothing kernel
assumes every step is the same size.
```

Randomizing the order with `-rn` is worth doing: it stops any drift in the
monitor over the course of a long measurement session from being confounded with
intensity. Measuring twice, once forward and once reversed with `-rv`, and
comparing the two, is a cheap check for that same drift.

Pressing Escape during measurement stops it cleanly, keeping what has been
measured so far.

### Step 2: smooth

```
hrl-util lut smooth
```

This reads `measure.csv` and writes `smooth.csv`, with columns `intensity_in`
and `luminance`. Four things happen inside:

1. **combine**, gathering all the repeated readings per intensity.
2. **remove_outliers**, discarding readings that deviate from the closest
   measurement at the same intensity by more than both an absolute tolerance
   (0.075 $cdm^{-2}$) and a relative one (0.75 percent). A photometer reading
   taken while somebody walked past the screen gets thrown out here.
3. **average**, collapsing the remaining readings per intensity to one value.
4. **smooth**, convolving the luminance values of adjacent intensities with a
   kernel.

Options:

| Flag | Meaning |
| ---- | ------- |
| `-n`, `--order` | Number of times to apply the kernel, 0 by default, meaning no smoothing at all and only the averaging above. |
| `-k`, `--kernel` | The kernel, by default `0.2 0.2 0.2 0.2 0.2`, a five-point moving average. |

Start with the default of no smoothing. Smooth only if the measured curve is
visibly noisy, and check the result with `plot`. Smoothing too aggressively
flattens the low-intensity region, which is where the curve is steepest and
where you can least afford the error.

### Step 3: linearize

```
hrl-util lut linearize
```

This reads `smooth.csv` and writes `lut.csv`, the file you pass to `HRL`. It
takes `2**bit_depth` equally spaced steps between the minimum and maximum
measured luminance, and for each one finds the first measured intensity that
reaches at least that luminance.

```{note}
This step **does not interpolate** between measurements. The resulting LUT is at
most as long as the measurements, and usually shorter: if several input
intensities were measured as approximately the same luminance, they collapse to
one entry. So a `lut.csv` with fewer rows than `2**bit_depth` is expected, not a
sign that something went wrong.
```

The `-b/--bit_depth` here is the resolution of the LUT you want, and is
independent of the one used during measurement.

### Step 4: verify

```
hrl-util lut verify
```

This is the check that the whole thing worked. It measures the monitor again,
but this time with the new LUT applied, using the `intensity_in` values from the
LUT itself, and writes `lut_verification.csv`.

If the calibration is good, the luminances in that file increase **linearly**
with the intensities. If they do not, the LUT is wrong and the earlier steps
need revisiting.

Options are those of `measure`, plus `-l/--lut` to point at a LUT other than
`lut.csv`, and `-o/--out_file` for the output name.

### Plotting

```
hrl-util lut plot
```

Reads `lut.csv` and shows two panels: output intensity against input intensity,
which is the inverse gamma curve, and luminance against intensity before and
after correction. The corrected luminance curve should be a straight line. This
requires `matplotlib`.


## Using the LUT

Once you have a `lut.csv`, pass it to `HRL` as described in
[deploying your code in the lab](../getting-started/deploying-in-lab), and keep
it with the experiment. It is worth storing LUTs under a datestamp, as the lab
does in `~/luts/YYYYMMDD/`, and always using the most recent one: a LUT measured
a year ago describes a monitor that no longer exists.

If you need to specify your stimuli in luminance rather than in intensity, you
have to invert the mapping: look up the desired luminance in the third column
and read off the first. See
[deploying your code in the lab](../getting-started/deploying-in-lab) for a
script that does this.


## Related

- [How is high resolution achieved?](how-high-resolution-lum-is-achieved)
  explains what happens to the corrected intensities afterwards.
- [Minimal luminance step](minimal-lum-step) is about how finely the corrected
  scale can actually be divided.
