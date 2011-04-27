# $Id$

"""
The stpyfits module is an extension to the pyfits module which offers
additional features specific to STScI.  These features include the handling
of Constant Data Value Arrays.

The pyfits module is:
"""


from __future__ import division

import functools
import re
import numpy as np

import pyfits
# A few imports for backward compatibility; in the earlier stpyfits these were
# overridden, but with pyfits's new extension system it's not necessary
from pyfits import HDUList


__version__ = '1.1.0/%s' % pyfits.__version__


STPYFITS_ENABLED = False # Not threadsafe TODO: (should it be?)

# Register the extension classes; simply importing stpyfits does not
# automatically enable it.  Instead, it can be enabled/disabled using these
# functions.
def enable_stpyfits():
    global STPYFITS_ENABLED
    if not STPYFITS_ENABLED:
        pyfits.register_hdu(ConstantValuePrimaryHDU)
        pyfits.register_hdu(ConstantValueImageHDU)
        STPYFITS_ENABLED = True


def disable_stpyfits():
    global STPYFITS_ENABLED
    if STPYFITS_ENABLED:
        pyfits.unregister_hdu(ConstantValuePrimaryHDU)
        pyfits.unregister_hdu(ConstantValueImageHDU)
        STPYFITS_ENABLED = False


# For backwards compatibility, provide the same convenience functions that this
# module originally provided
def with_stpyfits(func):
    @functools.wraps(func)
    def wrapped_with_stpyfits(*args, **kwargs):
        global STPYFITS_ENABLED
        was_enabled = STPYFITS_ENABLED
        enable_stpyfits()
        try:
            retval = func(*args, **kwargs)
        finally:
            # Only disable stpyfits if it wasn't already enabled
            if not was_enabled:
                disable_stpyfits()
        return retval
    return wrapped_with_stpyfits


open = fitsopen = with_stpyfits(pyfits.open)
info = with_stpyfits(pyfits.info)
append = with_stpyfits(pyfits.append)
writeto = with_stpyfits(pyfits.writeto)
update = with_stpyfits(pyfits.update)
getheader = with_stpyfits(pyfits.getheader)
getdata = with_stpyfits(pyfits.getdata)
getval = with_stpyfits(pyfits.getval)
setval = with_stpyfits(pyfits.setval)
delval = with_stpyfits(pyfits.delval)


