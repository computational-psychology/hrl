import numpy as np
import stimupy

# Defaults
TARGET_SIZE = 2  # deg. visual angle, bounding square size
PPD = 48  # default on our ViewPixx setup

INTENSITY_BACKGROUND = 0.3


# %% SBC circular
def sbc(
    ppd=PPD,
    intensity_targets=(0.5, 0.5),
    intensity_contexts=(0.0, 1.0),
    target_size=TARGET_SIZE,
    intensity_background=INTENSITY_BACKGROUND,
):
    visual_size = np.array((7, 10)) * target_size

    return stimupy.stimuli.sbcs.circular_two_sided(
        ppd=ppd,
        visual_size=visual_size,
        target_radius=target_size / 2,
        surround_radius=target_size,
        intensity_target=intensity_targets,
        intensity_surround=intensity_contexts,
        intensity_background=intensity_background,
    )


if __name__ == "__main__":
    stim = sbc(intensity_contexts=(0.0, 1.0))

    stimupy.utils.plot_stim(stim)
