import numpy as np
import pylab as plt
import scipy as sp

"""
In order to build a look up table, perform the following steps:

    filesToTable(filenames) -> (produces 'average.txt')
    *processTable() -> (takes 'average.txt' and produces 'fit.txt')
    interpLUT() -> (takes 'fit.txt' and produces 'lut.txt')

Each of these functions will save their results to files, and lut.txt can then be
given to hrl to correct textures at load time.

*processTable can either be gprocessTable for the gaussian process fit, whereas
sprocessTable uses a simpler smoothing technique. gprocessTable is more
general, and can work well with small datasets, but is sensitive to its
parameters, and takes a long time to run. Datasets of more than 4000 points are
not recommended.

sprocessTable simply averages nearby values with a sliding window.
sprocessTable is generally more advisable than gprocessTable at this point, as
its much easier to use. The quality of the fit is proportional to the data set,
so it is especially recommended to use sprocessTable when the data set is
large.

The following functions are available for plotting the results of the various
stages of LUT creation (these do not call plt.show on their own):

    plotFit()
    plotLUT() takes lut.txt and plots it on to average.txt 
"""


### Plotting Functions ###


def plotFit(avgfl="average.txt",fitfl="fit.txt"):
    """
    This function takes the averaged data, the generated lookup table, and plots them to
    see the quality of the fit.
    """
    avg = np.genfromtxt(avgfl,skip_header=1)
    fit = np.genfromtxt(fitfl,skip_header=1)
    plt.plot(avg[:,0],avg[:,1])
    plt.plot(fit[:,0],fit[:,1])
    plt.xlabel('Intensity')
    plt.ylabel('Luminance')
    plt.title('Fit')
    plt.legend(['Empirical Average','Fit'])
    #plt.plot(fit[:,0],fit[:,1]-np.sqrt(fit[:,2]))
    #plt.plot(fit[:,0],fit[:,1]+np.sqrt(fit[:,2]))

    plt.show()

def plotLUT(lutfl="lut.txt"):
    """
    This function takes the lookup table data and plots it to to depict the results of the
    correction.
    """
    lut = np.genfromtxt(lutfl,skip_header=1)

    plt.figure(1)
    
    plt.subplot(211)
    plt.plot(lut[:,0],lut[:,0])
    plt.plot(lut[:,0],lut[:,1])
    plt.xlabel('Input Intensity')
    plt.ylabel('Output Intensity')
    plt.title('Corrected Intensity')
    plt.legend(['Original','Corrected'],loc='upper left')

    plt.subplot(212)
    plt.plot(lut[:,1],lut[:,2])
    plt.plot(lut[:,0],lut[:,2])
    plt.xlabel('Input Intensity')
    plt.ylabel('Luminance')
    plt.title('Corrected Luminance')
    plt.legend(['Original','Corrected'],loc='upper left')
 
    plt.show()



### Lookup Table Functions ###


def filesToTable(fls,wfl='average.txt'):
    """
    This is the first step of preparing a lookup table. Here we gather
    together a set of csvs of luminance measurements into one array,
    clear out useless rows, and average points at the same intensity.

    This returns a two column array with a number of elements derived
    from the csv file, i.e. a bit less than 2^16. This array can then be
    sampled by interpLUT right away producing a very rough
    linearization, or it can be fed into gprocessTable, which fits the
    data set using a Gaussian process model, which can then be fed into
    interpLUT.
    """
    hshmp = {}
    if type(fls) == str: fls = [fls]
    tbls = [ np.genfromtxt(fl,skip_header=1) for fl in fls ]
    # First we build up a big intensity to luminance map
    for tbl in tbls:
        for rw in tbl:
            if hshmp.has_key(rw[0]):
                hshmp[rw[0]] = np.concatenate([hshmp[rw[0]],rw[1:]])
            else:
                hshmp[rw[0]] = rw[1:]
    # Now we average the values, clearing all nans from the picture.
    for ky in hshmp.keys():
        hshmp[ky] = np.mean(hshmp[ky][np.isnan(hshmp[ky]) == False])
        if np.isnan(hshmp[ky]): hshmp.pop(ky)
    tbl = np.array([hshmp.keys(),hshmp.values()]).transpose()
    tbl = tbl[tbl[:,0].argsort()]
    ofl = open(wfl,'w')
    ofl.write('Intensity Luminance\r\n')
    np.savetxt(ofl,tbl)
    ofl.close()
    #return tbl[tbl[:,0].argsort()]

def sprocessTable(tbl='average.txt',krn=[0.2,0.2,0.2,0.2,0.2],ordr=5,corr=20,wfl='fit.txt'):
    """
    This function uses a simple smoothing kernel to fit the gamma function.
    Since this smoothing will scale down the entire function, sprocess then
    rescales the function back within its original values. This should be safe
    as gamma function is quite close to an exponential at these values, and so is
    relatively scale invariant.

    A critical part of applying this function is to make sure that the data set
    has been evenly sampled across the intensity range, as internally the
    algorithm has no idea how far apart in intensity each sample is, and
    implicitly assumes each step size to be the same.

    Parameters:

    krn - The smoothing kernel. Default: [0.2,0.2,0.2,0.2,0.2]
    ordr - The number of times to smooth the data. Default: 5
    corr - The number of points at the end of the dataset used to estimate
        the scaling factor.
    """
    if type(tbl) == str: tbl = np.genfromtxt(tbl,skip_header=1)
    xsmps = tbl[:,0]
    ysmps = tbl[:,1]
    smthd = ysmps

    for i in range(ordr): smthd = sp.convolve(smthd,krn)
    smthd = smthd[:len(ysmps)]
    mn = min(ysmps)
    def fun(x):
        if x < mn:
            return mn
        else:
            return x
    smthd = map(fun,smthd)
    smthd *= 1 + (np.mean(ysmps[-corr:]) - np.mean(smthd[-corr:]))/np.mean(smthd[-corr:])

    print 'Saving to File...'
    rslt = np.array([xsmps,smthd]).transpose()
    ofl = open(wfl,'w')
    ofl.write('Input Luminance\r\n')
    np.savetxt(ofl,rslt)
    ofl.close()


def interpLUT(tbl='fit.txt',wfl='lut.txt',res=12):
    """
    This function takes a cleaned (i.e. by filesToTable and/or
    gprocessLUT) gamma measurement table (this can also can be given a
    file which corresponds to an appropriate table)  and linearly
    subsamples it at a given resolution so that the luminances are
    roughly evenly spaced across indicies.

    interpLUT will return a function based on numpy.interp
    which takes intensities from 0 to 1, and returns linearized
    intensities.
    """
    # Sample a linear subset of the gamma table
    tbl = np.genfromtxt(tbl,skip_header=1)
    idx = 0
    idxs = []
    itss = tbl[:,0]
    lmns = tbl[:,1]
    for smp in np.linspace(np.min(lmns),np.max(lmns),2**res):
        #while smp > lmns[idx]: idx += 1
        idx = np.nonzero(lmns >= smp)[0][0]
        idxs.append(idx)
    ofl = open(wfl,'w')
    ofl.write('IntensityIn IntensityOut Luminance\r\n')
    rslt = np.array([np.linspace(0,1,2**res),itss[idxs],lmns[idxs]]).transpose()
    np.savetxt(ofl,rslt)
    ofl.close()
    #return lambda x: np.interp(x,np.linspace(0,1,2**res),itss[idxs])
