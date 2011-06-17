#!/usr/bin/env python

# $Id$

"""
The stpyfits module is an extension to the pyfits module which offers
additional features specific to STScI.  These features include the handling
of Constant Data Value Arrays.

The pyfits module is:
"""

from __future__ import division
from pyfits import *
import pyfits
import re

try:
   numpyVersion = np.__version__
except:
   raise RuntimeError, "The numpy array package is required for use."

__version__ = '1.0.1' + '/' + pyfits.__version__

if pyfits.__doc__:
    __doc__ = __doc__ + pyfits.__doc__

class st_HDUList(pyfits.HDUList):
    """
    A class that extends the pyfits.HDUList class to extend its behavior to
    implement STScI specific extensions to Pyfits.

    Base Class methods reimplemented: writeto, __getitem__, insert, append,
    and flush.

    The pyfits.HDUList class is:

    """

    __doc__ = __doc__ + pyfits.HDUList.__doc__

    def writeto(self, name, output_verify='exception', clobber=False,
                classExtensions={}, checksum=False):
        _assignSt_pyfitsClassExtensions(classExtensions)
        pyfits.HDUList.writeto(self, name, output_verify, clobber,
                               classExtensions, checksum)

    writeto.__doc__ = pyfits.HDUList.writeto.__doc__

    def __getitem__(self, key, classExtensions={}):
        _assignSt_pyfitsClassExtensions(classExtensions)
        item = pyfits.HDUList.__getitem__(self, key, classExtensions)

        return item

    __getitem__.__doc__ = pyfits.HDUList.__getitem__.__doc__

    def flush(self, output_verify='exception', verbose=0, classExtensions={}):
        _assignSt_pyfitsClassExtensions(classExtensions)
        pyfits.HDUList.flush(self, output_verify, verbose, classExtensions)

    flush.__doc__ = pyfits.HDUList.flush.__doc__

    def insert(self, index, hdu, classExtensions={}):
        _assignSt_pyfitsClassExtensions(classExtensions)
        pyfits.HDUList.insert(self, index, hdu, classExtensions)

    insert.__doc__ = pyfits.HDUList.insert.__doc__

    def append(self, hdu, classExtensions={}):
        _assignSt_pyfitsClassExtensions(classExtensions)
        pyfits.HDUList.append(self, hdu, classExtensions)

    insert.__doc__ = pyfits.HDUList.append.__doc__

HDUList = st_HDUList

class st_File(core._File):
    """
    A class that extends the pyfits._File class to extend its behavior to
    implement STScI specific extensions to Pyfits.

    Base Class methods reimplemented: _readHDU, writeHDUheader, and
    writeHDUdata.

    The pyfits._File class is:

    """
    __doc__ = __doc__ + core._File.__doc__
#
#   some needed regular expressions as class attributes
#
    pixvalue_RE = re.compile('PIXVALUE=')
    naxis_RE = re.compile('NAXIS   = ')
    npixn_RE = re.compile(r'NPIX(\d+)\s*=\s*(\d+)')
    naxisVal_len1_RE = re.compile('0')
    naxisVal_len2_RE = re.compile('[ 0]|[0 ]')
    naxisVal_len3_RE = re.compile('[  0]|[ 0 ]|[0  ]')

    def _readHDU(self):
#
#       Call base class _readHDU to perform generic reading of header
#
        hdu = core._File._readHDU(self)
#
#       Convert header for HDU's with constant value data arrays
#
        pixvalue_mo = self.pixvalue_RE.search(hdu._raw)
        naxis_mo = self.naxis_RE.search(hdu._raw)
        naxis_sidx = naxis_mo.start()

        if (pixvalue_mo and int(hdu._raw[naxis_sidx+9:naxis_sidx+30]) == 0):
