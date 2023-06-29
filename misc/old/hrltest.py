from hrl import *
import numpy as np
import Image as im


fl = "data/cow.png"
pic = im.open(fl)
div = 255.0
pix = np.array(pic.getdata()).reshape(pic.size[0], pic.size[1], 4)
gar = np.mean(pix[:, :, :3], 2) / div

hrl = HRL()
hrl = HRL(coords=(-0.5, 0.5, -0.5, 0.5), flipcoords=False)
txt = hrl.newTexture(
    np.array([[x + y for x in np.linspace(0, 0.25, 10)] for y in np.linspace(0, 0.75, 10)])
)
# txt = hrl.newTexture(gar)
txt.draw((0, 0), (300, 300))
hrl.flip()
