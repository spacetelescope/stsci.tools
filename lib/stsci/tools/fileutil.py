"""fileutil.py -- General file functions

These were initially designed for use with PyDrizzle.
These functions only rely on booleans 'yes' and 'no', PyFITS and readgeis.

This file contains both IRAF-compatibility and general file access functions.
General functions included are::

    DEGTORAD(deg), RADTODEG(rad)

    DIVMOD(num,val)

    convertDate(date)
        Converts the DATE date string into a decimal year.

    decimal_date(date-obs,time-obs=None)
        Converts the DATE-OBS (with optional TIME-OBS) string into a decimal year

    buildRootname(filename, extn=None, extlist=None)

    buildNewRootname(filename, ext=None)

    parseFilename(filename)
        Splits a input name into a tuple containing (filename, group/extension)

    getKeyword(filename, keyword, default=None, handle=None)

    getHeader(filename,handle=None)
         Return a copy of the PRIMARY header, along with any group/extension
         header, for this filename specification.

    getExtn(fimg,extn=None)
        Returns a copy of the specified extension with data from PyFITS object
        'fimg' for desired file.

    updateKeyword(filename, key, value)

    openImage(filename,mode='readonly',memmap=False,fitsname=None)
         Opens file and returns PyFITS object.
         It will work on both FITS and GEIS formatted images.

    findFile(input)

    checkFileExists(filename,directory=None)

    removeFile(inlist):
        Utility function for deleting a list of files or a single file.

    rAsciiLine(ifile)
        Returns the next non-blank line in an ASCII file.

    readAsnTable(input,output=None,prodonly=yes)
        Reads an association (ASN) table and interprets inputs and output.
        The 'prodonly' parameter specifies whether to use products as inputs
            or not; where 'prodonly=no' specifies to only use EXP as inputs.

    isFits(input) - returns (True|False, fitstype), fitstype is one of
                    ('simple', 'mef', 'waiver')

IRAF compatibility functions (abbreviated list)::

    osfn(filename)
        Convert IRAF virtual path name to OS pathname

    show(*args, **kw)
        Print value of IRAF or OS environment variables

    time()
        Print current time and date

    access(filename)
        Returns true if file exists, where filename can include IRAF variables
"""

from __future__ import absolute_import, division, print_function  # confidence high

import astropy
from . import stpyfits as fits
from . import readgeis
from . import convertwaiveredfits

import datetime
import copy
import os
import re
import shutil
import sys

import time as _time
import numpy as np
from distutils.version import LooseVersion

PY3K = sys.version_info[0] > 2
if PY3K:
    string_types = str
else:
    string_types = basestring

ASTROPY_VER_GE13 = LooseVersion(astropy.__version__) >= LooseVersion('1.3')

# Environment variable handling - based on iraffunctions.py
# define INDEF, yes, no, EOF, Verbose, userIrafHome

# Set up IRAF-compatible Boolean values
yes = True
no = False

# List of supported default file types
# It will look for these file types by default
# when trying to recognize input rootnames.
EXTLIST =  ['_crj.fits', '_flt.fits', '_flc.fits', '_sfl.fits', '_cal.fits',
            '_raw.fits', '.c0h', '.hhh', '_c0h.fits', '_c0f.fits', '_c1f.fits',
            '.fits']


BLANK_ASNDICT = {
    'output': None,
    'order': [],
    'members': {
        'abshift': no,
        'dshift': no
    }
}


def help():
    print(__doc__)


#################
#
#
#               Generic Functions
#
#
#################
def DEGTORAD(deg):
    return (deg * np.pi / 180.)


def RADTODEG(rad):
    return (rad * 180. / np.pi)


def DIVMOD(num,val):
    if isinstance(num, np.ndarray):
    # Treat number as numpy object
        _num = np.remainder(num, val)
    else:
        _num = divmod(num, val)[1]
    return _num


def getLTime():
    """Returns a formatted string with the current local time."""

    _ltime = _time.localtime(_time.time())
    tlm_str = _time.strftime('%H:%M:%S (%d/%m/%Y)', _ltime)
    return tlm_str


def getDate():
    """Returns a formatted string with the current date."""

    _ltime = _time.localtime(_time.time())
    date_str = _time.strftime('%Y-%m-%dT%H:%M:%S',_ltime)

    return date_str


def convertDate(date):
    """Convert DATE string into a decimal year."""

    d, t = date.split('T')
    return decimal_date(d, timeobs=t)


def decimal_date(dateobs, timeobs=None):
    """Convert DATE-OBS (and optional TIME-OBS) into a decimal year."""

    year, month, day = dateobs.split('-')
    if timeobs is not None:
        hr, min, sec = timeobs.split(':')
    else:
        hr, min, sec = 0, 0, 0

    rdate = datetime.datetime(int(year), int(month), int(day), int(hr),
                              int(min), int(sec))
    dday = (float(rdate.strftime("%j")) + rdate.hour / 24.0 +
            rdate.minute / (60. * 24) + rdate.second / (3600 * 24.)) / 365.25
    ddate = int(year) + dday

    return ddate


