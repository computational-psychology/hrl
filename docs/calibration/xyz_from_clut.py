# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     custom_cell_magics: kql
#     notebook_metadata_filter: jupytext,-kernelspec
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.2
# ---

# %% [markdown]
# # CLUT: Mapping Input RGB to Output Chromaticity
#
# When you show a stimulus on a display, you usually want precise, physically
# accurate control over what actually appears on screen -- its chromaticity
# and luminance -- not just its nominal RGB numbers.
#
# That's harder than it sounds. Raw digital RGB has no guaranteed, fixed
# relationship to the physical light that comes out. Nothing promises that
# relationship is simple, or that it stays the same across the display's
# range. You can't assume it -- you have to measure it.
#
# This notebook works through what that measurement gives you, how to use it
# to predict what a stimulus will look like, and how to invert that to solve
# for the RGB a stimulus actually needs.

# %%
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from hrl.cluts import (
    RGB_to_XYZ,
    RGB_to_XYZ_single_matrix,
    XYZ_to_RGB,
    XYZ_to_RGB_single_matrix,
    gamma_correct_RGB,
    invert_gamma_correct_RGB,
)

# %% [markdown]
# ## 1. Measuring a Display's Behavior
#
# The characterization process: sweep each channel in isolation across its
# full input range, and measure the resulting CIE XYZ tristimulus with a
# colorimeter at each step (`hrl.cluts.measure()` does exactly this -- not
# run here, since it needs real hardware).
#
# That gives, per channel, a table of swept input level -> measured XYZ.
# Averaged, cleaned of outliers, and packaged up, this is what a CLUT is.
# Here's a real one, measured on a ViewPixx3D display.

# %%
try:
    notebook_dir = Path(__file__).resolve().parent
except NameError:
    notebook_dir = Path.cwd()

clut_path = notebook_dir / "VIEWPixx3D_20260808.clut.csv"
if not clut_path.exists():
    raise FileNotFoundError(f"CLUT file not found: {clut_path}")

clut = np.genfromtxt(clut_path, delimiter=",", skip_header=1)

print(f"Using CLUT: {clut_path}")
print(f"CLUT shape: {clut.shape}")
print(f"Swept levels (column 0): {clut[0, 0]:.3f} ... {clut[-1, 0]:.3f}, {clut.shape[0]} steps")

# Shared full-range sweeps, reused throughout the notebook: gray (R=G=B) and
# isolated single-channel primaries (other two channels held at 0).
gray_levels_full = np.linspace(0.0, 1.0, 300)
gray_rgb_full = np.column_stack([gray_levels_full] * 3)
zeros_full = np.zeros_like(gray_levels_full)
red_rgb_full = np.column_stack([gray_levels_full, zeros_full, zeros_full])
green_rgb_full = np.column_stack([zeros_full, gray_levels_full, zeros_full])
blue_rgb_full = np.column_stack([zeros_full, zeros_full, gray_levels_full])

# %% [markdown]
# The file has more structure than just that first column -- we'll get to
# the rest of it as we actually need it.

# %% [markdown]
# ## 2. A Big Lookup Table: Predicting XYZ Directly
#
# Here's the fundamental thing this measurement gives you: for a signal you
# actually send the display, what light comes out. No correction, no matrix,
# no separate model needed -- the measured relationship *is* the model, and
# predicting XYZ for any signal in between what was measured is just
# interpolation: `RGB_to_XYZ(signal, clut, gamma_correct=False)`.
#
# (One assumption worth flagging early: this treats each channel's
# contribution as independent and additive -- no cross-channel interaction.
# That's true by construction here, since the underlying measurements were
# channel-isolated. Section 5 comes back to what that means in practice.)

# %%
example_signal = np.array([0.3, 0.3, 0.3])
example_xyz = RGB_to_XYZ(example_signal, clut, gamma_correct=False)[0]
print(f"Signal {example_signal} -> XYZ {example_xyz}")

