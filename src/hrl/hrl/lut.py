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

def gprocessTable(tbl='average.txt',ss=4000,mnns=0.2,mxns=4,L=0.05,wfl='fit.txt'):
    """
    ***
    Right now it is recommended to use sprocessTable as gprocessTable is too
    difficult to use, and really isn't particularly well designed for this
    task. However, for now this code should be left here, in case we ever need
    it. There are models which apparently force monotonic regressions which
    would probably get this thing working well.
    ***

    This function uses a Gaussian process model to fit the gamma funciton.

    Since the dataset of 2^16 values is generally too large to run a complete
    Gaussian process on, this function breaks the dataset up into a set of
    regions ss (subsample) values long. We then build a set of overlapping
    gaussian process models, (up to two per input intensity) and average them
    at a point to get the estimation. If subsample is larger than the size of
    the dataset, then a normal, complete gaussian process model is fit.

    gprocessTable then samples this predicted function with 2**16
    values, and saves it to a file.  This file can then be read by hrl to
    linearize the gamma function.

    So that all the divisions in the algorithm are without remainder, it's
    advisable that ss be made divisible by 2.

    mnns and mxns are the minimum and maximum noise variance expected over the
    data set. These don't have to be exact, but they may improve the quality of the
    results.
    """
    if type(tbl) == str: tbl = np.genfromtxt(tbl,skip_header=1)
    xsmps = tbl[:,0]
    ysmps = tbl[:,1]
    xs = np.linspace(0,1,2**16)

    ss = len(tbl)

    if ss >= len(tbl):

        #print 'Sample size is larger than or equal to the number of data points.\r\n'
        print 'Generating complete prediction function...'
        fun = predictor(xsmps,ysmps,(mnns + mxns)/2.0,L)

        print 'Sampling Prediction Function... (this may take a while)...'
        rslts = [ [x] + list(fun(x)) for x in xs ]

    else:

        print 'Sample size is less than the number of data points.\r\n'
        hss = ss//2
        n = len(tbl)//ss
        stps = 2*n
        nss = np.linspace(mnns,mxns,stps)

        print 'Step 1' + ' of ' + str(stps)
        print 'Building Prediction Function...'

        predfun = predictor(xsmps[0:ss],ysmps[0:ss],nss[0],L)

        print 'Sampling Prediction Function...'

        mx = xsmps[hss]
        rslts = [ ([x] + list(predfun(x))) for x in xs[xs <= mx] ]

        print 'Example Intensity: ' + str(rslts[-1][0]) + ', Predicted Luminance: ' + str(rslts[-1][1])
        # + ', Variance: ' + str(rslts[-1][2]) <- add this to display variance

        for i in range(1,stps):

            print 'Step ' + str(i+1) + ' of ' + str(stps)
            print 'Building Prediction Function...'
            stp = hss*i
            mn = xsmps[stp]

            if i == stps-1:
                mx = 1.0
                predfun = predictor(xsmps[stp-hss:],ysmps[stp-hss:],nss[i],L)
            else:
                mx = xsmps[stp + hss]
                predfun = predictor(xsmps[stp-hss:stp+ss],ysmps[stp-hss:stp+ss],nss[i],L)

            print 'Sampling Prediction Function...'

            rslts += [ [x] + predfun(x) for x in xs[xs[xs <= mx] > mn] ]

            print 'Example Intensity: ' + str(rslts[-1][0]) + ', Predicted Luminance: ' + str(rslts[-1][1])

    print 'Saving to File...'
    rslt = np.array(rslts)
    ofl = open(wfl,'w')
    ofl.write('Input Luminance Variance\r\n')
    np.savetxt(ofl,rslt)
    ofl.close()

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


### Gaussian Process Functions ###


def predictor(xsmps,ysmps,sg,L,meanBool=True,varBool=False):
    """
    Returns a function for calculating an estimated y from a given x and its
    variance. Takes optional boolean arguments - meanBool, varBool - indicating
    which of the mean and variance of the process one wishes to calculate.
    """
    funs = []
    kmtx = kernelMatrix(xsmps,L)
    inv = (kmtx + sg * np.eye(len(ysmps))).I

    if meanBool:
        funs.append(lambda x: (kernelColumn(x,xsmps,L).T * inv * np.matrix(ysmps).T)[0,0])
    if varBool:
        funs.append(lambda x: rbfKernel(x,x,L) - (kernelColumn(x,xsmps,L).T * inv *
                                                kernelColumn(x,xsmps,L))[0,0])

    return lambda x: [ fun(x) for fun in funs ]

def kernelMatrix(xsmps,L):
    return np.matrix([ [ rbfKernel(ixsmp,jxsmp,L) for jxsmp in xsmps ] for ixsmp in xsmps ])

def kernelColumn(x,xsmps,L):
    krn = np.vectorize(lambda y: rbfKernel(x,y,L))
    return np.matrix(krn(xsmps)).T

def rbfKernel(x1,x2,L):
    return np.exp((-(x1 - x2)**2)/(2*L**2))
