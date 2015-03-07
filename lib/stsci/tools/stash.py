'''This is a tool for stashing certain information used by the
continuous integration system at STScI.  It is not intended for,
or even expected to work, in any other application.

--

use this in shell scripts:
    d=`python -m stsci.tools.stash`
    cp file $d

'''

from __future__ import print_function
import sys
import os

# use os.path.join because the file name may be used outside of
# python and we need it to be right on Windows.
stash_dir = os.path.join(os.path.dirname(__file__),'stash')

try :
    os.mkdir(stash_dir)
except OSError :
    pass

if __name__ == '__main__' :
    print(stash_dir)
    if not os.path.exists(stash_dir) :
        sys.exit(1)