Y_lookup_gray = RGB_to_XYZ(gray_rgb_full, clut, gamma_correct=False)[:, 1]
Y_lookup_red = RGB_to_XYZ(red_rgb_full, clut, gamma_correct=False)[:, 1]
Y_lookup_green = RGB_to_XYZ(green_rgb_full, clut, gamma_correct=False)[:, 1]
Y_lookup_blue = RGB_to_XYZ(blue_rgb_full, clut, gamma_correct=False)[:, 1]

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(gray_levels_full, Y_lookup_gray, color="k", label="Gray (R=G=B)")
ax.plot(gray_levels_full, Y_lookup_red, color="tab:red", label="Red only")
ax.plot(gray_levels_full, Y_lookup_green, color="tab:green", label="Green only")
ax.plot(gray_levels_full, Y_lookup_blue, color="tab:blue", label="Blue only")
ax.set_title("Direct Lookup: Predicted Y vs Raw Signal Sent")
ax.set_xlabel("Signal sent (0-1)")
ax.set_ylabel("Predicted Y")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()

# %% [markdown]
# This already works, end to end -- given any signal, we get a real,
# measured-data-backed prediction of what comes out. But look at the shape:
# clearly not straight lines. Equal steps in signal do not produce equal
# steps in luminance. That's not a mistake -- it's just what this display
# physically does. It's also inconvenient, which is where the next section
# picks up.

# %% [markdown]
# ## 3. Wouldn't a Linear Relationship Be Nicer?
#
# If you're building a stimulus -- say, modulating contrast between two
# chromaticity endpoints -- a coordinate where equal steps in your input
# variable produce equal physical steps would make that arithmetic trivial:
# just scale by the contrast fraction you want. The curves above don't have
# that property. Can we construct a coordinate that does?

# %% [markdown]
# ### 3a. Linearization
#
# This is exactly what a CLUT's remaining columns are for. Columns 1-3 give,
# for each swept level in column 0, the corrected ("drive") signal that
# actually gets sent to the display -- chosen specifically so that physical
# response comes out linear in column 0. `gamma_correct_RGB` applies this
# mapping; `invert_gamma_correct_RGB` undoes it.

# %%
example_input = np.array([0.5, 0.5, 0.5])
example_drive = gamma_correct_RGB(example_input, clut)
print(f"Input RGB {example_input} -> drive RGB {example_drive}")

recovered_input = invert_gamma_correct_RGB(example_drive, clut)
print(f"Drive RGB {example_drive} -> recovered input RGB {recovered_input} (round trip)")

drive_full = gamma_correct_RGB(gray_rgb_full, clut)

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(gray_levels_full, drive_full[:, 0], color="tab:red", label="R drive")
ax.plot(gray_levels_full, drive_full[:, 1], color="tab:green", label="G drive")
ax.plot(gray_levels_full, drive_full[:, 2], color="tab:blue", label="B drive")
ax.plot([0, 1], [0, 1], color="k", linestyle=":", linewidth=1, label="identity")
ax.set_title("Input Level vs Drive (per channel)")
ax.set_xlabel("Input level (intensity_in)")
ax.set_ylabel("Drive value")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()

# %% [markdown]
# Each channel's drive curve is a different, deliberately nonlinear function
# of input level -- that's the correction. Does it deliver on the promise?
# Route the exact same full model through this mapping (`gamma_correct=True`)
# and check.

# %%
Y_full_gray = RGB_to_XYZ(gray_rgb_full, clut, gamma_correct=True)[:, 1]
Y_full_red = RGB_to_XYZ(red_rgb_full, clut, gamma_correct=True)[:, 1]
Y_full_green = RGB_to_XYZ(green_rgb_full, clut, gamma_correct=True)[:, 1]
Y_full_blue = RGB_to_XYZ(blue_rgb_full, clut, gamma_correct=True)[:, 1]

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(gray_levels_full, Y_full_gray, color="k", label="Gray (R=G=B)")
ax.plot(gray_levels_full, Y_full_red, color="tab:red", label="Red only")
ax.plot(gray_levels_full, Y_full_green, color="tab:green", label="Green only")
ax.plot(gray_levels_full, Y_full_blue, color="tab:blue", label="Blue only")
ax.set_title("Full Model: Predicted Y vs Input Level (After Linearization)")
ax.set_xlabel("Input level (intensity_in)")
ax.set_ylabel("Predicted Y")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()


def linearity_r2(x, y):
    slope, intercept = np.polyfit(x, y, deg=1)
    fit = slope * x + intercept
    residual = y - fit
    return 1.0 - np.sum(residual**2) / np.sum((y - y.mean()) ** 2)


