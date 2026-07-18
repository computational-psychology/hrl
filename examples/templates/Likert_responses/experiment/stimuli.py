from copy import deepcopy

import numpy as np
import stimupy

target_size = 1

visual_size = np.array((5, 10)) * target_size

resolution = {
    "visual_size": visual_size,
    "ppd": 32,
}

intensity_background = 0.3


# Initialize empty dict to hold all stims
stims = {}


# -------------------------- #
# %%      BULLSEYE           #
# -------------------------- #
# Low freq
radii = np.array([0.5, 1.5, 2.5]) * target_size
left = stimupy.stimuli.rings.rectangular_generalized(
    ppd=resolution["ppd"],
    visual_size=(resolution["visual_size"][0], resolution["visual_size"][1] / 2),
    radii=radii,
    target_indices=1,
    intensity_frames=(1, 0),
)
right = stimupy.stimuli.rings.rectangular_generalized(
    ppd=resolution["ppd"],
    visual_size=(resolution["visual_size"][0], resolution["visual_size"][1] / 2),
    radii=radii,
    target_indices=1,
    intensity_frames=(0, 1),
)
stims["bullseye"] = stimupy.utils.stack_dicts(left, right, direction="horizontal")

# High-freq, extended
bullseye_hfe = stimupy.stimuli.bullseyes.rectangular_two_sided(
    **resolution, frame_width=target_size / 2, intensity_frames=((0.0, 1.0), (1.0, 0.0))
)
stims["bullseye, high freq extended"] = bullseye_hfe

# Mask separation frame
separate_mask = np.where(bullseye_hfe["grating_mask"] == 2, 1, 0)
separate_mask = np.where(bullseye_hfe["grating_mask"] == 3, 1, separate_mask)
separate_mask = np.where(bullseye_hfe["grating_mask"] == 7, 1, separate_mask)
separate_mask = np.where(bullseye_hfe["grating_mask"] == 8, 1, separate_mask)
separate_mask = np.where(bullseye_hfe["target_mask"], 1, separate_mask)

# High-freq, separated
stims["bullseye, high freq"] = deepcopy(stims["bullseye, high freq extended"])
stims["bullseye, high freq"]["img"] = np.where(
    separate_mask, stims["bullseye, high freq"]["img"], intensity_background
)

# Mask inner frame
frame_mask = np.where(bullseye_hfe["grating_mask"] == 2, 1, 0)
frame_mask = np.where(bullseye_hfe["grating_mask"] == 7, 1, frame_mask)
frame_mask = np.where(bullseye_hfe["target_mask"], 1, frame_mask)


# -------------------------- #
# %%         SBC             #
# -------------------------- #
stims["sbc"] = stimupy.stimuli.sbcs.basic_two_sided(
    **resolution, target_size=target_size, intensity_background=(0.0, 1.0)
)

# separated
sbc_separate = deepcopy(stims["bullseye"])
sbc_separate["img"] = np.where(separate_mask, sbc_separate["img"], intensity_background)
stims["sbc, separate"] = sbc_separate

# smallest
sbc_smallest = deepcopy(stims["bullseye, high freq extended"])
sbc_smallest["img"] = np.where(frame_mask, sbc_smallest["img"], intensity_background)
stims["sbc, smallest"] = sbc_smallest


# -------------------------- #
# %%       WHITE'S           #
# -------------------------- #
whites = {
    "whites, high freq": stimupy.stimuli.whites.white(
        **resolution,
        bar_width=target_size / 2,
        target_indices=(4, -5),
        target_heights=target_size,
        intensity_bars=(0, 1)
    ),
    "whites, high freq, equal aspect": stimupy.stimuli.whites.white(
        **resolution,
        bar_width=target_size / 2,
        target_indices=(4, -5),
        target_heights=target_size / 2,
        intensity_bars=(0, 1)
    ),
    "whites": stimupy.stimuli.whites.white(
        **resolution,
        bar_width=target_size,
        target_indices=(3, -2),
        target_heights=target_size,
        intensity_bars=(0, 1)
    ),
    "whites, narrow": stimupy.stimuli.whites.white(
        ppd=resolution["ppd"],
        visual_size=(3 * target_size, resolution["visual_size"][1]),
        bar_width=target_size,
        target_indices=(3, -2),
        target_heights=target_size,
        intensity_bars=(0, 1),
    ),
}
whites["whites, narrow"] = stimupy.utils.pad_dict_to_visual_size(
    dct=whites["whites, narrow"], **resolution, pad_value=intensity_background
)

whites["whites, separate"] = deepcopy(whites["whites, narrow"])
whites["whites, separate"]["img"] = np.where(
    separate_mask, whites["whites, separate"]["img"], intensity_background
)

stims = {**stims, **whites}

# -------------------------- #
# %%        STRIP            #
# -------------------------- #
stims["strip"] = stimupy.stimuli.whites.white(
    ppd=resolution["ppd"],
    visual_size=(target_size, resolution["visual_size"][1]),
    bar_width=target_size,
    target_indices=(3, -2),
    target_heights=target_size,
    intensity_bars=(1, 0),
)
stims["strip"] = stimupy.utils.pad_dict_to_visual_size(
    dct=stims["strip"], **resolution, pad_value=intensity_background
)


# -------------------------- #
# %%    CHECKERBOARDS        #
# -------------------------- #
checkerboards = {
    "checkerboard": stimupy.stimuli.checkerboards.checkerboard(
        **resolution,
        check_visual_size=target_size,
        target_indices=((2, 2), (2, 7)),
        intensity_checks=(1, 0)
    ),
    "checkerboard, narrow": stimupy.stimuli.checkerboards.checkerboard(
        ppd=resolution["ppd"],
        visual_size=(3 * target_size, resolution["visual_size"][1]),
        check_visual_size=target_size,
        target_indices=((1, 2), (1, 7)),
    ),
}
checkerboards["checkerboard, narrow"] = stimupy.utils.pad_dict_to_visual_size(
    dct=checkerboards["checkerboard, narrow"], **resolution, pad_value=intensity_background
)

checkerboards["checkerboard, separate"] = deepcopy(checkerboards["checkerboard, narrow"])
checkerboards["checkerboard, separate"]["img"] = np.where(
    separate_mask, checkerboards["checkerboard, separate"]["img"], intensity_background
)

stims = {**stims, **checkerboards}
