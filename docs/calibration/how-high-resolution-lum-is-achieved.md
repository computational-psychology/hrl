# How is high resolution achieved?

The "HR" in `HRL` is high resolution *luminance*. This page explains what that
means and how it is done.


## The problem with 8 bits

A standard graphics card drives a monitor with 8 bits per colour channel. For a
greyscale image, where red, green and blue all carry the same value, that gives
`2**8 = 256` distinguishable intensity levels between black and white.

For many purposes 256 levels are plenty. For psychophysics they often are not.
Two problems appear:

**The steps are visible.** On a smooth luminance gradient, 256 levels produce
visible banding. The eye is very good at detecting an edge, even one of a
fraction of a percent in luminance, and a quantized gradient is a series of
edges.

**The steps are unevenly useful.** After [gamma
correction](gamma-correction-linearization), the intensities are chosen to give
equal *luminance* steps. But the correction can only pick from the 256 values
the hardware can produce, and near the dark end of the range, where the gamma
curve is steepest, several of the original levels collapse onto the same
corrected value. You end up with fewer than 256 usable levels, and the loss is
worst exactly where you often care most. See
[minimal luminance step](minimal-lum-step).

If your experiment measures a threshold that is smaller than one of these steps,
you cannot measure it at all.


## The solution: two channels, one number

VPixx hardware (DataPixx and ViewPixx) provides a video mode called **M16** for
this. In M16 mode the device stops treating the red and green channels as
colours. Instead it reads them as the two halves of a single 16-bit number:

- the **red** channel carries the high byte, bits 8 to 15
- the **green** channel carries the low byte, bits 0 to 7
- the **blue** channel is unused

The device concatenates them back into one 16-bit greyscale value and drives all
three of the monitor's guns with it. The result is `2**16 = 65536` levels
instead of 256, a factor of 256 more resolution, over the same ordinary
8-bit-per-channel video link.

This trick costs colour: an M16 display is greyscale only. That is the trade
`HRL` was built around, and it is why the library's core is greyscale and
colour support came later, in a different device mode.


## Where it happens in the code

The splitting is done in **software**, by `HRL`, in the graphics class. Every
device class implements exactly one method, `channels_from_img`, which encodes a
`[0.0, 1.0]` image into four channels. That method is the only difference
between an ordinary GPU and a DataPixx.

For `GPU_grey`, the value is discretized to 8 bits and copied to all three
channels:

```{code-block} python
# Discretize to 8-bit integers, single channel
arr = img * (2**self.bitdepth - 1)
arr = np.asarray(arr, dtype=np.uint32)

# Duplicate to 4 channels, with max alpha
channels = (
    arr,  # R channel
    arr,  # G channel
    arr,  # B channel
    2**self.bitdepth - 1,  # Alpha channel
)
```

For `DATAPixx` and `VIEWPixx_grey`, the value is discretized to **16** bits and
then split by integer division and remainder:

```{code-block} python
# Discretize to 16-bit integers, single channel
arr = img * (2 ** (2 * self.bitdepth) - 1)
arr = np.asarray(arr, dtype=np.uint32)

# Convert to datapixx R-G concatenated format
channels = (
    arr // (2**self.bitdepth),  # R channel (high byte)
    arr % (2**self.bitdepth),   # G channel (low byte)
    np.zeros_like(arr),         # B channel (not used)
    2**self.bitdepth - 1,       # Alpha channel (max intensity)
)
```

`arr // 256` is the high byte and `arr % 256` is the low byte, which is the
whole encoding.

```{important}
`bitdepth` on these classes is **8** on every one of them, including the
DataPixx. It means bits per *physical channel*, which is a property of the video
link and is always 8. It is not the effective luminance resolution. That is why
the DataPixx code says `2 ** (2 * self.bitdepth)`: two channels of 8 bits each.
Reading `bitdepth = 8` on `DATAPixx` and concluding that it is an 8-bit device
is the mistake this note exists to prevent.
```


## The full pipeline

Every image you display goes through the same four stages:

```{mermaid}
graph LR;
    img["numpy array in [0, 1]"] --> gamma["gamma_correct (LUT)"]
    gamma --> channels["channels_from_img()"]
    channels --> bytestring["bytestring_from_channels()"]
    bytestring --> texture["OpenGL texture"]
```

Only the third stage differs between devices. Gamma correction, packing into a
32-bit RGBA bytestring, and uploading as an OpenGL texture are shared, in
`hrl/graphics/graphics.py`.

Note the order: **gamma correction happens before the split**. The LUT maps your
input intensity to a corrected intensity, still as a float in `[0.0, 1.0]`, and
only then is that float discretized to 16 bits and divided between the two
channels. The correction is therefore applied at the full resolution of the
device, not at 8 bits.


## This is what `graphics=` selects

All of the above is what changes when you change one constructor argument:

```{code-block} python
ihrl = HRL(graphics="gpu", ...)       # 8-bit, 256 levels, any machine
ihrl = HRL(graphics="datapixx", ...)  # 16-bit via R-G concatenation
ihrl = HRL(graphics="viewpixx", ...)  # 16-bit via R-G concatenation
```

Your experiment code does not change. You still hand `newTexture` a numpy array
of floats between 0 and 1; the encoding underneath is the device's business.
That is the whole design idea behind `HRL`, and it is why you can develop an
experiment on a laptop and run it in the lab by editing one dictionary. See
[deploying your code in the lab](../getting-started/deploying-in-lab).

```{note}
The device classes are imported lazily, only when selected. This is deliberate:
the VPixx classes need the proprietary `pypixxlib`, and importing it eagerly
would make `HRL` unusable on machines that do not have it. If you add a device,
add it the same way.
```

The ViewPixx can also be driven in **C24** mode, as `VIEWPixx_RGB`, which is
ordinary 8-bit-per-channel colour. High-resolution greyscale and colour are
mutually exclusive on this hardware: you pick one per session.


## Related

- [Gamma correction](gamma-correction-linearization), which happens before the
  encoding described here.
- [Minimal luminance step](minimal-lum-step), for what 16 bits buys you in
  $cdm^{-2}$.
- [Deploying your code in the lab](../getting-started/deploying-in-lab).