print(f"{'channel':>7}  {'R^2 vs signal (sec. 2)':>24}  {'R^2 vs input level':>20}")
for name, y_signal, y_input in [
    ("R", Y_lookup_red, Y_full_red),
    ("G", Y_lookup_green, Y_full_green),
    ("B", Y_lookup_blue, Y_full_blue),
    ("Gray", Y_lookup_gray, Y_full_gray),
]:
    print(
        f"{name:>7}  {linearity_r2(gray_levels_full, y_signal):24.4f}  "
        f"{linearity_r2(gray_levels_full, y_input):20.6f}"
    )

# %% [markdown]
# Same underlying model, same data -- just a different input coordinate --
# and the curves go from visibly bowed (R^2 as low as 0.88) to essentially
# straight (R^2 above 0.999). Input level (`intensity_in`) really is close
# to the linear coordinate we wanted.

# %% [markdown]
# ### 3b. A Single Matrix on Input Level
#
# If Y is close to linear in input level, a single 3x3 matrix -- one fixed
# gain per channel, no per-level lookup -- should predict it reasonably
# well. `RGB_to_XYZ_single_matrix(rgb, clut)` does exactly that: it builds
# the matrix from `clut` internally, calibrated directly against input
# level, so it applies with no separate gamma-correction step at all.

# %%
Y_single_gray = RGB_to_XYZ_single_matrix(gray_rgb_full, clut)[:, 1]
Y_single_red = RGB_to_XYZ_single_matrix(red_rgb_full, clut)[:, 1]
Y_single_green = RGB_to_XYZ_single_matrix(green_rgb_full, clut)[:, 1]
Y_single_blue = RGB_to_XYZ_single_matrix(blue_rgb_full, clut)[:, 1]

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(gray_levels_full, Y_full_gray, color="k", label="Full model (gray)")
ax.plot(gray_levels_full, Y_single_gray, color="k", linestyle="--", label="Single matrix (gray)")
ax.plot(gray_levels_full, Y_full_red, color="tab:red", alpha=0.5, label="Full model (red)")
ax.plot(
    gray_levels_full, Y_single_red, color="tab:red", linestyle="--", label="Single matrix (red)"
)
ax.set_title("Single Matrix vs Full Model, on Input Level")
ax.set_xlabel("Input level")
ax.set_ylabel("Predicted Y")
ax.legend(fontsize=8)
ax.grid(alpha=0.3)
plt.tight_layout()

print()
print(f"{'channel':>7}  {'R^2 vs full model':>18}  {'max abs err':>12}")
for name, y_single, y_full in [
    ("R", Y_single_red, Y_full_red),
    ("G", Y_single_green, Y_full_green),
    ("B", Y_single_blue, Y_full_blue),
    ("Gray", Y_single_gray, Y_full_gray),
]:
    resid = y_single - y_full
    r2 = 1.0 - np.sum(resid**2) / np.sum((y_full - y_full.mean()) ** 2)
    print(f"{name:>7}  {r2:18.4f}  {np.max(np.abs(resid)):12.3f}")

# %% [markdown]
# Good, not perfect: R^2 in the high 0.99s for every channel, with a few
# Y-units of residual error at the largest deviations. That residual is the
# real, physical departure from perfect linearity -- this display doesn't
# owe us an exactly linear response, and the calibration doesn't force one.
# For many practical purposes this single matrix, applied to input level
# directly, is good enough. The next section quantifies exactly how good.

# %% [markdown]
# ## 4. Comparing the Single Matrix to the Full Model
#
# Both models are on the table now. How much do they actually differ across
# the full range, and how large can that gap get?

# %%
rng = np.random.default_rng(2026)
low_triplets = rng.uniform(0.02, 0.12, size=(1500, 3))
Y_single_low = RGB_to_XYZ_single_matrix(low_triplets, clut)[:, 1]
Y_full_low = RGB_to_XYZ(low_triplets, clut, gamma_correct=True)[:, 1]
ratio_low = np.divide(Y_single_low, np.maximum(Y_full_low, 1e-12))

fig, ax = plt.subplots(1, 2, figsize=(11, 4))

