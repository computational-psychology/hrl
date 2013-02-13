import pyoptical as pop

def initializeOptiCAL(dev,timeout=5):
    return pop.OptiCAL(dev,timeout=timeout)

def tryReadLuminance(phtm,trs,slptm):
    """ Note that reading the optiCAL ocassionally fails. It's worth
    testing a few times. """
    for n in range(trs):
        try: 
            pg.time.delay(slptm)
            lm = phtm.read_luminance()
            print 'Recorded Luminance:',lm
            return lm
        except:
            print 'error while reading OptiCAL' 

    return np.nan