class _ConstantValueImageBaseHDU(pyfits.hdu.image._ImageBaseHDU):
    """
    A class that extends the pyfits.hdu.base._BaseHDU class to extend its
    behavior to implement STScI specific extensions to Pyfits.

    The pyfits.hdu.base._BaseHDU class is:
    """

    __doc__ += pyfits.hdu.image._ImageBaseHDU.__doc__

    def __init__(self, data=None, header=None, do_not_scale_image_data=False,
                 uint=False):
        if header and 'PIXVALUE' in header and header['NAXIS'] == 0:
            header = header.copy()
            # Add NAXISn keywords for each NPIXn keyword in the header and
            # remove the NPIXn keywords
            naxis = 0
            for card in reversed(header.ascard['NPIX*']):
                try:
                    idx = int(card.key[len('NPIX'):])
                except ValueError:
                    continue
                hdrlen = len(header.ascard)
                header.update('NAXIS' + str(idx), card.value,
                              card.comment, after='NAXIS')
                del header[card.key]
                if len(header.ascard) < hdrlen:
                    # A blank card was used when updating the header; add the
                    # blank back in.
                    # TODO: Fix header.update so that it has an option not to
                    # use a blank card--this is a detail that we really
                    # shouldn't have to worry about otherwise
                    header.add_blank()

                # Presumably the NPIX keywords are in order of their axis, but
                # just in case somehow they're not...
                naxis = max(naxis, idx)

            # Update the NAXIS keyword with the correct number of axes
            header['NAXIS'] = naxis
        elif header and 'PIXVALUE' in header:
            pixval = header['PIXVALUE']
            if header['BITPIX'] > 0:
                pixval = long(pixval)
            arrayval = self._check_constant_value_data(data)
            if arrayval is not None:
                header = header.copy()
                # Update the PIXVALUE keyword if necessary
                if arrayval != pixval:
                    header['PIXVALUE'] = arrayval
            else:
                header = header.copy()
                # There is a PIXVALUE keyword but NAXIS is not 0 and the data
                # does not match the PIXVALUE.
                # Must remove the PIXVALUE and NPIXn keywords so we recognize
                # tha there is non-constant data in the file.
                del header['PIXVALUE']
                for card in header.ascard['NPIX*']:
                    try:
                        idx = int(card.key[len('NPIX'):])
                    except ValueError:
                        continue
                    del header[card.key]

        super(_ConstantValueImageBaseHDU, self).__init__(
            data, header, do_not_scale_image_data, uint)

    def size(self):
        """
        The HDU's size should always come up as zero so long as there's no
        actual data in it other than the constant value array.
        """

        if 'PIXVALUE' in self._header:
            return 0
        else:
            return super(_ConstantValueImageBaseHDU, self).size()


    @pyfits.util.lazyproperty
    def data(self):
        if 'PIXVALUE' in self._header and 'NPIX1' not in self._header and \
           self._header['NAXIS'] > 0:
            bitpix = self._header['BITPIX']
            dims = self._dimShape()
            code = self.NumCode[bitpix]
            pixval = self._header['PIXVALUE']
            if code in ['uint8', 'int16', 'int32', 'int64']:
                pixval = long(pixval)

            raw_data = np.zeros(shape=dims, dtype=code) + pixval

            if raw_data.dtype.str[0] != '>':
                raw_data = raw_data.byteswap(True)

            raw_data.dtype = raw_data.dtype.newbyteorder('>')

            if self._bzero != 0 or self._bscale != 1:
                if bitpix > 16:  # scale integers to Float64
                    data = np.array(raw_data, dtype=np.float64)
                elif bitpix > 0:  # scale integers to Float32
                    data = np.array(raw_data, dtype=np.float32)
                else:  # floating point cases
                    data = raw_data

                if self._bscale != 1:
                    np.multiply(data, self._bscale, data)
                if self._bzero != 0:
                    data += self._bzero

                # delete the keywords BSCALE and BZERO after scaling
                del self._header['BSCALE']
                del self._header['BZERO']
                self._header['BITPIX'] = self.ImgCode[data.dtype.name]
            else:
                data = raw_data
            return data
        else:
            return super(_ConstantValueImageBaseHDU, self).data

    def _summary(self):
        summ = super(_ConstantValueImageBaseHDU, self)._summary()
        return (summ[0], summ[1].replace('ConstantValue', '')) + summ[2:]

    def _writeheader(self, fileobj, checksum=False):
        if 'PIXVALUE' in self._header and self._header['NAXIS'] > 0:
            # This is a Constant Value Data Array.  Verify that the data
            # actually matches the PIXVALUE
            pixval = self._header['PIXVALUE']
            if self._header['BITPIX'] > 0:
                pixval = long(pixval)

            arrayval = self._check_constant_value_data(self.data)
            new_header = self._header
            if arrayval is not None:
                st_ext = True
                if arrayval != pixval:
                    self._header['PIXVALUE'] = arrayval

                new_header = self._header.copy()
                naxis = self._header['NAXIS']
                new_header['NAXIS'] = 0
                for idx in range(naxis, 0, -1):
                    axisval = self._header['NAXIS' + str(idx)]
                    new_header.update('NPIX' + str(idx), axisval,
                                      'length of constant array axis ' +
                                      str(idx), after='PIXVALUE')
                    del new_header['NAXIS' + str(idx)]

            old_header = self._header
            self._header = new_header
            try:
                offset = super(_ConstantValueImageBaseHDU, self).\
                    _writeheader(fileobj, checksum)
            finally:
                self._header = old_header
        else:
            # All elements in array are not the same value.
            # so this is no longer a constant data value array
            del self._header['PIXVALUE']
            offset = super(_ConstantValueImageBaseHDU, self)._writeheader(
                fileobj, checksum)

        return offset

    def _writedata_internal(self, fileobj):
        if 'PIXVALUE' in self._header:
            # This is a Constant Value Data Array, so no data is written
            return 0
        else:
            return super(_ConstantValueImageBaseHDU, self).\
                    _writedata_internal(fileobj)

    def _check_constant_value_data(self, data):
        """Verify that the HDU's data is a constant value array."""

        arrayval = np.reshape(data, (data.size,))[0]
        if np.all(data == arrayval):
            return arrayval
        return None



class ConstantValuePrimaryHDU(pyfits.hdu.PrimaryHDU,
                              _ConstantValueImageBaseHDU):
    @classmethod
    def match_header(cls, header):
        return super(ConstantValuePrimaryHDU, cls).match_header(header) and \
               'PIXVALUE' in header
# For backward-compatibility
PrimaryHDU = ConstantValuePrimaryHDU


class ConstantValueImageHDU(pyfits.hdu.ImageHDU,
                            _ConstantValueImageBaseHDU):
    @classmethod
    def match_header(cls, header):
        return super(ConstantValueImageHDU, cls).match_header(header) and \
               'PIXVALUE' in header
# For backward-compatibility
ImageHDU = ConstantValueImageHDU


#
# Restrict what can be imported using from stpyfits import *
#
_locals = locals().keys()
for n in _locals[::-1]:
    if 'ConstantValue' not in n or \
       n not in ('enable_stpyfits', 'disable_stpyfits', 'open', 'info',
                 'append', 'writeto', 'update', 'getheader', 'getdata',
                 'getval', 'setval', 'delval', 'HDUList', 'PrimaryHDU',
                 'ImageHDU'):
        _locals.remove(n)
__all__ = _locals
