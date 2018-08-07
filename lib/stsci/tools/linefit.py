"""
Fit a line to a data set with optional weights.

Returns the parameters of the model, bo, b1:
Y = b0 + b1* X

:author: Nadia Dencheva
:version: '1.0 (2007-02-20)'

"""
from __future__ import absolute_import, division, print_function

import numpy as N

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
    >>> x = N.array([-5, -4 ,-3 ,-2 ,-1, 0, 1, 2, 3, 4, 5])
    >>> y = N.array([1, 5, 4, 7, 10, 8, 9, 13, 14, 13, 18])
    >>> around(linefit(x,y), decimals=5)
    array([9.27273, 1.43636])
    >>> x = N.array([1.3,1.3,2.0,2.0,2.7,3.3,3.3,3.7,3.7,4.,4.,4.,4.7,4.7,5.,5.3,5.3,5.3,5.7,6.,6.,6.3,6.7])
    >>> y = N.array([2.3,1.8,2.8,1.5,2.2,3.8,1.8,3.7,1.7,2.8,2.8,2.2,3.2,1.9,1.8,3.5,2.8,2.1,3.4,3.2,3.,3.,5.9])
    >>> around(linefit(x,y), decimals=5)
    array([1.42564, 0.31579])
    """
    if len(x) != len(y):
        print("Error: X and Y must have equal size\n")
        return
    n = len(x)
    w = N.zeros((n,n)).astype(N.float)
    if weights is None:
        for i in N.arange(n):
            w[i,i] = 1
    else:
        if len(weights) != n:
            print("Error: Weights must have the same size as X and Y.\n")
            return
        for i in N.arange(n):
            w[i,i] = weights[i]
    x = x.astype(N.float)
    y = y.astype(N.float)
    # take the weighted avg for calculatiing the covarince
    Xavg = N.sum(N.dot(w,x)) / N.sum(w.diagonal())
    Yavg = N.sum(N.dot(w,y)) / N.sum(w.diagonal())

    xm = x - Xavg
    xmt = N.transpose(xm)
    ym = y - Yavg

    b1 = N.dot(xmt,N.dot(w,ym)) / N.dot(xmt ,N.dot(w,xm))
    b0 = Yavg - b1 * Xavg

    return b0, b1
