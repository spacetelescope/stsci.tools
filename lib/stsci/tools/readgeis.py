#!/usr/bin/env python

# $Id$

"""
        readgeis: Read GEIS file and convert it to a FITS extension file.

        License: http://www.stsci.edu/resources/software_hardware/pyraf/LICENSE

        Usage:

                readgeis.py [options] GEISname FITSname

                GEISname is the input GEIS file in GEIS format, and FITSname
                is the output file in FITS format. GEISname can be a
                directory name.  In this case, it will try to use all `*.??h`
                files as input file names.

                If FITSname is omitted or is a directory name, this task will
                try to construct the output names from the input names, i.e.:

                abc.xyh will have an output name of abc_xyf.fits

        :Options:

        -h     print the help (this text)

        :Example:

        If used in Pythons script, a user can, e. g.::

            >>> from stsci.tools import readgeis
            >>> hdulist = readgeis.readgeis(GEISFileName)  # doctest: +SKIP
            (do whatever with hdulist)
            >>> hdulist.writeto(FITSFileName)  # doctest: +SKIP

        The most basic usage from the command line::

            readgeis.py test1.hhh test1.fits

        This command will convert the input GEIS file test1.hhh to
        a FITS file test1.fits.


        From the command line::

            readgeis.py .

        this will convert all `*.??h` files in the current directory
        to FITS files (of corresponding names) and write them in the
        current directory.


        Another example of usage from the command line::

            readgeis.py "u*" "*"

        this will convert all `u*.??h` files in the current directory
        to FITS files (of corresponding names) and write them in the
        current directory.  Note that when using wild cards, it is
        necessary to put them in quotes.

"""

# Developed by Science Software Branch, STScI, USA.
# This version needs pyfits 0.9.6.3 or later
# and numpy version 1.0.4 or later

from __future__ import division, print_function # confidence high

__version__ = "2.2 (18 Feb, 2011), \xa9 AURA"

import os, sys
from astropy.io import fits
import numpy
from numpy import memmap
from functools import reduce

def stsci(hdulist):
    """For STScI GEIS files, need to do extra steps."""

    instrument = hdulist[0].header.get('INSTRUME', '')

    # Update extension header keywords
    if instrument in ("WFPC2", "FOC"):
        rootname = hdulist[0].header.get('ROOTNAME', '')
        filetype = hdulist[0].header.get('FILETYPE', '')
        for i in range(1, len(hdulist)):
            # Add name and extver attributes to match PyFITS data structure
            hdulist[i].name = filetype
            hdulist[i]._extver = i
            # Add extension keywords for this chip to extension
            hdulist[i].header['EXPNAME'] = (rootname, "9 character exposure identifier")
            hdulist[i].header['EXTVER']= (i, "extension version number")
            hdulist[i].header['EXTNAME'] = (filetype, "extension name")
            hdulist[i].header['INHERIT'] = (True, "inherit the primary header")
            hdulist[i].header['ROOTNAME'] = (rootname, "rootname of the observation set")


def stsci2(hdulist, filename):
    """For STScI GEIS files, need to do extra steps."""

    # Write output file name to the primary header
    instrument = hdulist[0].header.get('INSTRUME', '')
    if instrument in ("WFPC2", "FOC"):
        hdulist[0].header['FILENAME'] = filename


