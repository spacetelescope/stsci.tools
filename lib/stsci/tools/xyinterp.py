"""
:Module: xyinterp.py

Interpolates y based on the given xval.

`x` and `y` are a pair of independent/dependent variable arrays that must
be the same length. The x array must also be sorted.
`xval` is a user-specified value. This routine looks
up `xval` in the x array and uses that information to properly interpolate
the value in the y array. 


:author: Vicki Laidler

:version: '0.1 (2006-07-06)'  


"""
from __future__ import division # confidence high
import numpy as N 

#This section for standalone imports only-------------------------------------
__version__ = '0.1'          #Release version number only
__vdate__ = '2006-07-06'     #Date of this version, in this (FITS-style) format
#-----------------------------------------------------------------------------


def xyinterp(x,y,xval):
    """ 
    
    :Purpose: Interpolates y based on the given xval.

    x and y are a pair of independent/dependent variable arrays that must
    be the same length. The x array must also be sorted.
    xval is a user-specified value. This routine looks
    up xval in the x array and uses that information to properly interpolate
    the value in the y array.  

    Notes
    =====
    Use the searchsorted method on the X array to determine the bin in
    which xval falls; then use that information to compute the corresponding
    y value.
    

    See Also 
    ========
    numpy

    Parameters
    ==========

    x: 1D numpy array  
        independent variable array: MUST BE SORTED

    y: 1D numpy array
        dependent variable array

    xval: float 
        the x value at which you want to know the value of y

    Returns
    =======
    y: float 
        the value of y corresponding to xval

    Raises
    ======
    ValueError: 
        If arrays are unequal length; or x array is unsorted;
        or if xval falls outside the bounds of x (extrapolation is unsupported

    :version: 0.1 last modified 2006-07-06

"""

    #Enforce conditions on x, y, and xval:
    #x and y must correspond
    if len(x) != len(y):
        raise ValueError("Input arrays must be equal lengths")

    #Extrapolation not supported
    if xval < x[0]:
        raise ValueError("Value %f < min(x) %f: Extrapolation unsupported"%(xval,x[0]))
    if xval > x[-1]:
        raise ValueError("Value > max(x): Extrapolation unsupported")

    #This algorithm only works on sorted data
    if x.argsort().all() != N.arange(len(x)).all():
        raise ValueError("Input array x must be sorted")
    
    # Now do the real work.
    hi = x.searchsorted(xval)
    lo = hi - 1
    
    try:
        seg = (float(xval)-x[lo]) / (x[hi] - x[lo])
    except ZeroDivisionError:
        seg = 0.0

    yval = y[lo] + seg*(y[hi] - y[lo])
    return yval
