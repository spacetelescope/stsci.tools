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
    # would rather check "if isinstance(retval, bytes)", but support 2.5.
    # could rm the if PY3K check, but it makes this faster on 2.x.
    if PY3K and not isinstance(retval, str):
        return retval.decode(encoding)
    else: # is str
        return retval


def ndarr2bytes(arr, encoding='ascii'):
    """ This is used to ensure that the return value of arr.tostring()
    is actually a *bytes* array in PY3K.  See notes in ndarr2str above.  Even
    though we consider it a bug that numpy's tostring() function returns
    a bytes array in PY3K, there are actually many instances where that is what
    we want - bytes, not unicode.  So we use this function in those
    instances to ensure that when/if this numpy "bug" is "fixed", that
    our calling code still gets bytes where it needs/expects them. """
    # be fast, don't check - just assume 'arr' is a numpy array - the tostring
    # call will fail anyway if not
    retval = arr.tostring()
    # would rather check "if not isinstance(retval, bytes)", but support 2.5.
    if PY3K and isinstance(retval, str):
        # Take note if this ever gets used.  If this ever occurs, it
        # is likely wildly inefficient since numpy.tostring() is now
        # returning unicode and numpy surely has a tobytes() func by now.
        # If so, add a code path to call its tobytes() func at our start.
        return retval.encode(encoding)
    else: # is str==bytes in 2.x
        return retval


def tobytes(s, encoding='ascii'):
    """ Convert string s to the 'bytes' type, in all Pythons, even
    back before Python 2.6.  What 'str' means varies by PY3K or not.
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

def tostr(s, encoding='ascii'):
    """ Convert string-like-thing s to the 'str' type, in all Pythons, even
    back before Python 2.6.  What 'str' means varies by PY3K or not.
    In Pythons before 3.0, str and bytes are the same type.
    In Python 3+, this may require a decoding step. """
    if PY3K:
        if isinstance(s, str): # str == unicode in PY3K
            return s
        else: # s is type bytes
            return s.decode(encoding)
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