#
#           Add NAXISn keywords for each NPIXn keyword in the raw header
#           and remove the NPIXx keyword
#
            iterator = self.npixn_RE.finditer(hdu._raw)
            numAxis = 0

            for mo in iterator:
                numAxis = numAxis + 1
                sidx = mo.start()
                nAxisStr = 'NAXIS' + str(numAxis) + \
                           (3-len(str(numAxis)))*' ' + \
                           hdu._raw[sidx+8:sidx+80]
                hdu._raw = hdu._raw[:naxis_sidx+(80*numAxis)] + nAxisStr + \
                           (80-len(nAxisStr))*' ' + \
                           hdu._raw[naxis_sidx+(80*numAxis):sidx] + \
                           hdu._raw[sidx+80:]
#
#           Replace NAXIS=0 keyword with NAXIS=n keyword where n is the
#           number of NPIXn keywords
#
            numAxisS = '%d'%numAxis
            lstr = len(numAxisS)

            if lstr == 1:
                naxisVal_RE = self.naxisVal_len1_RE
            elif lstr == 2:
                naxisVal_RE = self.naxisVal_len2_RE
            elif lstr == 3:
                naxisVal_RE = self.naxisVal_len3_RE
            else:
                raise RuntimeError("More than 999 NPIXn keywords in constant data value header")

            tmpRaw, nSub = naxisVal_RE.subn(numAxisS,hdu._raw[naxis_sidx+10:],1)

            if nSub != 1:
                raise RuntimeError("Unable to substitute NAXISn for NPIXn in the header")

            hdu._raw = hdu._raw[:naxis_sidx+10] + tmpRaw
        elif (pixvalue_mo):
#
#           There is a PIXVALUE keyword but NAXIS is not 0 so there is data.
#           Must remove the PIXVALUE and NPIXn keywords so we recognize that
#           there is data in the file.
#
            pixvalue_mo = self.pixvalue_RE.search(hdu._raw)
            sidx = pixvalue_mo.start()
            hdu._raw = hdu._raw[:sidx] + hdu._raw[sidx+80:]

            iterator = self.npixn_RE.finditer(hdu._raw)
            numAxis = 0

            for mo in iterator:
                numAxis = numAxis + 1
                npix_mo = self.npixn_RE.search(hdu._raw)
                sidx = npix_mo.start()
                hdu._raw = hdu._raw[:sidx] + hdu._raw[sidx+80:]
#
#           Add blanks to the end of the raw header to make up for the
#           deleted cards.
#
            hdu._raw = hdu._raw[:] + (80*(numAxis+1))*' '

        return hdu

    _readHDU.__doc__ = core._File._readHDU.__doc__

    def writeHDUheader(self, hdu, checksum=False):
        if (hdu.header.has_key('PIXVALUE') and hdu.header['NAXIS'] > 0):
#
#           This is a Constant Value Data Array.  Verify that the data actually
#           matches the PIXVALUE.
#
            pixVal = hdu.header['PIXVALUE']
            arrayVal = np.reshape(hdu.data,(hdu.data.size,))[0]

            if hdu.header['BITPIX'] > 0:
               pixVal = long(pixVal)

            if np.all(hdu.data == arrayVal):
                st_ext = True
                if arrayVal != pixVal:
                    hdu.header['PIXVALUE'] = arrayVal

                newHeader = hdu.header.copy()
                naxis = hdu.header['NAXIS']
                newHeader['NAXIS'] = 0

                for n in range(naxis,0,-1):
                    axisval = hdu.header['NAXIS'+str(n)]
                    newHeader.update('NPIX'+str(n), axisval,
                                     'length of constant array axis '+str(n),
                                     after='PIXVALUE')
                    del newHeader['NAXIS'+str(n)]

                hdu = core._AllHDU(header=newHeader)
            else:
#
#               All elements in array are not the same value.
#               so this is no longer a constant data value array
#
                del hdu.header['PIXVALUE']

#       This is not a STScI extension so call the base class method
#       to write the header.
#
        loc = core._File.writeHDUheader(self, hdu, checksum=checksum)

        return loc

    writeHDUheader.__doc__ = core._File.writeHDUheader.__doc__

    def writeHDUdata(self, hdu):
        if (hdu.header.has_key('PIXVALUE')):
