#!/usr/bin/env python

# $Id$

"""
Convert a waivered FITS file to various other formats.

Syntax for the command line::

    convertwaiveredfits.py [-hm] [-o <outputFileName>,...] FILE ...

Convert the waivered FITS files (wFITS) to various formats.
The default conversion format is multi-extension FITS (MEF).

Options::

    -h, --help                       print this help message and exit

    -v, --verbose                    turn on verbose output

    -m, --multiExtensionConversion   convert to multi-extension
                                     FITS format (Default)

    -o, --outputFileName             comma separated list of
                                     output file specifications
                                     one per input FILE
                                     Default: input file
                                     specification with the last
                                     character of the base name
                                     changed to `h` in multi-extension FITS format

For example, conversion of a WFPC2 waivered FITS file obtained
from the MAST archive::

    convertwaiveredfits u9zh010bm_c0f.fits

This will convert the waivered FITS file ``u9zh010bm_c0f.fits``
to multi-extension FITS format and generate the output file
``u9zh010bm_c0h.fits``.

Conversion of multiple FITS files can be done using::

    convertwaiveredfits -o out1.fits,out2.fits u9zh010bm_c0f.fits u9zh010bm_c1f.fits

This will convert the waivered FITS files ``u9zh010bm_c0f.fits``
and ``u9zh010bm_c1f.fits`` to multi-extension FITS format and
generate the output files ``out1.fits`` and ``out2.fits``.

Parameters
==========
waiveredObject: obj
    input object representing a waivered FITS
    file; either a ``astropy.io.fits.HDUList`` object, a file
    object, or a file specification.

outputFileName : string
    file specification for the output file.
    Default: `None` - do not generate an output file

forceFileOutput: boolean
    force the generation of an output file when
    the ``outputFileName`` parameter is `None`; the
    output file specification will be the same as
    the input file specification with the last
    character of the base name replaced with the
    character ``h`` in multi-extension FITS format.

    Default: False

convertTo: string
    target conversion type.
    Default: 'multiExtension'

verbose: boolean
    provide verbose output.
    Default: `False`

Returns
=======
hduList : fits.HDUList
    ``astropy.io.fits`` multi-extension FITS object containing converted output

Examples
========

>>> from stsci.tools import convertwaiveredfits
>>> hdulist = convertwaiveredfits.convertwaiveredfits(
...     'u9zh010bm_c0f.fits', forceFileOutput=True)  # doctest: +SKIP

This will convert the waivered FITS file ``u9zh010bm_c0f.fits``
to multi-extension FITS format and write the output to the
file ``u9zh010bm_c0h.fits``;  the returned ``HDUList`` is in
multi-extension FITS format.

>>> from stsci.tools import convertwaiveredfits
>>> with open('u9zh010bm_c0f.fits', mode='rb') as inFile:
...     hdulist = convertwaiveredfits.convertwaiveredfits(inFile, 'out.fits')  # doctest: +SKIP

This will convert the waivered FITS file ``u9zh010bm_c0f.fits``
to multi-extension FITS format and write the output to the
file ``out.fits``; the returned ``HDUList`` is in multi-extension
FITS format.

>>> from astropy.io import fits
>>> from stsci.tools import convertwaiveredfits
>>> with fits.open('u9zh010bm_c0f.fits') as inHdul:
...     hdulist = convertwaiveredfits.convertwaiveredfits(inHdul)  # doctest: +SKIP

This will convert the waivered FITS file ``u9zh010bm_c0f.fits``
to multi-extension FITS format; no output file is generated;
the returned ``HDUList`` is in multi-extension format.

"""
from __future__ import division, print_function  # confidence high

#
# -----------------------------------------------------------------------------
# Import required modules
# -----------------------------------------------------------------------------
#
import os
import sys
import astropy
from astropy.io import fits
from distutils.version import LooseVersion

if sys.version_info[0] < 3:
    string_types = basestring
else:
    string_types = str

ASTROPY_VER_GE13 = LooseVersion(astropy.__version__) >= LooseVersion('1.3')

__version__ = "1.1 (15 June, 2015)"


