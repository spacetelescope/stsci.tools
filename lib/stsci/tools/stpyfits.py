# $Id$

"""
The stpyfits module is an extension to the `astropy.io.fits` module which offers
additional features specific to STScI.  These features include the handling
of Constant Data Value Arrays.

"""
from __future__ import division

import functools
import sys
import numpy as np

import astropy
from astropy.io import fits
# A few imports for backward compatibility; in the earlier stpyfits these were
# overridden, but with fits's new extension system it's not necessary
from astropy.io.fits.util import _is_int
from astropy.utils import lazyproperty
from distutils.version import LooseVersion

PY3K = sys.version_info[0] > 2
ASTROPY_VER_GE20 = LooseVersion(astropy.__version__) >= LooseVersion('2.0')

STPYFITS_ENABLED = False  # Not threadsafe TODO: (should it be?)


# Register the extension classes; simply importing stpyfits does not
# automatically enable it.  Instead, it can be enabled/disabled using these
# functions.
def enable_stpyfits():
    global STPYFITS_ENABLED
    if not STPYFITS_ENABLED:
        fits.register_hdu(ConstantValuePrimaryHDU)
        fits.register_hdu(ConstantValueImageHDU)
        STPYFITS_ENABLED = True


def disable_stpyfits():
    global STPYFITS_ENABLED
    if STPYFITS_ENABLED:
        fits.unregister_hdu(ConstantValuePrimaryHDU)
        fits.unregister_hdu(ConstantValueImageHDU)
        STPYFITS_ENABLED = False


def with_stpyfits(func):
    @functools.wraps(func)
    def wrapped_with_stpyfits(*args, **kwargs):
        global STPYFITS_ENABLED
        was_enabled = STPYFITS_ENABLED
        enable_stpyfits()
        try:
            # BUG: Forcefully disable lazy loading.
            # Lazy loading breaks ability to initialize ConstantValueHDUs
            # TODO: Investigate the cause upstream (astropy.io.fits)
            if 'write' not in func.__name__:
                kwargs['lazy_load_hdus'] = False
            retval = func(*args, **kwargs)
        finally:
            # Only disable stpyfits if it wasn't already enabled
            if not was_enabled:
                disable_stpyfits()
        return retval
    return wrapped_with_stpyfits


