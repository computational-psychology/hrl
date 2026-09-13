import stimupy

resolution = {
    "visual_size": (10, 20),
    "ppd": 32,
}

target_size = resolution["visual_size"][1] / 10

intensity_background = 0.3

__all__ = ["sbc", "whites"]


# %% SBC
def sbc(intensity_target, intensity_left, intensity_right):
    return stimupy.stimuli.sbcs.basic_two_sided(
        **resolution,
        target_size=target_size,
        intensity_target=intensity_target,
        intensity_background=(intensity_left, intensity_right)
    )


# %% WHITE'S
def whites(intensity_target, intensity_left, intensity_right):
    return stimupy.stimuli.whites.white(
        **resolution,
        bar_width=target_size,
        target_indices=(2, -3),
        target_heights=target_size,
        intensity_bars=(intensity_left, intensity_right),
        intensity_target=intensity_target
    )