#
#           This is a Constant Value Data Array.
#
            self._File__file.flush()
            loc = self._File__file.tell()
            _size = 0
        else:
#
#          This is not a STScI extension so call the base class method
#          to write the data.
#
            loc, _size =  core._File.writeHDUdata(self,hdu)

        # return both the location and the size of the data area
        return loc, _size+core._padLength(_size)

    writeHDUdata.__doc__ = core._File.writeHDUdata.__doc__

class st_ImageBaseHDU(core._ImageBaseHDU):
    """
    A class that extends the pyfits._ImageBaseHDU class to extend its behavior
    to implement STScI specific extensions to Pyfits.

    Base Class methods reimplemented: __getattr__

    The pyfits._ImageBaseHDU class is:

    """
    __doc__ = __doc__ + core._ImageBaseHDU.__doc__

    def __getattr__(self, attr):

#        Notes
#        -----
#
#        This method only handles requests for the data attribute when the HDU
#        represents a Constant Value Data Array.  All other attribute requests
#        are passed on to the base class __getattr__ method.

        if (attr == 'data' and self.header.has_key('PIXVALUE') and
            (not self.header.has_key('NPIX1')) and self.header['NAXIS'] > 0):
            self.__dict__[attr] = None
            _bitpix = self.header['BITPIX']
            if isinstance(self, GroupsHDU):
                dims = self.size()*8//abs(_bitpix)
            else:
                dims = self._dimShape()

            code = core._ImageBaseHDU.NumCode[_bitpix]
            pixVal = self.header['PIXVALUE']

            if code in ['uint8','int16','int32','int64']:
               pixVal = long(pixVal)

            raw_data = np.zeros(shape=dims,dtype=code) + pixVal

            if raw_data.dtype.str[0] != '>':
               raw_data = raw_data.byteswap(True)

            raw_data.dtype = raw_data.dtype.newbyteorder('>')

            if (self._bzero != 0 or self._bscale != 1):
                if _bitpix > 16:  # scale integers to Float64
                    self.data = np.array(raw_data, dtype=np.float64)
                elif _bitpix > 0:  # scale integers to Float32
                    self.data = np.array(raw_data, dtype=np.float32)
                else:  # floating point cases
                    self.data = raw_data

                if self._bscale != 1:
                    np.multiply(self.data, self._bscale, self.data)
                if self._bzero != 0:
                    self.data += self._bzero

                # delete the keywords BSCALE and BZERO after scaling
                del self.header['BSCALE']
                del self.header['BZERO']
                self.header['BITPIX'] = core._ImageBaseHDU.ImgCode[self.data.dtype.name]
            else:
                self.data = raw_data

            rtn_value = self.data
        else:
#
#           This is not a STScI extenstion so call the base class
#           method.
#
            rtn_value = core._ImageBaseHDU.__getattr__(self, attr)

        return rtn_value

    __getattr__.__doc__ = core._ImageBaseHDU.__getattr__.__doc__

    def writeto(self, name, output_verify='exception', clobber=False,
                classExtensions={}, checksum=False):
        _assignSt_pyfitsClassExtensions(classExtensions)
        core._ImageBaseHDU.writeto(self, name, output_verify, clobber,
                                   classExtensions, checksum)

    writeto.__doc__ = core._ImageBaseHDU.writeto.__doc__


class st_PrimaryHDU(PrimaryHDU, st_ImageBaseHDU):
    """
    A class that extends the pyfits.PrimaryHDU class to extend its behavior
    to implement STScI specific extensions to Pyfits.

    Base Class methods reimplemented: None

    Notes
    -----

    While this class does not reimplement any methods, it does add
    st_ImageBaseHDU to the inheritance hierarchy of pyfits.PrimaryHDU when
    accessed through the stpyfits namespace.

    The pyfits.PrimaryHDU class is:

    """
    __doc__ = __doc__ + pyfits.PrimaryHDU.__doc__

    pass