def interpretDQvalue(input):
    """
    Converts an integer 'input' into its component bit values as a list of
    power of 2 integers.

    For example, the bit value 1027 would return [1, 2, 1024]
    """

    nbits = 16
    # We will only support integer values up to 2**128
    for iexp in [16, 32, 64, 128]:
        # Find out whether the input value is less than 2**iexp
        if (input // (2 ** iexp)) == 0:
            # when it finally is, we have identified how many bits can be used to
            # describe this input bitvalue
            nbits = iexp
            break

    # Find out how 'dtype' values are described on this machine
    a = np.zeros(1, dtype='int16')
    atype_descr = a.dtype.descr[0][1]
    # Use this description to build the description we need for our input integer
    dtype_str = atype_descr[:2] + str(nbits // 8)
    result = np.zeros(nbits + 1, dtype=dtype_str)

    # For each bit, determine whether it has been set in the input value or not
    for n in range(nbits + 1):
        i = 2 ** n
        if input & i > 0:
            # record which bit has been set as the power-of-2 integer
            result[n] = i

    # Return the non-zero unique values as a Python list
    return np.delete(np.unique(result), 0).tolist()


def isFits(input):
    """
    Returns
    --------
    isFits: tuple
        An ``(isfits, fitstype)`` tuple.  The values of ``isfits`` and
        ``fitstype`` are specified as:

         - ``isfits``: True|False
         - ``fitstype``: if True, one of 'waiver', 'mef', 'simple'; if False, None

    Notes
    -----
    Input images which do not have a valid FITS filename will automatically
    result in a return of (False, None).

    In the case that the input has a valid FITS filename but runs into some
    error upon opening, this routine will raise that exception for the calling
    routine/user to handle.
    """

    isfits = False
    fitstype = None
    names = ['fits', 'fit', 'FITS', 'FIT']
    #determine if input is a fits file based on extension
    # Only check type of FITS file if filename ends in valid FITS string
    f = None
    fileclose = False
    if isinstance(input, fits.HDUList):
        isfits = True
        f = input
    else:
        isfits = True in [input.endswith(l) for l in names]

    # if input is a fits file determine what kind of fits it is
    #waiver fits len(shape) == 3
    if isfits:
        if not f:
            try:
                f = fits.open(input, mode='readonly')
                fileclose = True
            except Exception:
                if f is not None:
                    f.close()
                raise
        data0 = f[0].data
        if data0 is not None:
            try:
                if isinstance(f[1], fits.TableHDU):
                    fitstype = 'waiver'
            except IndexError:
                fitstype = 'simple'

        else:
            fitstype = 'mef'
        if fileclose:
            f.close()

    return isfits, fitstype


def buildRotMatrix(theta):
    _theta = DEGTORAD(theta)
    _mrot = np.zeros(shape=(2,2), dtype=np.float64)
    _mrot[0] = (np.cos(_theta), np.sin(_theta))
    _mrot[1] = (-np.sin(_theta), np.cos(_theta))

    return _mrot


#################
#
#
#               Generic File/Header Functions
#
#
#################
def verifyWriteMode(files):
    """
    Checks whether files are writable. It is up to the calling routine to raise
    an Exception, if desired.

    This function returns True, if all files are writable and False, if any are
    not writable.  In addition, for all files found to not be writable, it will
    print out the list of names of affected files.
    """

    # Start by insuring that input is a list of filenames,
    # if only a single filename has been given as input,
    # convert it to a list with len == 1.
    if not isinstance(files, list):
        files = [files]

    # Keep track of the name of each file which is not writable
    not_writable = []
    writable = True

    # Check each file in input list
    for fname in files:
        try:
            f = open(fname,'a')
            f.close()
            del f
        except:
            not_writable.append(fname)
            writable = False

    if not writable:
        print('The following file(s) do not have write permission!')
        for fname in not_writable:
            print('    ', fname)

    return writable


def getFilterNames(header, filternames=None):
    """
    Returns a comma-separated string of filter names extracted from the input
    header (PyFITS header object).  This function has been hard-coded to
    support the following instruments:

        ACS, WFPC2, STIS

    This function relies on the 'INSTRUME' keyword to define what instrument
    has been used to generate the observation/header.

    The 'filternames' parameter allows the user to provide a list of keyword
    names for their instrument, in the case their instrument is not supported.
    """

    # Define the keyword names for each instrument
    _keydict = {
        'ACS': ['FILTER1', 'FILTER2'],
        'WFPC2': ['FILTNAM1', 'FILTNAM2'],
        'STIS': ['OPT_ELEM', 'FILTER'],
        'NICMOS': ['FILTER', 'FILTER2'],
        'WFC3': ['FILTER', 'FILTER2']
    }

    # Find out what instrument the input header came from, based on the
    # 'INSTRUME' keyword
    if 'INSTRUME' in header:
        instrument = header['INSTRUME']
    else:
        raise ValueError('Header does not contain INSTRUME keyword.')

    # Check to make sure this instrument is supported in _keydict
    if instrument in _keydict:
        _filtlist = _keydict[instrument]
    else:
        _filtlist = filternames

    # At this point, we know what keywords correspond to the filter names
    # in the header.  Now, get the values associated with those keywords.
    # Build a list of all filter name values, with the exception of the
    # blank keywords. Values containing 'CLEAR' or 'N/A' are valid.
    _filter_values = []
    for _key in _filtlist:
        if _key in header:
            _val = header[_key]
        else:
            _val = ''
        if _val.strip() != '':
            _filter_values.append(header[_key])

    # Return the comma-separated list
    return ','.join(_filter_values)


def buildNewRootname(filename, extn=None, extlist=None):
    """
    Build rootname for a new file.

    Use 'extn' for new filename if given, does NOT append a suffix/extension at
    all.

    Does NOT check to see if it exists already.  Will ALWAYS return a new
    filename.
    """

    # Search known suffixes to replace ('_crj.fits',...)
    _extlist = copy.deepcopy(EXTLIST)
    # Also, add a default where '_dth.fits' replaces
    # whatever extension was there ('.fits','.c1h',...)
    #_extlist.append('.')
    # Also append any user-specified extensions...
    if extlist:
        _extlist += extlist

    for suffix in _extlist:
        _indx = filename.find(suffix)
        if _indx > 0: break

    if _indx < 0:
         # default to entire rootname
        _indx = len(filename)

    if extn is None:
        extn = ''

    return filename[:_indx] + extn


def buildRootname(filename, ext=None):
    """
    Build a new rootname for an existing file and given extension.

    Any user supplied extensions to use for searching for file need to be
    provided as a list of extensions.

    Examples
    --------

    ::

        >>> rootname = buildRootname(filename, ext=['_dth.fits'])  # doctest: +SKIP

    """

    if filename in ['' ,' ', None]:
        return None

    fpath, fname = os.path.split(filename)
    if ext is not None and '_' in ext[0]:
        froot = os.path.splitext(fname)[0].split('_')[0]
    else:
        froot = fname

    if fpath in ['', ' ', None]:
        fpath = os.curdir
    # Get complete list of filenames from current directory
    flist = os.listdir(fpath)

    #First, assume given filename is complete and verify
    # it exists...
    rootname = None

    for name in flist:
        if name == froot:
            rootname = froot
            break
        elif name == froot + '.fits':
            rootname = froot + '.fits'
            break

    # If we have an incomplete filename, try building a default
    # name and seeing if it exists...
    #
    # Set up default list of suffix/extensions to add to rootname
    _extlist = []
    for extn in EXTLIST:
        _extlist.append(extn)

    if rootname is None:
        # Add any user-specified extension to list of extensions...
        if ext is not None:
            for i in ext:
                _extlist.insert(0,i)
        # loop over all extensions looking for a filename that matches...
        for extn in _extlist:
            # Start by looking for filename with exactly
            # the same case a provided in ASN table...
            rname = froot + extn
            for name in flist:
                if rname == name:
                    rootname = name
                    break
            if rootname is None:
                # Try looking for all lower-case filename
                # instead of a mixed-case filename as required
                # by the pipeline.
                rname = froot.lower() + extn
                for name in flist:
                    if rname == name:
                        rootname = name
                        break

            if rootname is not None:
                break

    # If we still haven't found the file, see if we have the
    # info to build one...
    if rootname is None and ext is not None:
        # Check to see if we have a full filename to start with...
        _indx = froot.find('.')
        if _indx > 0:
            rootname = froot[:_indx] + ext[0]
        else:
            rootname = froot + ext[0]

    if fpath not in ['.', '', ' ', None]:
        rootname = os.path.join(fpath, rootname)
    # It will be up to the calling routine to verify
    # that a valid rootname, rather than 'None', was returned.
    return rootname


def getKeyword(filename, keyword, default=None, handle=None):
    """
    General, write-safe method for returning a keyword value from the header of
    a IRAF recognized image.

    Returns the value as a string.
    """

    # Insure that there is at least 1 extension specified...
    if filename.find('[') < 0:
        filename += '[0]'

    _fname, _extn = parseFilename(filename)

    if not handle:
        # Open image whether it is FITS or GEIS
        _fimg = openImage(_fname)
    else:
        # Use what the user provides, after insuring
        # that it is a proper PyFITS object.
        if isinstance(handle, fits.HDUList):
            _fimg = handle
        else:
            raise ValueError('Handle must be %r object!' % fits.HDUList)

    # Address the correct header
    _hdr = getExtn(_fimg, _extn).header

    try:
        value =  _hdr[keyword]
    except KeyError:
        _nextn = findKeywordExtn(_fimg, keyword)
        try:
            value = _fimg[_nextn].header[keyword]
        except KeyError:
            value = ''

    if not handle:
        _fimg.close()
        del _fimg

    if value == '':
        if default is None:
            value = None
        else:
            value = default

    # NOTE:  Need to clean up the keyword.. Occasionally the keyword value
    # goes right up to the "/" FITS delimiter, and iraf.keypar is incapable
    # of realizing this, so it incorporates "/" along with the keyword value.
    # For example, after running "pydrizzle" on the image "j8e601bkq_flt.fits",
    # the CD keywords look like this:
    #
    #   CD1_1   = 9.221627430999639E-06/ partial of first axis coordinate w.r.t. x
    #   CD1_2   = -1.0346992614799E-05 / partial of first axis coordinate w.r.t. y
    #
    # so for CD1_1, iraf.keypar returns:
    #       "9.221627430999639E-06/"
    #
    # So, the following piece of code CHECKS for this and FIXES the string,
    # very simply by removing the last character if it is a "/".
    # This fix courtesy of Anton Koekemoer, 2002.
    elif isinstance(value, string_types):
        if value[-1:] == '/':
            value = value[:-1]

    return value


def getHeader(filename, handle=None):
    """
    Return a copy of the PRIMARY header, along with any group/extension header
    for this filename specification.
    """

    _fname, _extn = parseFilename(filename)
    # Allow the user to provide an already opened PyFITS object
    # to derive the header from...
    #
    if not handle:
        # Open image whether it is FITS or GEIS
        _fimg = openImage(_fname, mode='readonly')
    else:
        # Use what the user provides, after insuring
        # that it is a proper PyFITS object.
        if isinstance(handle, fits.HDUList):
            _fimg = handle
        else:
            raise ValueError('Handle must be a %r object!' % fits.HDUList)

    _hdr = _fimg['PRIMARY'].header.copy()

    # if the data is not in the primary array delete NAXIS
    # so that the correct value is read from the extension header
    if _hdr['NAXIS'] == 0:
        del _hdr['NAXIS']

    if not (_extn is None or (_extn.isdigit() and int(_extn) == 0)):
        # Append correct extension/chip/group header to PRIMARY...
        #for _card in getExtn(_fimg,_extn).header.ascard:
            #_hdr.ascard.append(_card)
        for _card in getExtn(_fimg, _extn).header.cards:
            _hdr.append(_card)
    if not handle:
        # Close file handle now...
        _fimg.close()
        del _fimg

    return _hdr


def updateKeyword(filename, key, value,show=yes):
    """Add/update keyword to header with given value."""

    _fname, _extn = parseFilename(filename)

    # Open image whether it is FITS or GEIS
    _fimg = openImage(_fname, mode='update')

    # Address the correct header
    _hdr = getExtn(_fimg, _extn).header

    # Assign a new value or add new keyword here.
    try:
        _hdr[key] = value
    except KeyError:
        if show:
            print('Adding new keyword ', key, '=', value)
        _hdr[key] = value

    # Close image
    _fimg.close()
    del _fimg


def buildFITSName(geisname):
    """Build a new FITS filename for a GEIS input image."""

    # User wants to make a FITS copy and update it...
    _indx = geisname.rfind('.')
    _fitsname = geisname[:_indx] + '_' + geisname[_indx + 1:-1] + 'h.fits'

    return _fitsname


def openImage(filename, mode='readonly', memmap=False, writefits=True,
              clobber=True, fitsname=None):
    """
    Opens file and returns PyFITS object.  Works on both FITS and GEIS
    formatted images.

    Notes
    -----
    If a GEIS or waivered FITS image is used as input, it will convert it to a
    MEF object and only if ``writefits = True`` will write it out to a file. If
    ``fitsname = None``, the name used to write out the new MEF file will be
    created using `buildFITSName`.

    Parameters
    ----------
    filename: str
        name of input file
    mode: str
        mode for opening file based on PyFITS `mode` parameter values
    memmap: bool
        switch for using memory mapping, `False` for no, `True` for yes
    writefits: bool
        if `True`, will write out GEIS as multi-extension FITS
        and return handle to that opened GEIS-derived MEF file
    clobber: bool
        overwrite previously written out GEIS-derived MEF file
    fitsname: str
        name to use for GEIS-derived MEF file,
        if None and writefits==`True`, will use 'buildFITSName()' to generate one
    """
    from stwcs import updatewcs

    # Insure that the filename is always fully expanded
    # This will not affect filenames without paths or
    # filenames specified with extensions.
    filename = osfn(filename)

    # Extract the rootname and extension specification
    # from input image name
    _fname, _iextn = parseFilename(filename)

    # Check whether we have a FITS file and if so what type
    isfits, fitstype = isFits(_fname)

    if isfits:
        if fitstype != 'waiver':
            # Open the FITS file
            fimg = fits.open(_fname, mode=mode, memmap=memmap)
            return fimg
        else:
            fimg = convertwaiveredfits.convertwaiveredfits(_fname)

            #check for the existence of a data quality file
            _dqname = buildNewRootname(_fname, extn='_c1f.fits')
            dqexists = os.path.exists(_dqname)
            if dqexists:
                try:
                    dqfile = convertwaiveredfits.convertwaiveredfits(_dqname)
                    dqfitsname = buildNewRootname(_dqname, extn='_c1h.fits')
                except:
                    print("Could not read data quality file %s" % _dqname)
            if writefits:
                # User wants to make a FITS copy and update it
                # using the filename they have provided
                if fitsname is None:
                    rname = buildNewRootname(_fname)
                    fitsname = buildNewRootname(rname, extn='_c0h.fits')

                # Write out GEIS image as multi-extension FITS.
                fexists = os.path.exists(fitsname)
                if (fexists and clobber) or not fexists:
                    print('Writing out WAIVERED as MEF to ', fitsname)
                    if ASTROPY_VER_GE13:
                        fimg.writeto(fitsname, overwrite=clobber)
                    else:
                        fimg.writeto(fitsname, clobber=clobber)
                    if dqexists:
                        print('Writing out WAIVERED as MEF to ', dqfitsname)
                        if ASTROPY_VER_GE13:
                            dqfile.writeto(dqfitsname, overwrite=clobber)
                        else:
                            dqfile.writeto(dqfitsname, clobber=clobber)
                # Now close input GEIS image, and open writable
                # handle to output FITS image instead...
                fimg.close()
                del fimg
                # Image re-written as MEF, now it needs its WCS updated
                updatewcs.updatewcs(fitsname)

                fimg = fits.open(fitsname, mode=mode, memmap=memmap)

        # Return handle for use by user
        return fimg
    else:
        # Input was specified as a GEIS image, but no FITS copy
        # exists.  Read it in with 'readgeis' and make a copy
        # then open the FITS copy...
        try:
            # Open as a GEIS image for reading only
            fimg = readgeis.readgeis(_fname)
        except:
            raise IOError("Could not open GEIS input: %s" % _fname)

        #check for the existence of a data quality file
        _dqname = buildNewRootname(_fname, extn='.c1h')
        dqexists = os.path.exists(_dqname)
        if dqexists:
            try:
                dqfile = readgeis.readgeis(_dqname)
                dqfitsname = buildFITSName(_dqname)
            except:
                print("Could not read data quality file %s" % _dqname)

        # Check to see if user wanted to update GEIS header.
        # or write out a multi-extension FITS file and return a handle to it
        if writefits:
                # User wants to make a FITS copy and update it
                # using the filename they have provided
            if fitsname is None:
                fitsname = buildFITSName(_fname)

            # Write out GEIS image as multi-extension FITS.
            fexists = os.path.exists(fitsname)
            if (fexists and clobber) or not fexists:
                    print('Writing out GEIS as MEF to ', fitsname)
                    if ASTROPY_VER_GE13:
                        fimg.writeto(fitsname, overwrite=clobber)
                    else:
                        fimg.writeto(fitsname, clobber=clobber)
                    if dqexists:
                        print('Writing out GEIS as MEF to ', dqfitsname)
                        if ASTROPY_VER_GE13:
                            dqfile.writeto(dqfitsname, overwrite=clobber)
                        else:
                            dqfile.writeto(dqfitsname, clobber=clobber)
            # Now close input GEIS image, and open writable
            # handle to output FITS image instead...
            fimg.close()
            del fimg
            # Image re-written as MEF, now it needs its WCS updated
            updatewcs.updatewcs(fitsname)

            fimg = fits.open(fitsname, mode=mode, memmap=memmap)

        # Return handle for use by user
        return fimg


def parseFilename(filename):
    """
    Parse out filename from any specified extensions.

    Returns rootname and string version of extension name.
    """

    # Parse out any extension specified in filename
    _indx = filename.find('[')
    if _indx > 0:
        # Read extension name provided
        _fname = filename[:_indx]
        _extn = filename[_indx + 1:-1]
    else:
        _fname = filename
        _extn = None

    return _fname, _extn


def parseExtn(extn=None):
    """
    Parse a string representing a qualified fits extension name as in the
    output of `parseFilename` and return a tuple ``(str(extname),
    int(extver))``, which can be passed to `astropy.io.fits` functions using
    the 'ext' kw.

    Default return is the first extension in a fits file.

    Examples
    --------

    ::

        >>> parseExtn('sci, 2')
        ('sci', 2)
        >>> parseExtn('2')
        ('', 2)
        >>> parseExtn('sci')
        ('sci', 1)

    """

    if not extn:
        return ('', 0)

    try:
        lext = extn.split(',')
    except:
        return ('', 1)

    if len(lext) == 1 and lext[0].isdigit():
        return ("", int(lext[0]))
    elif len(lext) == 2:
        return (lext[0], int(lext[1]))
    else:
        return (lext[0], 1)


def countExtn(fimg, extname='SCI'):
    """
    Return the number of 'extname' extensions, defaulting to counting the
    number of SCI extensions.
    """

    closefits = False
    if isinstance(fimg, string_types):
        fimg = fits.open(fimg)
        closefits = True

    n = 0
    for e in fimg:
        if 'extname' in e.header and e.header['extname'] == extname:
            n += 1

    if closefits:
        fimg.close()

    return n


def getExtn(fimg, extn=None):
    """
    Returns the PyFITS extension corresponding to extension specified in
    filename.

    Defaults to returning the first extension with data or the primary
    extension, if none have data.  If a non-existent extension has been
    specified, it raises a `KeyError` exception.
    """

    # If no extension is provided, search for first extension
    # in FITS file with data associated with it.
    if extn is None:
        # Set up default to point to PRIMARY extension.
        _extn = fimg[0]
        # then look for first extension with data.
        for _e in fimg:
            if _e.data is not None:
                _extn = _e
                break
    else:
        # An extension was provided, so parse it out...
        if repr(extn).find(',') > 1:
            if isinstance(extn, tuple):
                # We have a tuple possibly created by parseExtn(), so
                # turn it into a list for easier manipulation.
                _extns = list(extn)
                if '' in _extns:
                    _extns.remove('')
            else:
                _extns = extn.split(',')
            # Two values given for extension:
            #    for example, 'sci,1' or 'dq,1'
            try:
                _extn = fimg[_extns[0], int(_extns[1])]
            except KeyError:
                _extn = None
                for e in fimg:
                    hdr = e.header
                    if ('extname' in hdr and
                            hdr['extname'].lower() == _extns[0].lower() and
                            hdr['extver'] == int(_extns[1])):
                        _extn = e
                        break
        elif repr(extn).find('/') > 1:
            # We are working with GEIS group syntax
            _indx = str(extn[:extn.find('/')])
            _extn = fimg[int(_indx)]
        elif isinstance(extn, string_types):
            if extn.strip() == '':
                _extn = None  # force error since invalid name was provided
            # Only one extension value specified...
            elif extn.isdigit():
                # We only have an extension number specified as a string...
                _nextn = int(extn)
            else:
                # We only have EXTNAME specified...
                _nextn = None
                if extn.lower() == 'primary':
                    _nextn = 0
                else:
                    i = 0
                    for hdu in fimg:
                        isimg = 'extname' in hdu.header
                        hdr = hdu.header
                        if isimg and extn.lower() == hdr['extname'].lower():
                            _nextn = i
                            break
                        i += 1

            if _nextn < len(fimg):
                _extn = fimg[_nextn]
            else:
                _extn = None

        else:
            # Only integer extension number given, or default of 0 is used.
            if int(extn) < len(fimg):
                _extn = fimg[int(extn)]
            else:
                _extn = None

    if _extn is None:
        raise KeyError('Extension %s not found' % extn)

    return _extn


#Revision History:
#    Nov 2001: findFile upgraded to accept full filenames with paths,
#               instead of working only on files from current directory. WJH
#
# Base function for
#   with optional path.
def findFile(input):
    """Search a directory for full filename with optional path."""

    # If no input name is provided, default to returning 'no'(FALSE)
    if not input:
        return no

    # We use 'osfn' here to insure that any IRAF variables are
    # expanded out before splitting out the path...
    _fdir, _fname = os.path.split(osfn(input))

    if _fdir == '':
        _fdir = os.curdir

    try:
        flist = os.listdir(_fdir)
    except OSError:
        # handle when requested file in on a disconnect network store
        return no

    _root, _extn = parseFilename(_fname)

    found = no
    for name in flist:
        if name == _root:
            # Check to see if given extension, if any, exists
            if _extn is None:
                found = yes
                continue
            else:
                _split = _extn.split(',')
                _extnum = None
                _extver = None
                if  _split[0].isdigit():
                    _extname = None
                    _extnum = int(_split[0])
                else:
                    _extname = _split[0]
                    if len(_split) > 1:
                        _extver = int(_split[1])
                    else:
                        _extver = 1
                f = openImage(_root)
                f.close()
                if _extnum is not None:
                    if _extnum < len(f):
                        found = yes
                        del f
                        continue
                    else:
                        del f
                else:
                    _fext = findExtname(f, _extname, extver=_extver)
                    if _fext is not None:
                        found = yes
                        del f
                        continue
    return found


def checkFileExists(filename, directory=None):
    """
    Checks to see if file specified exists in current or specified directory.

    Default is current directory.  Returns 1 if it exists, 0 if not found.
    """

    if directory is not None:
        fname = os.path.join(directory,filename)
    else:
        fname = filename
    _exist = os.path.exists(fname)
    return _exist


def copyFile(input, output, replace=None):
    """Copy a file whole from input to output."""

    _found = findFile(output)
    if not _found or (_found and replace):
        shutil.copy2(input, output)


def _remove(file):
    # Check to see if file exists.  If not, return immediately.
    if not findFile(file):
        return

    if file.find('.fits') > 0:
        try:
            os.remove(file)
        except (IOError, OSError):
            pass
    elif file.find('.imh') > 0:
        # Delete both .imh and .pix files
        os.remove(file)
        os.remove(file[:-3] + 'pix')
    else:
        # If we have a GEIS image that has separate header
        # and pixel files which need to be removed.
        # Assumption: filenames end in '.??h' and '.??d'
        #
        os.remove(file)
        # At this point, we may be deleting a non-image
        # file, so only verify whether a GEIS hhd or similar
        # file exists before trying to delete it.
        if findFile(file[:-1] + 'd'):
            os.remove(file[:-1] + 'd')


def removeFile(inlist):
    """
    Utility function for deleting a list of files or a single file.

    This function will automatically delete both files of a GEIS image, just
    like 'iraf.imdelete'.
    """

    if not isinstance(inlist, string_types):
    # We do have a list, so delete all filenames in list.
        # Treat like a list of full filenames
        _ldir = os.listdir('.')
        for f in inlist:
        # Now, check to see if there are wildcards which need to be expanded
            if f.find('*') >= 0 or f.find('?') >= 0:
                # We have a wild card specification
                regpatt = f.replace('?', '.?')
                regpatt = regpatt.replace('*', '.*')
                _reg = re.compile(regpatt)
                for file in _ldir:
                    if _reg.match(file):
                        _remove(file)
            else:
                # This is just a single filename
                _remove(f)
    else:
        # It must be a string then, so treat as a single filename
        _remove(inlist)


def findKeywordExtn(ft, keyword, value=None):
    """
    This function will return the index of the extension in a multi-extension
    FITS file which contains the desired keyword with the given value.
    """

    i = 0
    extnum = -1
    # Search through all the extensions in the FITS object
    for chip in ft:
        hdr = chip.header
        # Check to make sure the extension has the given keyword
        if keyword in hdr:
            if value is not None:
                # If it does, then does the value match the desired value
                # MUST use 'str.strip' to match against any input string!
                if hdr[keyword].strip() == value:
                    extnum = i
                    break
            else:
                extnum = i
                break
        i += 1
    # Return the index of the extension which contained the
    # desired EXTNAME value.
    return extnum


def findExtname(fimg, extname, extver=None):
    """
    Returns the list number of the extension corresponding to EXTNAME given.
    """

    i = 0
    extnum = None
    for chip in fimg:
        hdr = chip.header
        if 'EXTNAME' in hdr:
            if hdr['EXTNAME'].strip() == extname.upper():
                if extver is None or hdr['EXTVER'] == extver:
                    extnum = i
                    break
        i += 1
    return extnum


def rAsciiLine(ifile):
    """Returns the next non-blank line in an ASCII file."""

    _line = ifile.readline().strip()
    while len(_line) == 0:
        _line = ifile.readline().strip()
    return _line


#######################################################
#
#
#
#  IRAF environment variable interpretation routines
#      extracted from PyRAF's 'iraffunction.py'
#
#  These allow IRAF variables to be interpreted without
#      having to install/use IRAF or PyRAF.
#
#
#######################################################
# -----------------------------------------------------
# private dictionaries:
#
# _varDict: dictionary of all IRAF cl variables (defined with set name=value)
# _tasks: all IRAF tasks (defined with task name=value)
# _mmtasks: minimum-match dictionary for tasks
# _pkgs: min-match dictionary for all packages (defined with
#                       task name.pkg=value)
# _loaded: loaded packages
# -----------------------------------------------------

# Will want to enhance this to allow a "bye" function that unloads packages.
# That might be done using a stack of definitions for each task.

_varDict = {}


# module variables that don't get saved (they get
# initialized when this module is imported)

unsavedVars = [
    'EOF',
    '_NullFile',
    '_NullPath',
    '__builtins__',
    '__doc__',
    '__file__',
    '__name__',
    '__re_var_match',
    '__re_var_match2',
    '__re_var_paren',
    '_badFormats',
    '_clearString',
    '_exitCommands',
    '_unsavedVarsDict',
    '_radixDigits',
    '_re_taskname',
    '_sttyArgs',
    'no',
    'yes',
    'userWorkingHome'
]

_unsavedVarsDict = {}
for v in unsavedVars:
    _unsavedVarsDict[v] = 1
del unsavedVars, v


# -----------------------------------------------------
# Miscellaneous access routines:
# getVarList: Get list of names of all defined IRAF variables
# -----------------------------------------------------

def getVarDict():
    """Returns dictionary all IRAF variables."""

    return _varDict


def getVarList():
    """Returns list of names of all IRAF variables."""

    return list(_varDict.keys())


# -----------------------------------------------------
# listVars:
# list contents of the dictionaries
# -----------------------------------------------------

def listVars(prefix="", equals="\t= ", **kw):
    """List IRAF variables."""

    keylist = getVarList()
    if len(keylist) == 0:
        print('No IRAF variables defined')
    else:
        keylist.sort()
        for word in keylist:
            print("%s%s%s%s" % (prefix, word, equals, envget(word)))


def untranslateName(s):
    """Undo Python conversion of CL parameter or variable name."""

    s = s.replace('DOT', '.')
    s = s.replace('DOLLAR', '$')
    # delete 'PY' at start of name components
    if s[:2] == 'PY': s = s[2:]
    s = s.replace('.PY', '.')
    return s


def envget(var, default=None):
    """Get value of IRAF or OS environment variable."""

    if 'pyraf' in sys.modules:
        #ONLY if pyraf is already loaded, import iraf into the namespace
        from pyraf import iraf
    else:
        # else set iraf to None so it knows to not use iraf's environment
        iraf = None

    try:
        if iraf:
            return iraf.envget(var)
        else:
            raise KeyError
    except KeyError:
        try:
            return _varDict[var]
        except KeyError:
            try:
                return os.environ[var]
            except KeyError:
                if default is not None:
                    return default
                elif var == 'TERM':
                    # Return a default value for TERM
                    # TERM gets caught as it is found in the default
                    # login.cl file setup by IRAF.
                    print("Using default TERM value for session.")
                    return 'xterm'
                else:
                    raise KeyError("Undefined environment variable `%s'" % var)


def osfn(filename):
    """Convert IRAF virtual path name to OS pathname."""

    # Try to emulate the CL version closely:
    #
    # - expands IRAF virtual file names
    # - strips blanks around path components
    # - if no slashes or relative paths, return relative pathname
    # - otherwise return absolute pathname
    if filename is None:
        return filename

    ename = Expand(filename)
    dlist = [part.strip() for part in ename.split(os.sep)]
    if len(dlist) == 1 and dlist[0] not in [os.curdir, os.pardir]:
        return dlist[0]

    # I use str.join instead of os.path.join here because
    # os.path.join("","") returns "" instead of "/"

    epath = os.sep.join(dlist)
    fname = os.path.abspath(epath)
    # append '/' if relative directory was at end or filename ends with '/'
    if fname[-1] != os.sep and dlist[-1] in ['', os.curdir, os.pardir]:
        fname = fname + os.sep
    return fname


def defvar(varname):
    """Returns true if CL variable is defined."""

    if 'pyraf' in sys.modules:
        #ONLY if pyraf is already loaded, import iraf into the namespace
        from pyraf import iraf
    else:
        # else set iraf to None so it knows to not use iraf's environment
        iraf = None

    if iraf:
        _irafdef = iraf.envget(varname)
    else:
        _irafdef = 0
    return varname in _varDict or varname in os.environ or _irafdef


# -----------------------------------------------------
# IRAF utility procedures
# -----------------------------------------------------

# these have extra keywords (redirection, _save) because they can
# be called as tasks

def set(*args, **kw):
    """Set IRAF environment variables."""

    if len(args) == 0:
        if len(kw) != 0:
            # normal case is only keyword,value pairs
            for keyword, value in kw.items():
                keyword = untranslateName(keyword)
                svalue = str(value)
                _varDict[keyword] = svalue
        else:
            # set with no arguments lists all variables (using same format
            # as IRAF)
            listVars(prefix="    ", equals="=")
    else:
        # The only other case allowed is the peculiar syntax
        # 'set @filename', which only gets used in the zzsetenv.def file,
        # where it reads extern.pkg.  That file also gets read (in full cl
        # mode) by clpackage.cl.  I get errors if I read this during
        # zzsetenv.def, so just ignore it here...
        #
        # Flag any other syntax as an error.
        if (len(args) != 1 or len(kw) != 0 or
                not isinstance(args[0], string_types) or args[0][:1] != '@'):
            raise SyntaxError("set requires name=value pairs")

# currently do not distinguish set from reset
# this will change when keep/bye/unloading are implemented

reset = set

def show(*args, **kw):
    """Print value of IRAF or OS environment variables."""

    if len(kw):
        raise TypeError('unexpected keyword argument: %r' % list(kw))

    if args:
        for arg in args:
            print(envget(arg))
    else:
        # print them all
        listVars(prefix="    ", equals="=")


def unset(*args, **kw):
    """
    Unset IRAF environment variables.

    This is not a standard IRAF task, but it is obviously useful.  It makes the
    resulting variables undefined.  It silently ignores variables that are not
    defined.  It does not change the os environment variables.
    """

    if len(kw) != 0:
        raise SyntaxError("unset requires a list of variable names")

    for arg in args:
        if arg in _varDict:
            del _varDict[arg]


def time(**kw):
    """Print current time and date."""

    print(_time.ctime(_time.time()))


# -----------------------------------------------------
# Expand: Expand a string with embedded IRAF variables
# (IRAF virtual filename)
# -----------------------------------------------------

# Input string is in format 'name$rest' or 'name$str(name2)' where
# name and name2 are defined in the _varDict dictionary.  The
# name2 string may have embedded dollar signs, which are ignored.
# There may be multiple embedded parenthesized variable names.
#
# Returns string with IRAF variable name expanded to full host name.
# Input may also be a comma-separated list of strings to Expand,
# in which case an expanded comma-separated list is returned.

# search for leading string without embedded '$'
__re_var_match = re.compile(r'(?P<varname>[^$]*)\$')
__re_var_match2 = re.compile(r'\$(?P<varname>\w*)')

# search for string embedded in parentheses
__re_var_paren = re.compile(r'\((?P<varname>[^()]*)\)')


def Expand(instring, noerror=0):
    """
    Expand a string with embedded IRAF variables (IRAF virtual filename).

    Allows comma-separated lists.  Also uses os.path.expanduser to replace '~'
    symbols.

    Set the noerror flag to silently replace undefined variables with just the
    variable name or null (so Expand('abc$def') = 'abcdef' and
    Expand('(abc)def') = 'def').  This is the IRAF behavior, though it is
    confusing and hides errors.
    """

    # call _expand1 for each entry in comma-separated list
    wordlist = instring.split(",")
    outlist = []
    for word in wordlist:
        outlist.append(os.path.expanduser(_expand1(word, noerror=noerror)))
    return ",".join(outlist)


def _expand1(instring, noerror):
    """Expand a string with embedded IRAF variables (IRAF virtual filename)."""

    # first expand names in parentheses
    # note this works on nested names too, expanding from the
    # inside out (just like IRAF)
    mm = __re_var_paren.search(instring)
    while mm is not None:
        # remove embedded dollar signs from name
        varname = mm.group('varname').replace('$','')
        if defvar(varname):
            varname = envget(varname)
        elif noerror:
            varname = ""
        else:
            raise ValueError("Undefined variable `%s' in string `%s'" %
                             (varname, instring))

        instring = instring[:mm.start()] + varname + instring[mm.end():]
        mm = __re_var_paren.search(instring)
    # now expand variable name at start of string
    mm = __re_var_match.match(instring)
    if mm is None:
        return instring
    varname = mm.group('varname')
    if varname in ['', ' ', None]:
        mm = __re_var_match2.match(instring)
        varname = mm.group('varname')

    if defvar(varname):
        # recursively expand string after substitution
        return _expand1(envget(varname) + instring[mm.end():], noerror)
    elif noerror:
        return _expand1(varname + instring[mm.end():], noerror)
    else:
        raise ValueError("Undefined variable `%s' in string `%s'" %
                         (varname, instring))


def access(filename):
    """Returns true if file exists."""

    return os.path.exists(Expand(filename))