ax[0].plot(gray_levels_full, Y_single_gray, color="tab:blue", label="Single matrix")
ax[0].plot(gray_levels_full, Y_full_gray, color="tab:orange", label="Full model")
ax[0].set_title("Gray-axis Y")
ax[0].set_xlabel("Input level")
ax[0].set_ylabel("Predicted Y")
ax[0].legend()
ax[0].grid(alpha=0.3)

ax[1].hist(ratio_low, bins=45, color="tab:orange", alpha=0.85)
ax[1].axvline(1.0, color="k", linestyle="--", linewidth=1)
ax[1].set_title("Low-input ratio: Y_single / Y_full")
ax[1].set_xlabel("Ratio")
ax[1].set_ylabel("Count")
ax[1].grid(alpha=0.3)

plt.tight_layout()

print(f"Low-input median ratio: {np.median(ratio_low):.3f}x")
print(f"Low-input 90th percentile |ratio - 1|: {np.percentile(np.abs(ratio_low - 1), 90):.3f}")

# %% [markdown]
# So: the single matrix is a solid, cheap approximation. The full per-level
# model remains the more accurate choice whenever the leftover gap matters --
# small/near-threshold contrasts, tight calibration tolerances, or anywhere
# you can't afford a few percent of error. Section 5 comes back to exactly
# this trade-off.

# %% [markdown]
# ## 5. The Inverse Problem: From a Target Chromaticity to RGB
#
# Predicting XYZ from RGB is only half of what you need to calibrate a
# stimulus. The other half is the reverse: "I want this XYZ (or this
# luminance, or this point on a chromaticity axis) on screen -- what RGB do
# I send?"

# %% [markdown]
# ### 5a. Easy Case: A Target Luminance on the Gray Axis
#
# Along the gray axis there's exactly one free parameter, and luminance is
# monotonic in it -- so this inverts directly by interpolation, no search
# needed.

# %%
gray_levels_fine = np.linspace(0.0, 1.0, 4097)
gray_Y_fine = RGB_to_XYZ(
    np.column_stack([gray_levels_fine] * 3), clut, gamma_correct=True
)[:, 1]

print(f"Gray-axis luminance range: [{gray_Y_fine.min():.2f}, {gray_Y_fine.max():.2f}]")

target_Y = 75.0
sort_idx = np.argsort(gray_Y_fine)
solved_level = float(np.interp(target_Y, gray_Y_fine[sort_idx], gray_levels_fine[sort_idx]))
achieved_xyz = RGB_to_XYZ(np.array([solved_level] * 3), clut)[0]

print(f"Target Y = {target_Y}  ->  gray input level = {solved_level:.4f}")
print(f"Achieved XYZ: {achieved_xyz}")

# %% [markdown]
# ### 5b. General Case: An Arbitrary Target XYZ
#
# Off the gray axis, three channels jointly determine XYZ, and (per section
# 3b) the true relationship isn't exactly linear -- so this needs a real
# numerical solve, not a closed form. `XYZ_to_RGB` does exactly this: seed
# from the instant `XYZ_to_RGB_single_matrix` guess, then refine with a few
# Gauss-Newton steps against the exact model (`RGB_to_XYZ`) until the
# residual is small.

# %%
true_rgb_example = np.array([0.6, 0.4, 0.5])
xyz_target = RGB_to_XYZ(true_rgb_example, clut)[0]
print(f"(Demo target, generated from RGB {true_rgb_example} so we know the right answer)")
print(f"xyz_target = {xyz_target}")

initial_guess = XYZ_to_RGB_single_matrix(xyz_target, clut)[0]
print(f"\nInitial guess from single-matrix inverse: {initial_guess}")

solved_rgb = XYZ_to_RGB(xyz_target, clut)[0]
achieved_xyz = RGB_to_XYZ(solved_rgb, clut)[0]
fit_error = float(np.linalg.norm(achieved_xyz - xyz_target))

print(f"Solved RGB (XYZ_to_RGB): {solved_rgb}")
print(f"True RGB:                {true_rgb_example}")
print(f"Fit error (XYZ norm): {fit_error:.2e}")

# %% [markdown]
# Converges to the exact original RGB -- the single-matrix inverse gets you
# close immediately, and the full model cleans up the rest. This -- not a
# linear shortcut -- is the reliable way to hit an arbitrary target
# chromaticity.

