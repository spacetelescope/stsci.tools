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

import inspect

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
        def factory(self,*args,**keywords):
            import numerix
            return numerix.array(*args,**keywords)
            
        def reshape(self, newshape):
            return numarray.reshape(self, newshape)

        def ItemSizeMethod(self):
            return numarray.NDArray.itemsize(self)

        def get_itemsize(self):
            frame = inspect.currentframe()
            callingframe = frame.f_back
            valuelist = callingframe.f_globals.values()
            numArrMode = False
            for item in valuelist:
                if type(item) is type(numarray):
                    if item is numarray:
                        numArrMode = True
            if (numArrMode):
                return self.ItemSizeMethod
            else:
                return self.dtype.itemsize
                
        itemsize = property(get_itemsize,None,None,"The size of the array elements in bytes.")
 
        def get_size_of_arrray(self):
            return self.nelements()
        
        size = property(get_size_of_arrray,None,None,"The number of elements in the array.")