#
# -----------------------------------------------------------------------------
# Function definitions
# -----------------------------------------------------------------------------
#
def _usage():
    """
        Print a usage message.

        Parameters: NONE

        Returns: None

        Exceptions: NONE
    """

    print("usage: convertwaiveredfits.py [-hmv] [-o <outputFileName>, ...] FILE ...")


def _processCommandLineArgs():
    """
        Get the command line arguments

        Parameters: NONE

        Returns:

           files            list of file specifications to be converted

           outputFileNames  list of output file specifications
                             (one per input file)
                             Default: a list of None values (one per input file)

           conversionFormat string indicating the conversion format requested
                             Default: "mulitextension"

           verbose          flag indicating if verbose output is desired
                             Default: False

        Exceptions: NONE
    """

    import getopt

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvmo:",
                                   ["help",
                                    "verbose",
                                    "multiExtensionConversion",
                                    "outputFileName"])
    except getopt.GetoptError as e:
        print(str(e))
        _usage()
        sys.exit(1)

    conversionFormat = ""
    outputFileNames = []
    verbose = False

    for o, a in opts:
        if o in ("-h", "--help"):
            _usage()
            print("       Convert the waivered FITS Files (FILEs) to various formats.")
            print("       The default conversion format is multi-extension FITS.")
            print("       Options:")
            print("         -h,  --help                       display this help message and exit")
            print("         -v,  --verbose                    provide verbose output")
            print("         -m,  --multiExtensionConversion   convert to multiExtension FITS format")
            print("         -o,  --outputFileName             comma separated list of output file")
            print("                                           specifications (one per input FILE)")
            sys.exit()

        if o in ("-v", "--verbose"):
            verbose = True

        if o in ("-m", "--multiExtensionConversion"):
            if conversionFormat != "":
                print("convertwaiveredfits.py: only one conversion format allowed")
                _usage()
                sys.exit(1)

            conversionFormat = "multiExtension"

        if o in ("-o", "--outputFileName"):
            outputFileNames = a.split(',')

    if conversionFormat == "":
        #
        # Set the default conversion format if none was provided
        #
        conversionFormat = "multiExtension"

    if not args:
        print("convertwaiveredfits.py: nothing to convert")
        _usage()
        sys.exit(1)
    else:
        files = args

        if outputFileNames:
            if len(files) != len(outputFileNames):
                print("convertwaiveredfits.py: number of output file names does not match")
                print("                        the number of FILEs to convert")
                _usage()
                sys.exit(1)
        else:
            for i in range(0,len(files)):
                outputFileNames.append(None)

    return files,outputFileNames,conversionFormat,verbose

def _verify(waiveredHdul):
    """
        Verify that the input HDUList is for a waivered FITS file.

        Parameters:

           waiveredHdul     HDUList object to be verified

        Returns: None

        Exceptions:

           ValueError       Input HDUList is not for a waivered FITS file
    """

    if len(waiveredHdul) == 2:
        #
        # There must be exactly 2 HDU's
        #
        if waiveredHdul[0].header['NAXIS'] > 0:
            #
            # The Primary HDU must have some data
            #
            if isinstance(waiveredHdul[1], fits.TableHDU):
                #
                # The Alternate HDU must be a TableHDU
                #
                if waiveredHdul[0].data.shape[0] == \
                   waiveredHdul[1].data.shape[0] or \
                   waiveredHdul[1].data.shape[0] == 1:
                    #
                    # The number of arrays in the Primary HDU must match
                    # the number of rows in the TableHDU.  This includes
                    # the case where there is only a single array and row.
                    #
                    return
    #
    # Not a valid waivered Fits file
    #
    raise ValueError("Input object does not represent a valid waivered" + \
                      " FITS file")