PrimaryHDU = st_PrimaryHDU

class st_ImageHDU(ImageHDU, st_ImageBaseHDU):
    """
    A class that extends the pyfits.ImageHDU class to extend its behavior
    to implement STScI specific extensions to Pyfits.

    Base Class methods reimplemented: __init__

    Notes
    -----

    This class adds st_ImageBaseHDU to the inheritance hierarchy of
    pyfits.ImageHDU when accessed through the stpyfits namespace.

    The pyfits.ImageHDU class is:

    """
    __doc__ = __doc__ + pyfits.ImageHDU.__doc__

    def __init__(self, data=None, header=None, name=None):
        pyfits.ImageHDU.__init__(self, data=data, header=header)

        self.header._hdutype = st_ImageHDU

    __init__.__doc__ = pyfits.ImageHDU.__init__.__doc__


ImageHDU = st_ImageHDU

def _assignSt_pyfitsClassExtensions(classExtensions):
    """
    Function to assign stpyfits class extensions to the input dictionary.

    If and extenstion for a class already exists in the dictionary, it is
    not replaced.

    Parameters
    ----------
    classExtensions: A dictionary
        This dictionary maps pyfits classes to extensions of
        those classes.  When present in the dictionary, the
        extension class will be constructed in place of the
        pyfits class.

    Returns
    -------
    None
    """

    if not classExtensions.has_key(core._File):
        classExtensions[core._File] = st_File

    if not classExtensions.has_key(pyfits.HDUList):
        classExtensions[pyfits.HDUList] = st_HDUList

    if not classExtensions.has_key(pyfits.PrimaryHDU):
        classExtensions[pyfits.PrimaryHDU] = st_PrimaryHDU

    if not classExtensions.has_key(pyfits.ImageHDU):
        classExtensions[pyfits.ImageHDU] = st_ImageHDU

def _assignSt_pyfitsClassExtensionsKeywordDict(keywords):
    """
    Function to add the stpyfits classExtension dictionary to the input
    keyword dictionary.

    If the classExtension dictionary already exists in the inpt keyword
    dictionary, it is updated for stpyfits.

    Parameters
    ----------
    keywords: dictionary
        A dictionary that maps keyword arguments to their values.

    Returns
    -------
    None
    """

    if keywords.has_key('classExtensions'):
        _assignSt_pyfitsClassExtensions(keywords['classExtensions'])
    else:
        classExtensions = {}
        _assignSt_pyfitsClassExtensions(classExtensions)
        keywords['classExtensions'] = classExtensions

#
# Reimplement the open convenience function to allow it to pass a dictionary
# containing classes and their corresponding reimplementations.  The
# reimplemented classes will be constructed instead of the original classes.
# This will allow for support of the STScI specific features provided in
# stpyfits.
#
def open(name, mode="copyonwrite", memmap=0, classExtensions={}, **parms):

    _assignSt_pyfitsClassExtensions(classExtensions)
    hduList = pyfits.open(name, mode, memmap, classExtensions, **parms)

    return hduList

open.__doc__ = pyfits.open.__doc__
fitsopen = open

#
# Reimplement the info convenience function to allow it to pass a dictionary
# containing classes and their corresponding reimplementations.  The
# reimplemented classes will be constructed instead of the original classes.
# This will allow for support of the STScI specific features provided in
# stpyfits.
#
def info(filename, classExtensions={}, **parms):

    _assignSt_pyfitsClassExtensions(classExtensions)
    pyfits.info(filename,classExtensions=classExtensions, **parms)

info.__doc__ = pyfits.info.__doc__

#
# Reimplement the append convenience function to allow it to pass a dictionary
# containing classes and their corresponding reimplementations.  The
# reimplemented classes will be constructed instead of the original classes.
# This will allow for support of the STScI specific features provided in
# stpyfits.
#
def append(filename, data, header=None, classExtensions={}):

    _assignSt_pyfitsClassExtensions(classExtensions)
    pyfits.append(filename, data, header, classExtensions)

