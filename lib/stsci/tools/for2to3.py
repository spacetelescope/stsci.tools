""" This is a temporary module, used during (and for a while after) the
transition to Python 3.  This code is planned to be kept in place until
the least version of Python supported no longer requires it (and of course
until all callers no longer need it).
This code should run as-is in 2.x and also run unedited after 2to3 in 3.x.

$Id$
"""

from __future__ import division # confidence high
import os, sys
PY3K = sys.version_info[0] > 2


def ndarr2str(arr, encoding='ascii'):
    """ This is used to ensure that the return value of arr.tostring()
    is actually a string.  This will prevent lots of if-checks in calling
    code.  As of numpy v1.6.1 (in Python 3.2.3), the tostring() function
    still returns type 'bytes', not 'str' as it advertises. """
    # be fast, don't check - just assume 'arr' is a numpy array - the tostring
    # call will fail anyway if not
    retval = arr.tostring()
    # would rather check "if isinstance(retval, bytes)", but support 2.5
    if not isinstance(retval, (str, unicode)):
        return retval.decode(encoding)
    else: # is str
        return retval


def tobytes(s, encoding='ascii'):
    """ Convert string s to the 'bytes' type, even back before Python 2.6.
    In Pythons before 3.0, this is technically the same as the str type
    in terms of the character data in memory. """
    # NOTE: after we abandon 2.5, we might simply instead use "bytes(s)"
    # NOTE: after we abandon all 2.*, del this and prepend byte strings with 'b'
    if PY3K:
        if isinstance(s, bytes):
            return s
        else:
            return s.encode(encoding)
    else:
        # for py2.6 on (before 3.0), bytes is same as str;  2.5 has no bytes
        # but handle if unicode is passed
        if isinstance(s, unicode):
            return s.encode(encoding)
        else:
            return s


try:
    BNULLSTR = tobytes('')   # after dropping 2.5, change to: b''
    BNEWLINE = tobytes('\n') # after dropping 2.5, change to: b'\n'
except:
    BNULLSTR = ''
    BNEWLINE = '\n'


def bytes_read(fd, sz):
   """ Perform an os.read in a way that can handle both Python2 and Python3
   IO.  Assume we are always piping only ASCII characters (since that is all
   we have ever done with IRAF).  Either way, return the data as bytes.
   """
#  return tobytes(os.read(fd, sz))
   return os.read(fd, sz) # already returns str in Py2.x and bytes in PY3K


def bytes_write(fd, bufstr):
   """ Perform an os.write in a way that can handle both Python2 and Python3
   IO.  Assume we are always piping only ASCII characters (since that is all
   we have ever done with IRAF).  Either way, write the binary data to fd.
   """
   return os.write(fd, tobytes(bufstr))
