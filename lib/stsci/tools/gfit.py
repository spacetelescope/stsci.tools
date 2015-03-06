"""
Return the gaussian fit of a 1D array.

Uses mpfit.py - a python implementation of the Levenberg-Marquardt
least-squares minimization, based on MINPACK-1. See nmpfit.py for
the history of this module (fortran -> idl -> python).
nmpfit.py is a version of mpfit.py which uses numarray.

@author: Nadia Dencheva
@version: '1.0 (2007-02-20)'

"""
from __future__ import division, print_function # confidence high

__version__ = '1.0'          #Release version number only
__vdate__ = '2007-02-20'     #Date of this version

import numerixenv
numerixenv.check()

import nmpfit
import numpy as N
from numpy import random

def _gauss_funct(p, fjac = None, x = None, y=None, err=None,
weights=None):

    """
    Defines the gaussian function to be used as the model.

    """

    if p[2] != 0.0:
        Z = (x - p[1]) / p[2]
        model = p[0]*N.e ** (-Z**2 / 2.0)
    else:
        model = N.zeros(N.size(x))


    status = 0
    if weights != None:
        if err != None:
            print("Warning: Ignoring errors and using weights.\n")
        return [status, (y - model) * weights]
    elif err != None:
        return [status, (y - model) / err]
    else:
        return [status, y-model]

def test_gaussfit():
    x=N.arange(10,20, 0.1)
    #x1=N.arange(0,10,0.1)
    #y1=5*N.e**(-(5-x1)**2/4)
    n=random.randn(100)
    y= 10*N.e**(-(15-x)**2/4) +n*3
    #x=N.arange(100, typecode=N.Int)
    #y=n.zeros(10, typecode=n.Float)
    #y= random.rand(100)
    #err = N.zeros(100)
    #return gaussfit(x,y, maxiter=20) #, x,y, n
    return gfit1d(y,x, maxiter=20)

def gfit1d(y, x=None, err = None, weights=None, par=None, parinfo=None,
maxiter=200, quiet=0):
    """
    Return the gaussian fit as an object.

    Parameters
    ----------
    y:   1D Numarray array
        The data to be fitted
    x:   1D Numarray array
        (optional) The x values of the y array. x and y must
        have the same shape.
    err: 1D Numarray array
        (optional) 1D array with measurement errors, must be
        the same shape as y
    weights: 1D Numarray array
        (optiional) 1D array with weights, must be the same
        shape as y
    par:  List
        (optional) Starting values for the parameters to be fitted
    parinfo: Dictionary of lists
        (optional) provides additional information for the
        parameters. For a detailed description see nmpfit.py.
        Parinfo can be used to limit parameters or keep
        some of them fixed.
    maxiter: number
        Maximum number of iterations to perform
        Default: 200
    quiet: number
        if set to 1, nmpfit does not print to the screen
        Default: 0

    Examples
    --------
    >>> x=N.arange(10,20, 0.1)
    >>> y= 10*N.e**(-(x-15)**2/4)
    >>> print gfit1d(y,x=x, maxiter=20,quiet=1).params
    [ 10.          15.           1.41421356]

    """
    if numerixenv.check_input(x) or numerixenv.check_input(y):
        raise ValueError("Input is a NumArray array. This version of %s requires a Numpy array\n" % __name__)
    
    y = y.astype(N.float)
    if weights != None:
        weights = weights.astype(N.float)
    if err != None:
        err = err.astype(N.float)
    if x == None and len(y.shape)==1 :
        x = N.arange(len(y)).astype(N.float)
    if x.shape != y.shape:
        print("input arrays X and Y must be of equal shape.\n")
        return


    fa = {'x':x, 'y':y, 'err':err, 'weights':weights}

    if par != None:
        p = par
    else:
        ysigma = y.std()
        ind = N.nonzero(y > ysigma)[0]
        if len(ind) != 0:
            xind = int(ind.mean())
            p2 = x[xind]
            p1 = y[xind]
            p3 = 1.0
        else:
            ymax = y.max()
            ymin = y.min()
            ymean= y.mean()
            if (ymax - ymean) > (abs(ymin - ymean)):
                p1 = ymax
            else: p1 = ymin
            ind = (N.nonzero(y == p1))[0]
            p2 = x.mean()
            p3 = 1.


        p = [p1, p2, p3]
    m=nmpfit.mpfit(_gauss_funct, p,parinfo = parinfo, functkw=fa,
maxiter=maxiter, quiet=quiet)
    if (m.status <=0): print('error message = ', m.errmsg)
    return m


def plot_fit(y, mfit, x=None):
    if x == None:
        x=N.arange(len(y))
    else:
        x = x
    p = mfit.params
    #y = gauss_funct(p, y)
    yy = p[0] + N.e**(-0.5*(x-p[1])**2/p[2]**2)
    try:
        import pylab
    except ImportError:
        print("Matplotlib is not available.\n")
        return
    pylab.plot(x,yy)

def test():
    import doctest
    import gfit
    return doctest.testmod(gfit)
