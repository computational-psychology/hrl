import stimupy
import itertools

resolution = {
    "visual_size": (8, 8),
    "ppd": 48,
}

target_size = resolution["visual_size"][1] / 3

# %% SBC
def sbc(intensity_target, intensity_background):
    return stimupy.stimuli.sbcs.basic(
        **resolution,
        target_size=target_size,
        intensity_target=intensity_target,
        intensity_background=intensity_background,
    )


# %% SBC circular
def sbc_circular(intensity_target, intensity_background, bg):
    return stimupy.bullseyes.circular(
        **resolution,
        intensity_target=intensity_target,
        intensity_background=bg,
        intensity_rings=[intensity_background,intensity_background,intensity_background],
        n_rings = 3,
    )



if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import numpy as np
    from design import luminances
    
    luminances = np.array(luminances)**(1.0)
    
    stim_set = list(itertools.combinations(luminances, 3))
    
    s = 8 # panel size
    
    fig, axes = plt.subplots(1, len(luminances), figsize=(s*len(luminances), s))  
    for j, t in enumerate(luminances):
        im = sbc_circular(t, intensity_background=0.5, bg=0.5)
        axes[j].imshow(im['img'], cmap='gray', vmin=0, vmax=1.0, aspect='equal')
        axes[j].set_axis_off()
          
    fig.patch.set_facecolor([0.5, 0.5, 0.5])
    plt.tight_layout(h_pad=5, w_pad=5)
    fig.savefig('../stimuli.pdf')
    #plt.show()