class _ConstantValueImageBaseHDU(fits.hdu.image._ImageBaseHDU):
    """
    A class that extends the `astropy.io.fits.hdu.base._BaseHDU` class to extend its
    behavior to implement STScI specific extensions to `astropy.io.fits`.

    The `astropy.io.fits.hdu.base._BaseHDU class` is:
    """

    __doc__ += fits.hdu.image._ImageBaseHDU.__doc__

    def __init__(self, data=None, header=None, do_not_scale_image_data=False,
                 uint=False, **kwargs):
        if header and 'PIXVALUE' in header and header['NAXIS'] == 0:
            header = header.copy()
            # Add NAXISn keywords for each NPIXn keyword in the header and
            # remove the NPIXn keywords
            naxis = 0
            for card in reversed(header['NPIX*'].cards):
                try:
                    idx = int(card.keyword[len('NPIX'):])
                except ValueError:
                    continue
                hdrlen = len(header)
                header.set('NAXIS' + str(idx), card.value,
                           card.comment, after='NAXIS')
                del header[card.keyword]
                if len(header) < hdrlen:
                    # A blank card was used when updating the header; add the
                    # blank back in.
                    # TODO: Fix header.set so that it has an option not to
                    # use a blank card--this is a detail that we really
                    # shouldn't have to worry about otherwise
                    header.append()

                # Presumably the NPIX keywords are in order of their axis, but
                # just in case somehow they're not...
                naxis = max(naxis, idx)

            # Update the NAXIS keyword with the correct number of axes
            header['NAXIS'] = naxis
        elif header and 'PIXVALUE' in header:
            pixval = header['PIXVALUE']
            if header['BITPIX'] > 0:
                if PY3K:
                    pixval = int(pixval)
                else:
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
                # that there is non-constant data in the file.
                del header['PIXVALUE']
                for card in header['NPIX*'].cards:
                    try:
                        idx = int(card.keyword[len('NPIX'):])
                    except ValueError:
                        continue
                    del header[card.keyword]

        # Make sure to pass any arguments other than data and header as
        # keyword arguments, because PrimaryHDU and ImageHDU have stupidly
        # different signatures for __init__
        super(_ConstantValueImageBaseHDU, self).__init__(
            data, header, do_not_scale_image_data=do_not_scale_image_data,
            uint=uint)

    @property
    def size(self):
        """
        The HDU's size should always come up as zero so long as there's no
        actual data in it other than the constant value array.
        """

        if 'PIXVALUE' in self._header:
            return 0
        else:
            return super(_ConstantValueImageBaseHDU, self).size

    @lazyproperty
    def data(self):
        if ('PIXVALUE' in self._header and 'NPIX1' not in self._header and
                self._header['NAXIS'] > 0):
            bitpix = self._header['BITPIX']
            dims = self.shape

            # Special case where the pixvalue can be present but all the NPIXn
            # keywords are zero.
            if sum(dims) == 0:
                return None

            code = BITPIX2DTYPE[bitpix]
            pixval = self._header['PIXVALUE']
            if code in ['uint8', 'int16', 'int32', 'int64']:
                if PY3K:
                    pixval = int(pixval)
                else:
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
                self._header['BITPIX'] = DTYPE2BITPIX[data.dtype.name]
            else:
                data = raw_data
            return data
        else:
            return super(_ConstantValueImageBaseHDU, self).data

    @data.setter
    def data(self, data):
        self.__dict__['data'] = data
        self._modified = True
        if self.data is not None and not isinstance(data, np.ndarray):
            # Try to coerce the data into a numpy array--this will work, on
            # some level, for most objects
            try:
                data = np.array(data)
            except:
                raise TypeError('data object %r could not be coerced into an '
                                'ndarray' % data)

        if isinstance(data, np.ndarray):
            self._bitpix = DTYPE2BITPIX[data.dtype.name]
            self._axes = list(data.shape)
            self._axes.reverse()
        elif self.data is None:
            self._axes = []
        else:
            raise ValueError('not a valid data array')

        self.update_header()

    @classmethod
    def match_header(cls, header):
        """A constant value HDU will only be recognized as such if the header
        contains a valid PIXVALUE and NAXIS == 0.
        """

        pixvalue = header.get('PIXVALUE')
        naxis = header.get('NAXIS', 0)

        return (super(_ConstantValueImageBaseHDU, cls).match_header(header) and
                (isinstance(pixvalue, float) or _is_int(pixvalue)) and
                naxis == 0)

    def update_header(self):
        if (not self._modified and not self._header._modified and
                (self._has_data and self.shape == self.data.shape)):
            # Not likely that anything needs updating
            return

        super(_ConstantValueImageBaseHDU, self).update_header()

        if 'PIXVALUE' in self._header and self._header['NAXIS'] > 0:
            # This is a Constant Value Data Array.  Verify that the data
            # actually matches the PIXVALUE
            pixval = self._header['PIXVALUE']
            if self._header['BITPIX'] > 0:
                if PY3K:
                    pixval = int(pixval)
                else:
                    pixval = long(pixval)

            if self.data is None or self.data.nbytes == 0:
                # Empty data array; just keep the existing PIXVALUE
                arrayval = self._header['PIXVALUE']
            else:
                arrayval = self._check_constant_value_data(self.data)
            if arrayval is not None:
                if arrayval != pixval:
                    self._header['PIXVALUE'] = arrayval

                naxis = self._header['NAXIS']
                self._header['NAXIS'] = 0
                for idx in range(naxis, 0, -1):
                    axisval = self._header['NAXIS%d' % idx]
                    self._header.set('NPIX%d' % idx, axisval,
                                     'length of constant array axis %d' % idx,
                                     after='PIXVALUE')
                    del self._header['NAXIS%d' % idx]
            else:
                # No longer a constant value array; remove any remaining
                # NPIX or PIXVALUE keywords
                try:
                    del self._header['PIXVALUE']
                except KeyError:
                    pass

                try:
                    del self._header['NPIX*']
                except KeyError:
                    pass

    def _summary(self):
        summ = super(_ConstantValueImageBaseHDU, self)._summary()
        if ASTROPY_VER_GE20:
            outsumm = ((summ[0], summ[1],
                        summ[2].replace('ConstantValue', '')) + summ[3:])
        else:
            outsumm = ((summ[0],
                        summ[1].replace('ConstantValue', '')) + summ[2:])
        return outsumm

    def _writedata_internal(self, fileobj):
        if 'PIXVALUE' in self._header:
            # This is a Constant Value Data Array, so no data is written
            return 0
        else:
            return super(_ConstantValueImageBaseHDU, self)._writedata_internal(fileobj)

    def _check_constant_value_data(self, data):
        """Verify that the HDU's data is a constant value array."""

        arrayval = data.flat[0]
        if np.all(data == arrayval):
            return arrayval
        return None


class ConstantValuePrimaryHDU(_ConstantValueImageBaseHDU,
                              fits.hdu.PrimaryHDU):
    """Primary HDUs with constant value arrays."""


class ConstantValueImageHDU(_ConstantValueImageBaseHDU, fits.hdu.ImageHDU):
    """Image extension HDUs with constant value arrays."""


# Import the rest of the astropy.io.fits module
from astropy.io.fits import *  # noqa

# For backward-compatibility with older code that thinks PrimaryHDU and
# ImageHDU should support the ConstantValue features
PrimaryHDU = ConstantValuePrimaryHDU
ImageHDU = ConstantValueImageHDU


# Override the other "convenience" functions to use stpyfits
open = fitsopen = with_stpyfits(fits.open)
info = with_stpyfits(fits.info)
append = with_stpyfits(fits.append)
writeto = with_stpyfits(fits.writeto)
update = with_stpyfits(fits.update)
getheader = with_stpyfits(fits.getheader)
getdata = with_stpyfits(fits.getdata)
getval = with_stpyfits(fits.getval)
setval = with_stpyfits(fits.setval)
delval = with_stpyfits(fits.delval)


__all__ = fits.__all__ + ['enable_stpyfits', 'disable_stpyfits',
                          'with_stpyfits', 'ConstantValuePrimaryHDU',
                          'ConstantValueImageHDU']
