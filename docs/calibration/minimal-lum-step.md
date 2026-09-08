# Minimal luminance step

The smallest change in luminance you can present is the resolution of your
experiment on the intensity axis. If the effect you are measuring is smaller
than one step, you cannot measure it.


## The nominal step

Once the display is [linearized](gamma-correction-linearization), the luminance
steps are all the same size by construction, and the nominal step follows
directly from the bit depth and the measured luminance range:

$$
\Delta L = \frac{L_{max} - L_{min}}{2^{b}}
$$

where $b$ is the bit depth of the device.

Take the example `lut.csv` from the
[gamma correction](gamma-correction-linearization) page, measured on the
high-luminance Siemens monitor in the lab, with $L_{min} = 0.0034$ and
$L_{max} = 501.90$ $cdm^{-2}$, a range of about 501.9 $cdm^{-2}$.

| Device | $b$ | Levels | $\Delta L$ ($cdm^{-2}$) |
| ------ | --- | ------ | ----------------------- |
| Standard GPU | 8 | 256 | 1.96 |
| DataPixx or ViewPixx in M16 | 16 | 65536 | 0.0077 |

The difference is a factor of 256, which is
[where the extra bits come from](how-high-resolution-lum-is-achieved).

Whether those numbers are small enough depends on where in the range you are
working, because vision is roughly a ratio detector. At a background of 100
$cdm^{-2}$, the 8-bit step of 1.96 $cdm^{-2}$ is a contrast of about 2 percent,
which is comfortably above the detection threshold: it will be visible as
banding, and it is too coarse to sample a threshold function. The same step at
500 $cdm^{-2}$ is about 0.4 percent, near threshold. The 16-bit step of 0.0077
$cdm^{-2}$ is 0.008 percent at 100 $cdm^{-2}$, and stays below 1 percent all the
way down to about 1 $cdm^{-2}$.

So the resolution you have is not a single number: it is fine at the bright end
and coarse at the dark end, and the dark end is where an experiment runs out of
resolution first.


## Why it has to be measured

The calculation above is an upper bound on how well you can do. Three things
make the real step larger.

**The LUT is shorter than $2^{b}$.** The `linearize` step does not interpolate
between measurements. Where several input intensities were measured as
approximately the same luminance, they collapse into a single entry. A LUT built
from a 16-bit request will usually have fewer than 65536 rows, and each missing
row is a level you cannot address.

**The measurements are themselves quantized and noisy.** The step cannot be
smaller than what the photometer can resolve, or than the spread of repeated
readings at the same intensity. If your measurement noise is 0.05 $cdm^{-2}$, a
nominal step of 0.0077 $cdm^{-2}$ is not a measured quantity.

**Monitors drift.** Warm-up, ambient temperature and age all move the curve. A
step measured today is not a step tomorrow, which is why LUTs are dated and
re-measured.


## Measuring it

The direct check is to look at the LUT you actually have:

```{code-block} python
import numpy as np

lut = np.genfromtxt("lut.csv", skip_header=1, delimiter=",")

print(f"{len(lut)} addressable levels")

steps = np.diff(lut[:, 2])  # differences of the luminance column
print(f"smallest step: {steps.min():.5f} cd/m2")
print(f"largest step:  {steps.max():.5f} cd/m2")
print(f"median step:   {np.median(steps):.5f} cd/m2")
```

The number of rows is how many distinct luminances the display can actually
produce, and the differences of the third column are the steps between them. If
the largest step is much bigger than the median, the linearization has gaps and
the measurement is worth repeating with denser sampling in that region.

The independent check is to measure it: run

```
hrl-util lut verify
```

which re-measures the monitor with the LUT applied, and inspect the resulting
`lut_verification.csv`. The differences between successive measured luminances
there are the real steps, including everything the LUT does not know about.
Comparing them against the nominal step tells you how much of the theoretical
resolution you actually have.

```{note}
When reporting a stimulus in a paper, report the measured luminances, not the
intensities you asked for. The nominal step is a property of the encoding; the
measured one is a property of the display in the room where the experiment ran.
```


## Related

- [How is high resolution achieved?](how-high-resolution-lum-is-achieved) for
  where the 16 bits come from.
- [Gamma correction](gamma-correction-linearization) for how the LUT that
  determines the steps is built.
