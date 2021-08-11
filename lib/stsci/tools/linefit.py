"""
Fit a line to a data set with optional weights.

Returns the parameters of the model, bo, b1:
Y = b0 + b1* X

:author: Nadia Dencheva
:version: '1.0 (2007-02-20)'

"""
import numpy as np

__version__ = '1.0'          # Release version number only
__vdate__ = '2007-02-20'     # Date of this version


def linefit(x, y, weights=None):

    """
    Parameters
    ----------
    y: 1D numpy array
        The data to be fitted
    x: 1D numpy array
        The x values of the y array. x and y must
        have the same shape.
    weights:   1D numpy array, must have the same shape as x and y
        weight values

    Examples
    --------
    >>> import numpy as N
    >>> from numpy.core import around
    >>> x = np.array([-5, -4 ,-3 ,-2 ,-1, 0, 1, 2, 3, 4, 5])
    >>> y = np.array([1, 5, 4, 7, 10, 8, 9, 13, 14, 13, 18])
    >>> around(linefit(x,y), decimals=5)
    array([9.27273, 1.43636])
    >>> x = np.array([1.3,1.3,2.0,2.0,2.7,3.3,3.3,3.7,3.7,4.,4.,4.,4.7,4.7,5.,5.3,5.3,5.3,5.7,6.,6.,6.3,6.7])
    >>> y = np.array([2.3,1.8,2.8,1.5,2.2,3.8,1.8,3.7,1.7,2.8,2.8,2.2,3.2,1.9,1.8,3.5,2.8,2.1,3.4,3.2,3.,3.,5.9])
    >>> around(linefit(x,y), decimals=5)
    array([1.42564, 0.31579])
    """
    if len(x) != len(y):
        print("Error: X and Y must have equal size\n")
        return
    n = len(x)
    w = np.zeros((n,n)).astype(float)
    if weights is None:
        for i in np.arange(n):
            w[i,i] = 1
    else:
        if len(weights) != n:
            print("Error: Weights must have the same size as X and Y.\n")
            return
        for i in np.arange(n):
            w[i,i] = weights[i]
    x = x.astype(float)
    y = y.astype(float)
    # take the weighted avg for calculatiing the covarince
    Xavg = np.sum(np.dot(w,x)) / np.sum(w.diagonal())
    Yavg = np.sum(np.dot(w,y)) / np.sum(w.diagonal())

    xm = x - Xavg
    xmt = np.transpose(xm)
    ym = y - Yavg

    b1 = np.dot(xmt,np.dot(w,ym)) / np.dot(xmt ,np.dot(w,xm))
    b0 = Yavg - b1 * Xavg

    return b0, b1
