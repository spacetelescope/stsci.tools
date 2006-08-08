"""
Program: numerixclass.py
Author: Christopher Hanley
Purpose:

This class is used to provide a common interface to the numpy and numarray
array packages.  The numerix interface is designed to match the numpy
interface.  Python "properties" are used to make numarray calls with 
numpy syntax in the numerix interface.

"""

import os

__version__ = '0.1'

# Check the environment variables for NUMERIX
try:
    numerix = os.environ["NUMERIX"]
except:
    numerix = 'numarray'

if numerix == 'numpy':
    import numpy
    class numerix(numpy.ndarray):
        pass
else:
    import numarray
    class numerix(numarray.numarraycore.NumArray):
        def get_itemsize(self):
            return self.dtype.itemsize
        
        itemsize = property(get_itemsize,None,None,"The size of the array elements in bytes.")
        def get_size_of_arrray(self):
            return self.nelements()
        
        size = property(get_size_of_arrray,None,None,"The number of elements in the array.")

        