# %% [markdown]
# ### 5c. A Blind Spot: Cross-Channel Additivity
#
# Every prediction in this notebook, single-matrix or full-model, computes
# XYZ as a *sum* of three independent per-channel contributions -- there is
# no term for how channels interact when driven together. That's a direct
# consequence of how the underlying measurements were taken: channel by
# channel, in isolation. If this display's channels mix subadditively when
# driven simultaneously (a real phenomenon on some displays, and worth
# checking for gray in particular), neither model here can detect or
# correct for it -- the data to see it was never collected. Verifying that
# requires actual combined-channel measurements, which this CLUT format
# doesn't include.

# %% [markdown]
# ### 5d. Back to the Original Question: Can You Just Rescale?
#
# Section 3 asked for a coordinate where you could just scale by a contrast
# fraction. We got one (input level) that's *close* to linear. Close enough
# to skip solving per point? Test it directly: pick a mean point and
# direction in input-level space, and compare linearly interpolating between
# two endpoints against the true full-model value at the midpoint.

# %%
rng = np.random.default_rng(3)
interp_errors = {}
for max_delta in (0.02, 0.05, 0.1, 0.2, 0.3):
    rel_errs = []
    for _ in range(150):
        mean = rng.uniform(0.3, 0.7, size=3)
        direction = rng.uniform(-1, 1, size=3)
        direction = direction / np.linalg.norm(direction)
        lo = np.clip(mean - max_delta * direction, 0.0, 1.0)
        hi = np.clip(mean + max_delta * direction, 0.0, 1.0)

        xyz_lo = RGB_to_XYZ(lo, clut)[0]
        xyz_hi = RGB_to_XYZ(hi, clut)[0]
        xyz_mid_true = RGB_to_XYZ(mean, clut)[0]
        xyz_mid_linear = 0.5 * (xyz_lo + xyz_hi)

        full_range = abs(xyz_hi[1] - xyz_lo[1])
        if full_range < 0.5:
            continue
        rel_errs.append(abs(xyz_mid_true[1] - xyz_mid_linear[1]) / full_range)
    interp_errors[max_delta] = np.array(rel_errs)

print(f"{'contrast delta':>15}  {'median rel. err':>16}  {'90th pct':>10}")
for max_delta, rel_errs in interp_errors.items():
    print(
        f"{max_delta:15.2f}  {100 * np.median(rel_errs):15.2f}%  "
        f"{100 * np.percentile(rel_errs, 90):9.2f}%"
    )

# %% [markdown]
# So: not free, and not uniform. For large excursions the linear shortcut is
# usually within a couple of percent -- often fine. For small, near-threshold
# contrasts -- exactly where psychophysics tends to need the most
# precision -- the median error climbs to several percent, with a long tail
# well beyond that. Rescaling by a contrast fraction is a reasonable
# *approximation*, with a real, quantifiable error budget; it is not a
# substitute for solving when precision actually matters. Section 5b is the
# reliable version.

# %% [markdown]
# ## 6. Summary / Practical Guidance
#
# 1. **`RGB_to_XYZ(rgb, clut)` / `XYZ_to_RGB(xyz, clut)` are the recommended
#    default** for predicting/solving RGB<->XYZ on a CLUT-characterized
#    display. Both use the full per-level model -- no single-fixed-matrix
#    assumption. `RGB_to_XYZ` also accepts `gamma_correct=False` for a
#    direct lookup when you already have a drive-space signal.
# 2. `RGB_to_XYZ_single_matrix` / `XYZ_to_RGB_single_matrix` are the cheap,
#    closed-form approximation -- good to a few percent on this real CLUT,
#    and what `XYZ_to_RGB` uses internally as a fast starting point. Reach
#    for these directly only when you specifically want the speed and can
#    accept the gap quantified in section 4.
# 3. `gamma_correct_RGB` / `invert_gamma_correct_RGB` convert between input
#    level and drive. Needed to actually send a signal to the display, and
#    to build the linearized coordinate stimulus math wants -- not needed
#    for `RGB_to_XYZ`/`XYZ_to_RGB` themselves, which take input level
#    directly.
# 4. Cross-channel additivity is assumed everywhere in this notebook and
#    verified nowhere -- it's a structural blind spot of channel-isolated
#    CLUT measurements, not something either model can check.