def toMultiExtensionFits(waiveredObject,
                         multiExtensionFileName=None,
                         forceFileOutput=False,
                         verbose=False):
    """
        Convert the input waivered FITS object to a multi-extension FITS
        HDUList object.  Generate an output multi-extension FITS file if
        requested.

        Parameters:

          waiveredObject  input object representing a waivered FITS file;
                          either a astroyp.io.fits.HDUList object, a file object, or a
                          file specification

          outputFileName  file specification for the output file
                          Default: None - do not generate an output file

          forceFileOutput force the generation of an output file when the
                          outputFileName parameter is None; the output file
                          specification will be the same as the input file
                          specification with the last character of the base
                          name replaced with the character 'h'.
                          Default: False

          verbose         provide verbose output
                          Default: False

        Returns:

          mhdul           an HDUList object in multi-extension FITS format.

        Exceptions:

          TypeError       Input object is not a HDUList, a file object or a
                          file name
    """

    if isinstance(waiveredObject, fits.HDUList):
        whdul = waiveredObject
        inputObjectDescription = "HDUList object"
    else:
        try:
            whdul = fits.open(waiveredObject)
            if isinstance(waiveredObject, string_types):
                inputObjectDescription = "file " + waiveredObject
            else:
                inputObjectDescription = "file " + waiveredObject.name
        except TypeError:
            raise TypeError("Input object must be HDUList, file object, " + \
                            "or file name")

    _verify(whdul)

    undesiredPrimaryHeaderKeywords = ['ORIGIN','FITSDATE','FILENAME',
                                      'ALLG-MAX','ALLG-MIN','ODATTYPE',
                                      'SDASMGNU','OPSIZE','CTYPE2',
                                      'CD2_2','CD2_1','CD1_2','CTYPE3',
                                      'CD3_3','CD3_1','CD1_3','CD2_3',
                                      'CD3_2']
    #
    # Create the multi-extension primary header as a copy of the
    # wavered file primary header
    #
    mPHeader = whdul[0].header
    originalDataType =  whdul[0].header.get('ODATTYPE','')
    #
    # Remove primary header cards with keywords matching the
    # list of undesired primary header keywords
    #
    for keyword in undesiredPrimaryHeaderKeywords:
        #
        # Be careful only to delete the first card that matches
        # the keyword, not all of the cards
        #
        if keyword in mPHeader:
            del mPHeader[mPHeader.index(keyword)]
    #
    # Get the columns from the secondary HDU table
    #
    wcols = whdul[1].columns
    #
    # Remove primary header cards with keywords matching the
    # column names in the secondary HDU table
    #
    for keyword in wcols.names:
        if keyword in mPHeader:
            del mPHeader[keyword]
    #
    # Create the PrimaryHDU
    #
    mPHdu = fits.PrimaryHDU(header=mPHeader)
    #
    # Add the EXTEND card
    #
    mPHdu.header.set('EXTEND', value=True, after='NAXIS')
    #
    # Add the NEXTEND card.  There will be one extension
    # for each row in the wavered Fits file table HDU.
    #
    mPHdu.header['NEXTEND'] = (whdul[1].data.shape[0],
                               'Number of standard extensions')
    #
    # Create the multi-extension file HDUList from the primary header
    #
    mhdul = fits.HDUList([mPHdu])
    #
    # Create the extension HDUs for the multi-extension file.  There
    # will be one extension for each row in the wavered file's table.
    #
    instrument = mPHeader.get('INSTRUME', '')
    nrows = whdul[1].data.shape[0]

    for i in range(0,nrows):
        #
        # Create the basic HDU from the data
        #
        if nrows == 1:
            #
            # Handle case where there is only one row in the table
            #
            data = whdul[0].data
        else:
            data = whdul[0].data[i]

        mhdul.append(fits.ImageHDU(data))
        #
        # Add cards to the header for each keyword in the column
        # names of the secondary HDU table from the wavered file
        #
        for keyword,format,unit in zip(wcols.names,wcols.formats,wcols.units):
            if unit == 'LOGICAL-':
                #
                # Handle logical values
                #
                if whdul[1].data.field(keyword)[i].strip() == 'T':
                    d = True
                else:
                    d = False
            elif format[0] == 'E':
                #
                # Handle floating point values
                #
                fmt = '%'+format[1:]+'G'
                d = eval(fmt % float(whdul[1].data.field(keyword)[i]))
            else:
                d = whdul[1].data.field(keyword)[i]

            kw_descr = ""
            if keyword in whdul[1].header:
                kw_descr = whdul[1].header[keyword]
            mhdul[i+1].header[keyword] = (d, kw_descr)
        #
        # If original data is unsigned short then scale the data.
        #
        if originalDataType == 'USHORT':
            mhdul[i+1].scale('int16','',bscale=1,bzero=32768)
            mhdul[i+1].header.set('BSCALE', value=1, before='BZERO')
        #
        # For WFPC2 and FOS instruments require additional header cards
        #
        if instrument in ('WFPC2','FOC'):
            #
            # Add EXTNAME card to header
            #
            mhdul[i+1].header['EXTNAME'] = (mPHeader.get('FILETYPE',''),
                                            'extension name')
            #
            # Add EXTVER card to the header
            #
            mhdul[i+1]._extver = i+1
            mhdul[i+1].header.set('EXTVER', value=i+1,
                                  comment='extension version number',
                                  after='EXTNAME')
            #
            # Add the EXPNAME card to the header
            #
            mhdul[i+1].header.set('EXPNAME',
                                  mPHeader.get('ROOTNAME', ''),
                                  '9 character exposure identifier',
                                  before='EXTVER')
            #
            # Add the INHERIT card to the header.
            #
            mhdul[i+1].header.set('INHERIT', True,
                                  'inherit the primary header',
                                  after='EXTVER')
            #
            # Add the ROOTNAME card to the header
            #
            mhdul[i+1].header.set('ROOTNAME',
                                  mPHeader.get('ROOTNAME', ''),
                                  'rootname of the observationset',
                                  after='INHERIT')

    if not multiExtensionFileName and forceFileOutput:
        base,ext = os.path.splitext(whdul[0]._file.name)
        multiExtensionFileName = base[:-1]+'h'+ext

    verboseString = "Input " + inputObjectDescription + \
                    " converted to multi-extension FITS format."

    if multiExtensionFileName:
        if instrument in ('WFPC2','FOC'):
            #
            # write the FILENAME card to the header for the WFPC2 and FOC
            # instruments
            #
            head,tail = os.path.split(multiExtensionFileName)
            mhdul[0].header.set('FILENAME', value=tail, after='NEXTEND')

        if ASTROPY_VER_GE13:
            mhdul.writeto(multiExtensionFileName, overwrite=True)
        else:
            mhdul.writeto(multiExtensionFileName, clobber=True)

        verboseString = verboseString[:-1] + " and written to " + \
                        multiExtensionFileName + "."

    if verbose:
        print(verboseString)

    return mhdul


