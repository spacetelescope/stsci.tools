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

from numerixclass import numerix

if arraypkg == 'numpy':
    from numpy import *
    from numpy import rec as rec
    from numpy import char as char

if arraypkg == 'numarray':
    from numarray import *
    from numarray import records as rec
    from numarray import strings as char
    from numarray.dtype import *
    
    def array(*args, **keys):
        a = numarray.array(*args, **keys)
        a.__class__ = numerix
        return a 
    
    def ones(*args, **keys):
        a = numarray.ones(*args, **keys)
        a.__class__ = numerix
        return a 
    
    def ones(*args, **keys):
        a = numarray.zeros(*args, **keys)
        a.__class__ = numerix
        return a 

    def asarray(*args, **keys):
        a = numarray.asarray(*args, **keys)
        a.__class__ = numerix
        return a 


