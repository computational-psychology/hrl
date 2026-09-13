import stimupy

resolution = {
    "visual_size": (10, 20),
    "ppd": 32,
}

target_size = resolution["visual_size"][1] / 10

intensity_background = 0.3

__all__ = ["whites"]


# # %% SBC
# def sbc(intensity_target, target_side):
#     return stimupy.stimuli.sbcs.two_sided(
#         **resolution,
#         target_size=target_size,
#         intensity_target=intensity_target,
#         intensity_backgrounds=(0.0, 1.0)
#     )


# %% WHITE'S
def whites(intensity_target, target_side, intensity_match):
    if target_side == "Left":
        intensities = (intensity_target, intensity_match)
    elif target_side == "Right":
        intensities = (intensity_match, intensity_target)

    return stimupy.stimuli.whites.white(
        **resolution,
        bar_width=target_size,
        target_indices=(3, -2),
        target_heights=target_size,
        intensity_bars=(0.0, 1.0),
        intensity_target=intensities
    )