def convertwaiveredfits(waiveredObject,
                        outputFileName=None,
                        forceFileOutput=False,
                        convertTo='multiExtension',
                        verbose=False):
    """
        Convert the input waivered FITS object to various formats.  The
        default conversion format is multi-extension FITS.  Generate an output
        file in the desired format if requested.

        Parameters:

          waiveredObject  input object representing a waivered FITS file;
                          either a astropy.io.fits.HDUList object, a file object, or a
                          file specification

          outputFileName  file specification for the output file
                          Default: None - do not generate an output file

          forceFileOutput force the generation of an output file when the
                          outputFileName parameter is None; the output file
                          specification will be the same as the input file
                          specification with the last character of the base
                          name replaced with the character `h` in
                          multi-extension FITS format.

                          Default: False

          convertTo       target conversion type
                          Default: 'multiExtension'

          verbose         provide verbose output
                          Default: False

        Returns:

          hdul            an HDUList object in the requested format.

        Exceptions:

           ValueError       Conversion type is unknown
    """

    if convertTo == 'multiExtension':
        func = toMultiExtensionFits
    else:
        raise ValueError('Conversion type ' + convertTo + ' unknown')

    return func(*(waiveredObject,outputFileName,forceFileOutput,verbose))
#
# *****************************************************************************
# Main Program callable from the shell
# *****************************************************************************
#

def main() :
    files,outputFiles,conversionFormat,verbose = _processCommandLineArgs()

    for f,outputfile in zip(files,outputFiles):
        convertwaiveredfits(f,outputfile,True,conversionFormat,verbose)

    sys.exit()


if __name__ == '__main__':
    main()

"""

Copyright (C) 2005 Association of Universities for Research in Astronomy (AURA)

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above
      copyright notice, this list of conditions and the following
      disclaimer in the documentation and/or other materials provided
      with the distribution.

    3. The name of AURA and its representatives may not be used to
      endorse or promote products derived from this software without
      specific prior written permission.

THIS SOFTWARE IS PROVIDED BY AURA ``AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL AURA BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
DAMAGE.
"""