def readgeis(input):

    """Input GEIS files "input" will be read and a HDUList object will
       be returned.

       The user can use the writeto method to write the HDUList object to
       a FITS file.
    """

    global dat
    cardLen = fits.Card.length

    # input file(s) must be of the form *.??h and *.??d
    if input[-1] != 'h' or input[-4] != '.':
        raise "Illegal input GEIS file name %s" % input

    data_file = input[:-1]+'d'

    _os = sys.platform
    if _os[:5] == 'linux' or _os[:5] == 'win32' or _os[:5] == 'sunos' or _os[:3] == 'osf' or _os[:6] == 'darwin':
        bytes_per_line = cardLen+1
    else:
        raise "Platform %s is not supported (yet)." % _os

    geis_fmt = {'REAL':'f', 'INTEGER':'i', 'LOGICAL':'i','CHARACTER':'S'}
    end_card = 'END'+' '* (cardLen-3)

    # open input file
    im = open(input)

    # Generate the primary HDU
    cards = []
    while 1:
        line = im.read(bytes_per_line)[:cardLen]
        line = line[:8].upper() + line[8:]
        if line == end_card:
            break
        cards.append(fits.Card.fromstring(line))

    phdr = fits.Header(cards)
    im.close()

    _naxis0 = phdr.get('NAXIS', 0)
    _naxis = [phdr['NAXIS'+str(j)] for j in range(1, _naxis0+1)]
    _naxis.insert(0, _naxis0)
    _bitpix = phdr['BITPIX']
    _psize = phdr['PSIZE']
    if phdr['DATATYPE'][:4] == 'REAL':
        _bitpix = -_bitpix
    if _naxis0 > 0:
        size = reduce(lambda x,y:x*y, _naxis[1:])
        data_size = abs(_bitpix) * size // 8
    else:
        data_size = 0
    group_size = data_size + _psize // 8

    # decode the group parameter definitions,
    # group parameters will become extension header
    groups = phdr['GROUPS']
    gcount = phdr['GCOUNT']
    pcount = phdr['PCOUNT']

    formats = []
    bools = []
    floats = []
    _range = range(1, pcount+1)
    key = [phdr['PTYPE'+str(j)] for j in _range]
    comm = [phdr.cards['PTYPE'+str(j)].comment for j in _range]

    # delete group parameter definition header keywords
    _list = ['PTYPE'+str(j) for j in _range] + \
            ['PDTYPE'+str(j) for j in _range] + \
            ['PSIZE'+str(j) for j in _range] + \
            ['DATATYPE', 'PSIZE', 'GCOUNT', 'PCOUNT', 'BSCALE', 'BZERO']

    # Construct record array formats for the group parameters
    # as interpreted from the Primary header file
    for i in range(1, pcount+1):
        ptype = key[i-1]
        pdtype = phdr['PDTYPE'+str(i)]
        star = pdtype.find('*')
        _type = pdtype[:star]
        _bytes = pdtype[star+1:]

        # collect boolean keywords since they need special attention later

        if _type == 'LOGICAL':
            bools.append(i)
        if pdtype == 'REAL*4':
            floats.append(i)

        fmt = geis_fmt[_type] + _bytes
        formats.append((ptype,fmt))

    _shape = _naxis[1:]
    _shape.reverse()
    _code = fits.BITPIX2DTYPE[_bitpix]
    _bscale = phdr.get('BSCALE', 1)
    _bzero = phdr.get('BZERO', 0)
    if phdr['DATATYPE'][:10] == 'UNSIGNED*2':
        _uint16 = 1
        _bzero = 32768
    else:
        _uint16 = 0

    # delete from the end, so it will not conflict with previous delete
    for i in range(len(phdr)-1, -1, -1):
        if phdr.cards[i].keyword in _list:
            del phdr[i]

    # clean up other primary header keywords
    phdr['SIMPLE'] = True
    phdr['BITPIX'] = 16
    phdr['GROUPS'] = False
    _after = 'NAXIS'
    if _naxis0 > 0:
        _after += str(_naxis0)
    phdr.set('EXTEND', value=True, comment="FITS dataset may contain extensions", after=_after)
    phdr.set('NEXTEND', value=gcount, comment="Number of standard extensions")

    hdulist = fits.HDUList([fits.PrimaryHDU(header=phdr, data=None)])

    # Use copy-on-write for all data types since byteswap may be needed
    # in some platforms.
    f1 = open(data_file, mode='rb')
    dat = f1.read()