append.__doc__ = pyfits.append.__doc__

#
# Reimplement the writeto convenience function to allow it to pass a dictionary
# containing classes and their corresponding reimplementations.  The
# reimplemented classes will be constructed instead of the original classes.
# This will allow for support of the STScI specific features provided in
# stpyfits.
#
def writeto(filename, data, header=None, **keys):

    _assignSt_pyfitsClassExtensionsKeywordDict(keys)
    pyfits.writeto(filename, data, header, **keys)

writeto.__doc__ = pyfits.writeto.__doc__

#
# Reimplement the update convenience function to allow it to pass a dictionary
# containing classes and their corresponding reimplementations.  The
# reimplemented classes will be constructed instead of the original classes.
# This will allow for support of the STScI specific features provided in
# stpyfits.
#
def update(filename, data, *ext, **extkeys):

    _assignSt_pyfitsClassExtensionsKeywordDict(extkeys)
    pyfits.update(filename, data, *ext, **extkeys)

update.__doc__ = pyfits.update.__doc__

#
# Reimplement the getheader convenience function to allow it to pass a
# dictionary containing classes and their corresponding reimplementations.  The
# reimplemented classes will be constructed instead of the original classes.
# This will allow for support of the STScI specific features provided in
# stpyfits.
#
def getheader(filename, *ext, **extkeys):

    _assignSt_pyfitsClassExtensionsKeywordDict(extkeys)

    hdr = pyfits.getheader(filename, *ext, **extkeys)

    return hdr

getheader.__doc__ = pyfits.getheader.__doc__

#
# Reimplement the getdata convenience function to allow it to pass a dictionary
# containing classes and their corresponding reimplementations.  The
# reimplemented classes will be constructed instead of the original classes.
# This will allow for support of the STScI specific features provided in
# stpyfits.
#
def getdata(filename, *ext, **extkeys):

    _assignSt_pyfitsClassExtensionsKeywordDict(extkeys)
    data = pyfits.getdata(filename, *ext, **extkeys)

    return data

getdata.__doc__ = pyfits.getdata.__doc__

#
# Reimplement the getval convenience function to call the stpyfits
# getheader function.  This will allow it to pass a dictionary containing
# classes and their corresponding reimplementations.  The reimplemented
# classes will be constructed instead of the original classes.  This will
# allow for support of the STScI specific features provided in stpyfits.
#
def getval(filename, key, *ext, **extkeys):

    hdr = getheader(filename, *ext, **extkeys)
    return hdr[key]

getval.__doc__ = pyfits.getval.__doc__

#
# Reimplement the setval convenience function to allow it to pass a dictionary
# containing classes and their corresponding reimplementations.  The
# reimplemented classes will be constructed instead of the original classes.
# This will allow for support of the STScI specific features provided in
# stpyfits.
#
def setval(filename, key, value="", comment=None, before=None, after=None,
           savecomment=False, *ext, **extkeys):

    _assignSt_pyfitsClassExtensionsKeywordDict(extkeys)
    pyfits.setval(filename, key, value, comment, before, after,
                  savecomment, *ext, **extkeys)

setval.__doc__ = pyfits.setval.__doc__

#
# Reimplement the delval convenience function to allow it to pass a dictionary
# containing classes and their corresponding reimplementations.  The
# reimplemented classes will be constructed instead of the original classes.
# This will allow for support of the STScI specific features provided in
# stpyfits.
#
def delval(filename, key, *ext, **extkeys):

    _assignSt_pyfitsClassExtensionsKeywordDict(extkeys)
    pyfits.delval(filename, key, *ext, **extkeys)

delval.__doc__ = pyfits.delval.__doc__

#
# Restrict what can be imported using from stpyfits import *
#
_locals = locals().keys()
for n in _locals[::-1]:
    if n[0] == '_' or n in ('re', 'open') or n[0:3] == 'py_' or n[0:3] == 'st_':
        _locals.remove(n)
__all__ = _locals



