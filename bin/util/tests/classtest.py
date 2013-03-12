from hrl import HRL

import numpy as np

hrl = HRL(bg=0.5)
txt = hrl.graphics.newTexture(np.array([[1]]))
txt.draw((200,200),(200,200))
hrl.graphics.flip()

for btn in ['Left','Right','Up','Down','Space']:

    print('Please press ' + btn)
    (foo,t) = hrl.inputs.readButton(btns=[btn])
    print('Time taken: ' + str(t))