#    dat = memmap(data_file, mode='c')
    hdulist.mmobject = dat

    errormsg = ""

    loc = 0
    for k in range(gcount):
        ext_dat = numpy.fromstring(dat[loc:loc+data_size], dtype=_code)
        ext_dat = ext_dat.reshape(_shape)
        if _uint16:
            ext_dat += _bzero
        # Check to see whether there are any NaN's or infs which might indicate
        # a byte-swapping problem, such as being written out on little-endian
        #   and being read in on big-endian or vice-versa.
        if _code.find('float') >= 0 and \
            (numpy.any(numpy.isnan(ext_dat)) or numpy.any(numpy.isinf(ext_dat))):
            errormsg += "===================================\n"
            errormsg += "= WARNING:                        =\n"
            errormsg += "=  Input image:                   =\n"
            errormsg += input+"[%d]\n"%(k+1)
            errormsg += "=  had floating point data values =\n"
            errormsg += "=  of NaN and/or Inf.             =\n"
            errormsg += "===================================\n"
        elif _code.find('int') >= 0:
            # Check INT data for max values
            ext_dat_frac,ext_dat_exp = numpy.frexp(ext_dat)
            if ext_dat_exp.max() == int(_bitpix) - 1:
                # Potential problems with byteswapping
                errormsg += "===================================\n"
                errormsg += "= WARNING:                        =\n"
                errormsg += "=  Input image:                   =\n"
                errormsg += input+"[%d]\n"%(k+1)
                errormsg += "=  had integer data values        =\n"
                errormsg += "=  with maximum bitvalues.        =\n"
                errormsg += "===================================\n"

        ext_hdu = fits.ImageHDU(data=ext_dat)

        rec = numpy.fromstring(dat[loc+data_size:loc+group_size], dtype=formats)

        loc += group_size

        # Create separate PyFITS Card objects for each entry in 'rec'
        for i in range(1, pcount+1):
            #val = rec.field(i-1)[0]
            val = rec[0][i-1]
            if val.dtype.kind == 'S':
                val = val.decode('ascii')

            if i in bools:
                if val:
                    val = True
                else:
                    val = False

            if i in floats:
                # use fromstring, format in Card is deprecated in pyfits 0.9
                _str = '%-8s= %20.7G / %s' % (key[i-1], val, comm[i-1])
                _card = fits.Card.fromstring(_str)
            else:
                _card = fits.Card(keyword=key[i-1], value=val, comment=comm[i-1])

            ext_hdu.header.append(_card)

        # deal with bscale/bzero
        if (_bscale != 1 or _bzero != 0):
            ext_hdu.header['BSCALE'] = _bscale
            ext_hdu.header['BZERO'] = _bzero

        hdulist.append(ext_hdu)

    if errormsg != "":
        errormsg += "===================================\n"
        errormsg += "=  This file may have been        =\n"
        errormsg += "=  written out on a platform      =\n"
        errormsg += "=  with a different byte-order.   =\n"
        errormsg += "=                                 =\n"
        errormsg += "=  Please verify that the values  =\n"
        errormsg += "=  are correct or apply the       =\n"
        errormsg += "=  '.byteswap()' method.          =\n"
        errormsg += "===================================\n"
        print(errormsg)

    f1.close()
    stsci(hdulist)
    return hdulist

def parse_path(f1, f2):

    """Parse two input arguments and return two lists of file names"""

    import glob

    # if second argument is missing or is a wild card, point it
    # to the current directory
    f2 = f2.strip()
    if f2 == '' or f2 == '*':
        f2 = './'

    # if the first argument is a directory, use all GEIS files
    if os.path.isdir(f1):
        f1 = os.path.join(f1, '*.??h')
    list1 = glob.glob(f1)
    list1 = [name for name in list1 if name[-1] == 'h' and name[-4] == '.']

    # if the second argument is a directory, use file names in the
    # first argument to construct file names, i.e.
    # abc.xyh will be converted to abc_xyf.fits
    if os.path.isdir(f2):
        list2 = []
        for file in list1:
            name = os.path.split(file)[-1]
            fitsname = name[:-4] + '_' + name[-3:-1] + 'f.fits'
            list2.append(os.path.join(f2, fitsname))
    else:
        list2 = [s.strip() for s in f2.split(",")]

    if list1 == [] or list2 == []:
        err_msg = ""
        if list1 == []:
            err_msg += "Input files `{:s}` not usable/available. ".format(f1)

        if list2 == []:
            err_msg += "Input files `{:s}` not usable/available. ".format(f2)

        raise IOError(err_msg)

    else:
        return list1, list2

#-------------------------------------------------------------------------------
# special initialization when this is the main program

if __name__ == "__main__":

    import getopt

    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'h')
    except getopt.error as e:
        print(str(e))
        print(__doc__)
        print("\t", __version__)

    # initialize default values
    help = 0

    # read options
    for opt, value in optlist:
        if opt == "-h":
            help = 1

    if (help):
        print(__doc__)
        print("\t", __version__)
    else:
        if len(args) == 1:
            args.append('')
        list1, list2 = parse_path (args[0], args[1])
        npairs = min (len(list1), len(list2))
        for i in range(npairs):
            if os.path.exists(list2[i]):
                print("Output file %s already exists, skip." % list2[i])
                break
            try:
                hdulist = readgeis(list1[i])
                stsci2(hdulist, list2[i])
                hdulist.writeto(list2[i])
                hdulist.close()
                print("%s -> %s" % (list1[i], list2[i]))
            except Exception as e :
                print("Conversion fails for %s: %s" % (list1[i], str(e)))
                break

"""

Copyright (C) 2003 Association of Universities for Research in Astronomy (AURA)

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
