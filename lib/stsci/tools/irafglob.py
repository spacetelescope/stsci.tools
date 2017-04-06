"""
License: http://www.stsci.edu/resources/software_hardware/pyraf/LICENSE
"""
from __future__ import absolute_import, division # confidence high
import glob
try:
    from .fileutil import osfn # added to provide interpretation of environment variables
except:
    osfn = None
__author__ = 'Paul Barrett'
__version__ = '1.1'

def irafglob(inlist, atfile=None):
    """ Returns a list of filenames based on the type of IRAF input.

    Handles lists, wild-card characters, and at-files.  For special
    at-files, use the atfile keyword to process them.

    This function is recursive, so IRAF lists can also contain at-files
    and wild-card characters, e.g. `a.fits`, `@file.lst`, `*flt.fits`.
    """

    # Sanity check
    if inlist is None or len(inlist) == 0:
        return []

    # Determine which form of input was provided:
    if isinstance(inlist, list):
        #  python list
        flist = []
        for f in inlist:
            flist += irafglob(f)
    elif ',' in inlist:
        #  comma-separated string list
        flist = []
        for f in inlist.split(','):
            f = f.strip()
            flist += irafglob(f)
    elif inlist[0] == '@':
        #  file list
        flist = []
        for f in open(inlist[1:], 'r').readlines():
            f = f.rstrip()
            # hook for application specific atfiles.
            if atfile:
                f = atfile(f)
            flist += irafglob(f)
    else:
        #  shell globbing
        if osfn:
            inlist = osfn(inlist)
        flist = glob.glob(inlist)

    return flist
