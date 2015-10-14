from __future__ import division # confidence medium
import os

def check_input(xxx):
    """Check if input is a Numarray Array."""
    try:
        import numarray
        return isinstance(xxx,numarray.numarraycore.NumArray)    
    except ImportError:
        pass

def check():
    """Check for running numarray version of pyfits with numpy code."""
    pass

    

