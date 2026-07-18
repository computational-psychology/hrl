import stimupy

resolution = {
    "visual_size": (10, 20),
    "ppd": 32,
}
target_size = 2


def whites(intensity_target):
    return stimupy.stimuli.whites.white(
        **resolution,
        bar_width=target_size,
        target_indices=(2, -3),
        target_heights=target_size,
        intensity_bars=(0, 1),
        intensity_target=(intensity_target, 1)
    )
