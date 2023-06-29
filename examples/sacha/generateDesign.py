import numpy as np
import random as r


def makeLine(mns, ivl, rad, frm):
    ivl = r.choice([ivl / 2, -ivl / 2])
    return [mns - ivl, mns + ivl, rad, frm]


def generateDesign(mnslvls, ivllvls, rad, frm, trls):
    dsgn = [
        makeLine(mns, ivl, rad, frm) for mns in mnslvls for ivl in ivllvls for i in range(trls)
    ]
    r.shuffle(dsgn)
    ofl = open("design.csv", "w")
    ofl.write("LeftMunsell RightMunsell Radius FramePresent\r\n")
    np.savetxt(ofl, np.array(dsgn))
    ofl.close()
