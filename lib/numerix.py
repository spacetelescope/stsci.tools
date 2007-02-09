"""
Program: numerix.py
Author:  Christopher Hanley
Purpose:

This serves as the interface layer for importing either the numarray or numpy 
array package based upon the NUMERIX environment variable.  This interface
layer allows a user to write applications that will support both the numarray
and numpy array packages.  They syntax of the numerix object is equivalent 
to numpy syntax.

The NUMERIX array package is controlled by the NUMERIX environment variable.  
Set NUMERIX  to 'numarray' for use of numarray.  Set NUMERIX to 'numpy'
for the use of the numpy array package.

If only one array package is installed, that package's version of NUMERIX
will be imported.  If both packages are installed the NUMERIX value is
used to decide between the packages.  If no NUMERIX value is set then 
the numarray version of NUMERIX will be imported.

License: http://www.stsci.edu/resources/software_hardware/pyraf/LICENSE

"""

import os

__version__ = '0.1'

# Check the environment variables for NUMERIX
try:
    numerixflag = os.environ["NUMERIX"]
except:
    numerixflag = 'numarray'

# Deteremine if numarray is installed on the system
try:
    import numarray
    numarraystatus = True
except:
    numarraystatus = False

# Determine if numpy is installed on the system
try:
    import numpy
    numpystatus = True
except:
    numpystatus = False

arraypkg = 'numarray'

if (numpystatus and numarraystatus):
    # if both array packages are installed, use the NUMERIX environment
    # variable to break the tie.  If NUMERIX doesn't exist, default
    # to numarray
    if numerixflag == 'numpy':
        arraypkg = 'numpy'
    else:
        arraypkg = 'numarray'
        
elif (numpystatus):
    # if only numpy is installed use numpy 
    arraypkg = 'numpy'
    
elif (numarraystatus):
    # if only numarray is installed use numarray
    arraypkg = 'numarray'
 
else:
    raise RuntimeError, "The numarray or numpy array package is required for use."

import numerixclass
from numerixclass import numerix

if arraypkg == 'numpy':
    from numpy import *
    from numpy import rec as rec
    from numpy import char as char
    from numpy import memmap
    from numpy import linalg
    from numpy import bool
    import convolve
    import image
    
if arraypkg == 'numarray':
    from numarray import *
    from numarray import records as rec
    from numarray import strings as char
    from numarray.dtype import *
    from numarray import image
    from numarray import convolve
    from numarray.memmap import Memmap as memmap
    from numarray import linear_algebra as linalg
    from numarray.ieeespecial import *
    from numarray import Bool as bool_
    linalg.inv = linalg.inverse
    ndarray = numerixclass.numerix
    rec.recarray = numarray.records.RecArray
    char.chararray = numarray.strings.CharArray

    # Aliases for type names
    uint8 = UInt8
    uint16 = UInt16
    uint32 = UInt32
    uint64 = UInt64
    int8 = Int8
    int16 = Int16
    int32 = Int32
    int64 = Int64
    float32 = Float32
    float64 = Float64
    bool_ = Bool
    
    def array(*args, **keys):
        a = numarray.array(*args, **keys)
        a.__class__ = numerix
        return a 
    
    def ones(*args, **keys):
        a = numarray.ones(*args, **keys)
        a.__class__ = numerix
        return a 
    
    def zeros(*args, **keys):
        a = numarray.zeros(*args, **keys)
        a.__class__ = numerix
        return a 

    def asarray(*args, **keys):
        a = numarray.asarray(*args, **keys)
        a.__class__ = numerix
        return a 

    def fromstring(*args, **keys):
        a = numarray.fromstring(*args, **keys)
        a.__class__ = numerix
        return a

    def arange(*args, **keys):
        a = numarray.arange(*args, **keys)
        a.__class__ = numerix
        return a

_locals = locals().keys()
__all__ = _locals

