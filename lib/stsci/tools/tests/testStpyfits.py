#!/usr/bin/env python
from __future__ import division  # confidence high

import os
import tempfile

import numpy as np
from nose.tools import assert_true, assert_false, assert_equal, assert_raises

import stsci.tools.stpyfits as stpyfits
#import pyfits
from astropy.io import fits
#from pyfits.tests import PyfitsTestCase
from astropy.io.fits.tests import FitsTestCase


class TestStpyfitsFunctions(FitsTestCase):
    def setup(self):
        self.data_dir = os.path.dirname(__file__)
        self.temp_dir = tempfile.mkdtemp(prefix='stpyfits-test-')

    def testInfoConvienceFunction(self):
        """Test the info convience function in both the fits and stpyfits
           namespace."""

        assert_equal(
            stpyfits.info(self.data('o4sp040b0_raw.fits'), output=False),
            [(0, 'PRIMARY', 'PrimaryHDU', 215, (), '', ''),
             (1, 'SCI', 'ImageHDU', 141, (62, 44), 'int16', ''),
             (2, 'ERR', 'ImageHDU', 71, (62, 44), 'int16', ''),
             (3, 'DQ', 'ImageHDU', 71, (62, 44), 'int16', ''),
             (4, 'SCI', 'ImageHDU', 141, (62, 44), 'int16', ''),
             (5, 'ERR', 'ImageHDU', 71, (62, 44), 'int16', ''),
             (6, 'DQ', 'ImageHDU', 71, (62, 44), 'int16', '')])


        assert_equal(
            fits.info(self.data('o4sp040b0_raw.fits'), output=False),
            [(0, 'PRIMARY', 'PrimaryHDU', 215, (), '', ''),
             (1, 'SCI', 'ImageHDU', 141, (62, 44), 'int16', ''),
             (2, 'ERR', 'ImageHDU', 71, (), '', ''),
             (3, 'DQ', 'ImageHDU', 71, (), '', ''),
             (4, 'SCI', 'ImageHDU', 141, (62, 44), 'int16', ''),
             (5, 'ERR', 'ImageHDU', 71, (), '', ''),
             (6, 'DQ', 'ImageHDU', 71, (), '', '')])

        assert_equal(
            stpyfits.info(self.data('cdva2.fits'), output=False),
            [(0, 'PRIMARY', 'PrimaryHDU', 7, (10, 10), 'int32', '')])

        assert_equal(
            fits.info(self.data('cdva2.fits'), output=False),
            [(0, 'PRIMARY', 'PrimaryHDU', 7, (), '', '')])


    def testOpenConvienceFunction(self):
        """Test the open convience function in both the fits and stpyfits
           namespace."""

        hdul = stpyfits.open(self.data('cdva2.fits'))
        hdul1 = fits.open(self.data('cdva2.fits'))

        assert_equal(hdul[0].header['NAXIS'], 2)
        assert_equal(hdul1[0].header['NAXIS'], 0)
        assert_equal(hdul[0].header['NAXIS1'], 10)
        assert_equal(hdul[0].header['NAXIS2'], 10)

        assert_raises(KeyError, lambda: hdul1[0].header['NAXIS1'])
        assert_raises(KeyError, lambda: hdul1[0].header['NAXIS2'])
        assert_raises(KeyError, lambda: hdul[0].header['NPIX1'])
        assert_raises(KeyError, lambda: hdul[0].header['NPIX2'])

        assert_equal(hdul1[0].header['NPIX1'], 10)
        assert_equal(hdul1[0].header['NPIX2'], 10)

        assert_true((hdul[0].data == np.ones((10, 10), dtype=np.int32)).all())

        assert_equal(hdul1[0].data, None)

        hdul.close()
        hdul1.close()

    def testGetHeaderConvienceFunction(self):
        """Test the getheader convience function in both the fits and
           stpyfits namespace."""

        hd = stpyfits.getheader(self.data('cdva2.fits'))
        hd1 = fits.getheader(self.data('cdva2.fits'))

        assert_equal(hd['NAXIS'], 2)
        assert_equal(hd1['NAXIS'], 0)
        assert_equal(hd['NAXIS1'], 10)
        assert_equal(hd['NAXIS2'], 10)

        assert_raises(KeyError, lambda: hd1['NAXIS1'])
        assert_raises(KeyError, lambda: hd1['NAXIS2'])
        assert_raises(KeyError, lambda: hd['NPIX1'])
        assert_raises(KeyError, lambda: hd['NPIX2'])

        assert_equal(hd1['NPIX1'], 10)
        assert_equal(hd1['NPIX2'], 10)

        hd = stpyfits.getheader(self.data('o4sp040b0_raw.fits'), 2)
        hd1 = fits.getheader(self.data('o4sp040b0_raw.fits'), 2)

        assert_equal(hd['NAXIS'], 2)
        assert_equal(hd1['NAXIS'], 0)
        assert_equal(hd['NAXIS1'], 62)
        assert_equal(hd['NAXIS2'], 44)

        assert_raises(KeyError, lambda: hd1['NAXIS1'])
        assert_raises(KeyError, lambda: hd1['NAXIS2'])
        assert_raises(KeyError, lambda: hd['NPIX1'])
        assert_raises(KeyError, lambda: hd['NPIX2'])

        assert_equal(hd1['NPIX1'], 62)
        assert_equal(hd1['NPIX2'], 44)

    def testGetDataConvienceFunction(self):
        """Test the getdata convience function in both the fits and
           stpyfits namespace."""

        d = stpyfits.getdata(self.data('cdva2.fits'))
        assert_true((d == np.ones((10, 10), dtype=np.int32)).all())

        assert_raises(IndexError, fits.getdata, self.data('cdva2.fits'))

    def testGetValConvienceFunction(self):
        """Test the getval convience function in both the fits and
           stpyfits namespace."""

        val = stpyfits.getval(self.data('cdva2.fits'), 'NAXIS', 0)
        val1 = fits.getval(self.data('cdva2.fits'), 'NAXIS', 0)
        assert_equal(val, 2)
        assert_equal(val1, 0)

    def testwritetoConvienceFunction(self):
        """Test the writeto convience function in both the fits and stpyfits
           namespace."""

        hdul = stpyfits.open(self.data('cdva2.fits'))
        hdul1 = fits.open(self.data('cdva2.fits'))

        header = hdul[0].header.copy()
        header['NAXIS'] = 0

        stpyfits.writeto(self.temp('new.fits'), hdul[0].data, header,
                         clobber=True)
        fits.writeto(self.temp('new1.fits'), hdul1[0].data,hdul1[0].header,
                     clobber=True)

        hdul.close()
        hdul1.close()

        info1 = fits.info(self.temp('new.fits'), output=False)
        info2 = stpyfits.info(self.temp('new.fits'), output=False)
        info3 = fits.info(self.temp('new1.fits'), output=False)
        info4 = stpyfits.info(self.temp('new1.fits'), output=False)

        assert_equal(info1, [(0, 'PRIMARY', 'PrimaryHDU', 6, (), '', '')])
        assert_equal(info2,
            [(0, 'PRIMARY', 'PrimaryHDU', 6, (10, 10), 'int32', '')])
        assert_equal(info3, [(0, 'PRIMARY', 'PrimaryHDU', 6, (), '', '')])
        assert_equal(info4,
            [(0, 'PRIMARY', 'PrimaryHDU', 6, (10, 10), 'uint8', '')])

    def testappendConvienceFunction(self):
        """Test the append convience function in both the fits and stpyfits
           namespace."""

        hdul = stpyfits.open(self.data('cdva2.fits'))
        hdul1 = fits.open(self.data('cdva2.fits'))

        stpyfits.writeto(self.temp('new.fits'), hdul[0].data, hdul[0].header,
                         clobber=True)
        fits.writeto(self.temp('new1.fits'), hdul1[0].data, hdul1[0].header,
                       clobber=True)

        hdu = stpyfits.ImageHDU()
        hdu1 = fits.ImageHDU()

        hdu.data = hdul[0].data
        hdu1.data = hdul1[0].data
        hdu.header.set('BITPIX', 32)
        hdu1.header.set('BITPIX', 32)
        hdu.header.set('NAXIS', 2)
        hdu.header.set('NAXIS1', 10, 'length of constant array axis 1',
                       after='NAXIS')
        hdu.header.set('NAXIS2', 10, 'length of constant array axis 2',
                       after='NAXIS1')
        hdu.header.set('PIXVALUE', 1, 'Constant pixel value', after='GCOUNT')
        hdu1.header.set('PIXVALUE', 1, 'Constant pixel value', after='GCOUNT')
        hdu1.header.set('NPIX1', 10, 'length of constant array axis 1',
                        after='GCOUNT')
        hdu1.header.set('NPIX2', 10, 'length of constant array axis 2',
                        after='NPIX1')
        stpyfits.append(self.temp('new.fits'), hdu.data, hdu.header)
        fits.append(self.temp('new1.fits'), hdu1.data, hdu1.header)

        assert_equal(stpyfits.info(self.temp('new.fits'), output=False),
            [(0, 'PRIMARY', 'PrimaryHDU', 7, (10, 10), 'int32', ''),
             (1, '', 'ImageHDU', 8, (10, 10), 'int32', '')])
        assert_equal(stpyfits.info(self.temp('new1.fits'), output=False),
            [(0, 'PRIMARY', 'PrimaryHDU', 7, (10, 10), 'uint8', ''),
             (1, '', 'ImageHDU', 8, (10, 10), 'uint8', '')])
        assert_equal(fits.info(self.temp('new.fits'), output=False),
            [(0, 'PRIMARY', 'PrimaryHDU', 7, (10, 10), 'int32', ''),
             (1, '', 'ImageHDU', 8, (10, 10), 'int32', '')])
        assert_equal(fits.info(self.temp('new1.fits'), output=False),
            [(0, 'PRIMARY', 'PrimaryHDU', 7, (), '', ''),
             (1, '', 'ImageHDU', 8, (), '', '')])

        hdul5 = stpyfits.open(self.temp('new.fits'))
        hdul6 = fits.open(self.temp('new1.fits'))
        assert_equal(hdul5[1].header['NAXIS'], 2)
        assert_equal(hdul6[1].header['NAXIS'], 0)
        assert_equal(hdul5[1].header['NAXIS1'], 10)
        assert_equal(hdul5[1].header['NAXIS2'], 10)

        assert_raises(KeyError, lambda: hdul6[1].header['NAXIS1'])
        assert_raises(KeyError, lambda: hdul6[1].header['NAXIS2'])
        assert_raises(KeyError, lambda: hdul5[1].header['NPIX1'])
        assert_raises(KeyError, lambda: hdul5[1].header['NPIX2'])

        assert_equal(hdul6[1].header['NPIX1'], 10)
        assert_equal(hdul6[1].header['NPIX2'], 10)

        assert_true((hdul5[1].data == np.ones((10, 10), dtype=np.int32)).all())

        assert_equal(hdul6[1].data, None)

        hdul5.close()
        hdul6.close()
        hdul.close()
        hdul1.close()

    def testupdateConvienceFunction(self):
        """Test the update convience function in both the fits and stpyfits
           namespace."""

        hdul = stpyfits.open(self.data('cdva2.fits'))
        hdul1 = fits.open(self.data('cdva2.fits'))

        header = hdul[0].header.copy()
        header['NAXIS'] = 0
        stpyfits.writeto(self.temp('new.fits'), hdul[0].data, header,
                         clobber=True)

        hdu = stpyfits.ImageHDU()
        hdu1 = fits.ImageHDU()

        hdu.data = hdul[0].data
        hdu1.data = hdul1[0].data
        hdu.header.set('BITPIX', 32)
        hdu1.header.set('BITPIX', 32)
        hdu.header.set('NAXIS', 0)
        hdu.header.set('PIXVALUE', 1, 'Constant pixel value', after='GCOUNT')
        hdu1.header.set('PIXVALUE', 1, 'Constant pixel value', after='GCOUNT')
        hdu.header.set('NPIX1', 10, 'length of constant array axis 1',
                       after='GCOUNT')
        hdu.header.set('NPIX2', 10, 'length of constant array axis 2',
                       after='NPIX1')
        stpyfits.append(self.temp('new.fits'), hdu.data, hdu.header)

        d = hdu.data * 0

        stpyfits.update(self.temp('new.fits'), d, hdu.header, 1)

        assert_equal(fits.info(self.temp('new.fits'), output=False),
            [(0, 'PRIMARY', 'PrimaryHDU', 7, (), '', ''),
             (1, '', 'ImageHDU', 8, (), '', '')])
        assert_equal(stpyfits.info(self.temp('new.fits'), output=False),
            [(0, 'PRIMARY', 'PrimaryHDU', 7, (10, 10), 'int32', ''),
             (1, '', 'ImageHDU', 8, (10, 10), 'int32', '')])

        hdul7 = stpyfits.open(self.temp('new.fits'))
        assert_equal(hdul7[1].header['NAXIS'], 2)
        assert_equal(hdul7[1].header['NAXIS1'], 10)
        assert_equal(hdul7[1].header['NAXIS2'], 10)
        assert_equal(hdul7[1].header['PIXVALUE'], 0)

        assert_raises(KeyError, lambda: hdul7[1].header['NPIX1'])
        assert_raises(KeyError, lambda: hdul7[1].header['NPIX2'])

        assert_true((hdul7[1].data ==
                     np.zeros((10, 10), dtype=np.int32)).all())

        hdul8 = fits.open(self.temp('new.fits'))
        assert_equal(hdul8[1].header['NAXIS'], 0)
        assert_equal(hdul8[1].header['NPIX1'], 10)
        assert_equal(hdul8[1].header['NPIX2'], 10)
        assert_equal(hdul8[1].header['PIXVALUE'], 0)

        assert_raises(KeyError, lambda: hdul8[1].header['NAXIS1'])
        assert_raises(KeyError, lambda: hdul8[1].header['NAXIS2'])

        assert_equal(hdul8[1].data, None)

        hdul7.close()
        hdul8.close()
        hdul.close()
        hdul1.close()

    def testImageHDUConstructor(self):
        """Test the ImageHDU constructor in both the fits and stpyfits
           namespace."""

        hdu = stpyfits.ImageHDU()
        assert_true(isinstance(hdu, stpyfits.ConstantValueImageHDU))
        hdu1 = fits.ImageHDU()
        assert_true(isinstance(hdu, fits.ImageHDU))

    def testPrimaryHDUConstructor(self):
        """Test the PrimaryHDU constructor in both the fits and stpyfits
           namespace.  Although stpyfits does not reimplement the
           constructor, it does add _ConstantValueImageBaseHDU to the
           inheritance hierarchy of fits.PrimaryHDU when accessed through the
           stpyfits namespace.  This method tests that that inheritance is
           working"""

        n = np.zeros(10)
        n = n + 1

        hdu = stpyfits.PrimaryHDU(n)
        hdu.header.set('PIXVALUE', 1.0, 'Constant pixel value', after='EXTEND')
        hdu.header.set('NAXIS', 0)
        stpyfits.writeto(self.temp('new.fits'), hdu.data, hdu.header,
                         clobber=True)
        hdul = stpyfits.open(self.temp('new.fits'))
        hdul1 = fits.open(self.temp('new.fits'))

        assert_equal(hdul[0].header['NAXIS'], 1)
        assert_equal(hdul[0].header['NAXIS1'], 10)
        assert_equal(hdul[0].header['PIXVALUE'], 1.0)

        assert_raises(KeyError, lambda: hdul[0].header['NPIX1'])

        assert_true((hdul[0].data == np.ones(10, dtype=np.float32)).all())

        assert_equal(hdul1[0].header['NAXIS'], 0)
        assert_equal(hdul1[0].header['NPIX1'], 10)
        assert_equal(hdul1[0].header['PIXVALUE'], 1.0)

        assert_raises(KeyError, lambda: hdul1[0].header['NAXIS1'])

        assert_equal(hdul1[0].data, None)

        hdul.close()
        hdul1.close()

    def testHDUListWritetoMethod(self):
        """Test the writeto method of HDUList in both the fits and stpyfits
           namespace."""

        hdu = stpyfits.PrimaryHDU()
        hdu1 = stpyfits.ImageHDU()
        hdu.data = np.zeros((10, 10), dtype=np.int32)
        hdu1.data = hdu.data + 2
        hdu.header.set('BITPIX', 32)
        hdu1.header.set('BITPIX', 32)
        hdu.header.set('NAXIS', 2)
        hdu.header.set('NAXIS1', 10, 'length of constant array axis 1',
                       after='NAXIS')
        hdu.header.set('NAXIS2', 10, 'length of constant array axis 2',
                       after='NAXIS1')
        hdu.header.set('PIXVALUE', 0, 'Constant pixel value')
        hdu1.header.set('PIXVALUE', 2, 'Constant pixel value', after='GCOUNT')
        hdu1.header.set('NAXIS', 2)
        hdu1.header.set('NAXIS1', 10, 'length of constant array axis 1',
                        after='NAXIS')
        hdu1.header.set('NAXIS2', 10, 'length of constant array axis 2',
                        after='NAXIS1')
        hdul = stpyfits.HDUList([hdu,hdu1])
        hdul.writeto(self.temp('new.fits'), clobber=True)

        assert_equal(stpyfits.info(self.temp('new.fits'), output=False),
            [(0, 'PRIMARY', 'PrimaryHDU', 7, (10, 10), 'int32', ''),
             (1, '', 'ImageHDU', 8, (10, 10), 'int32', '')])

        assert_equal(fits.info(self.temp('new.fits'), output=False),
            [(0, 'PRIMARY', 'PrimaryHDU', 7, (), '', ''),
             (1, '', 'ImageHDU', 8, (), '', '')])

        hdul1 = stpyfits.open(self.temp('new.fits'))
        hdul2 = fits.open(self.temp('new.fits'))

        assert_equal(hdul1[0].header['NAXIS'], 2)
        assert_equal(hdul1[0].header['NAXIS1'], 10)
        assert_equal(hdul1[0].header['NAXIS2'], 10)
        assert_equal(hdul1[0].header['PIXVALUE'], 0)

        assert_raises(KeyError, lambda: hdul1[0].header['NPIX1'])
        assert_raises(KeyError, lambda: hdul1[0].header['NPIX2'])

        assert_true((hdul1[0].data ==
                     np.zeros((10, 10), dtype=np.int32)).all())

        assert_equal(hdul1[1].header['NAXIS'], 2)
        assert_equal(hdul1[1].header['NAXIS1'], 10)
        assert_equal(hdul1[1].header['NAXIS2'], 10)
        assert_equal(hdul1[1].header['PIXVALUE'], 2)

        assert_raises(KeyError, lambda: hdul1[1].header['NPIX1'])
        assert_raises(KeyError, lambda: hdul1[1].header['NPIX2'])

        assert_true((hdul1[1].data ==
                     (np.zeros((10, 10), dtype=np.int32) + 2)).all())

        assert_equal(hdul2[0].header['NAXIS'], 0)
        assert_equal(hdul2[0].header['NPIX1'], 10)
        assert_equal(hdul2[0].header['NPIX2'], 10)
        assert_equal(hdul2[0].header['PIXVALUE'], 0)

        assert_raises(KeyError, lambda: hdul2[0].header['NAXIS1'])
        assert_raises(KeyError, lambda: hdul2[0].header['NAXIS2'])

        assert_equal(hdul2[0].data, None)

        assert_equal(hdul2[1].header['NAXIS'], 0)
        assert_equal(hdul2[1].header['NPIX1'], 10)
        assert_equal(hdul2[1].header['NPIX2'], 10)
        assert_equal(hdul2[1].header['PIXVALUE'], 2)

        assert_raises(KeyError, lambda: hdul2[1].header['NAXIS1'])
        assert_raises(KeyError, lambda: hdul2[1].header['NAXIS2'])

        hdul1.close()
        hdul2.close()

    def testHDUList__getitem__Method(self):
        """Test the __getitem__ method of st_HDUList in the stpyfits
           namespace."""

        n = np.zeros(10)
        n = n + 1

        hdu = stpyfits.PrimaryHDU(n)
        hdu.header.set('PIXVALUE', 1., 'constant pixel value', after='EXTEND')

        hdu.writeto(self.temp('new.fits'), clobber=True)

        hdul = stpyfits.open(self.temp('new.fits'))
        hdul1 = fits.open(self.temp('new.fits'))

        hdu = hdul[0]
        hdu1 = hdul1[0]

        assert_equal(hdu.header['NAXIS'], 1)
        assert_equal(hdu.header['NAXIS1'], 10)
        assert_equal(hdu.header['PIXVALUE'], 1.0)

        assert_raises(KeyError, lambda: hdu.header['NPIX1'])

        assert_true((hdu.data == np.ones(10, dtype=np.float32)).all())
        assert_equal(hdu1.header['NAXIS'], 0)
        assert_equal(hdu1.header['NPIX1'], 10)
        assert_equal(hdu1.header['PIXVALUE'], 1.0)

        assert_raises(KeyError, lambda: hdu1.header['NAXIS1'])

        assert_equal(hdu1.data, None)

        hdul.close()
        hdul1.close()

    def testHDUListFlushMethod(self):
        """Test the flush method of HDUList in both the fits and stpyfits
           namespace."""

        hdu = stpyfits.PrimaryHDU()
        hdu1 = stpyfits.ImageHDU()
        hdu.data = np.zeros((10, 10), dtype=np.int32)
        hdu1.data = hdu.data + 2
        hdu.header.set('BITPIX', 32)
        hdu1.header.set('BITPIX', 32)
        hdu.header.set('NAXIS', 2)
        hdu.header.set('NAXIS1', 10, 'length of constant array axis 1',
                       after='NAXIS')
        hdu.header.set('NAXIS2', 10, 'length of constant array axis 2',
                       after='NAXIS1')
        hdu.header.set('PIXVALUE', 0, 'Constant pixel value')
        hdu1.header.set('PIXVALUE', 2, 'Constant pixel value', after='GCOUNT')
        hdu1.header.set('NAXIS', 2)
        hdu1.header.set('NAXIS1', 10, 'length of constant array axis 1',
                        after='NAXIS')
        hdu1.header.set('NAXIS2', 10, 'length of constant array axis 2',
                        after='NAXIS1')
        hdul = stpyfits.HDUList([hdu, hdu1])
        hdul.writeto(self.temp('new.fits'), clobber=True)

        hdul = stpyfits.open(self.temp('new.fits'), 'update')
        d = np.arange(10, dtype=np.int32)
        d = d * 0
        d = d + 3
        hdul[0].data = d
        hdul.flush()
        hdul.close()

        assert_equal(stpyfits.info(self.temp('new.fits'), output=False),
            [(0, 'PRIMARY', 'PrimaryHDU', 6, (10,), 'int32', ''),
             (1, '', 'ImageHDU', 8, (10, 10), 'int32', '')])
        assert_equal(fits.info(self.temp('new.fits'), output=False),
            [(0, 'PRIMARY', 'PrimaryHDU', 6, (), '', ''),
             (1, '', 'ImageHDU', 8, (), '', '')])

        hdul1 = stpyfits.open(self.temp('new.fits'))
        hdul2 = fits.open(self.temp('new.fits'))

        assert_equal(hdul1[0].header['NAXIS'], 1)
        assert_equal(hdul1[0].header['NAXIS1'], 10)
        assert_equal(hdul1[0].header['PIXVALUE'], 3)

        assert_raises(KeyError, lambda: hdul1[0].header['NPIX1'])

        assert_true((hdul1[0].data ==
                     (np.zeros(10, dtype=np.int32) + 3)).all())

        assert_equal(hdul2[0].header['NAXIS'], 0)
        assert_equal(hdul2[0].header['NPIX1'], 10)
        assert_equal(hdul2[0].header['PIXVALUE'], 3)

        assert_raises(KeyError, lambda: hdul2[0].header['NAXIS1'])

        assert_equal(hdul2[0].data, None)

        hdul1.close()
        hdul2.close()

        hdul3 = stpyfits.open(self.temp('new.fits'), 'update')
        d = np.arange(15, dtype=np.int32)
        d = d * 0
        d = d + 4
        hdul3[0].data = d
        hdul3.close()      # Note that close calls flush

        assert_equal(stpyfits.info(self.temp('new.fits'), output=False),
            [(0, 'PRIMARY', 'PrimaryHDU', 6, (15,), 'int32', ''),
             (1, '', 'ImageHDU', 8, (10, 10), 'int32', '')])
        assert_equal(fits.info(self.temp('new.fits'), output=False),
            [(0, 'PRIMARY', 'PrimaryHDU', 6, (), '', ''),
             (1, '', 'ImageHDU', 8, (), '', '')])

        hdul1 = stpyfits.open(self.temp('new.fits'))
        hdul2 = fits.open(self.temp('new.fits'))

        assert_equal(hdul1[0].header['NAXIS'], 1)
        assert_equal(hdul1[0].header['NAXIS1'], 15)
        assert_equal(hdul1[0].header['PIXVALUE'], 4)

        assert_raises(KeyError, lambda: hdul1[0].header['NPIX1'])

        assert_true((hdul1[0].data ==
                     (np.zeros(15, dtype=np.int32) + 4)).all())

        assert_equal(hdul2[0].header['NAXIS'], 0)
        assert_equal(hdul2[0].header['NPIX1'], 15)
        assert_equal(hdul2[0].header['PIXVALUE'], 4)

        assert_raises(KeyError, lambda: hdul2[0].header['NAXIS1'])

        assert_equal(hdul2[0].data, None)

        hdul1.close()
        hdul2.close()

    def testImageBaseHDU__getattr__Method(self):
        """Test the __getattr__ method of ImageBaseHDU in both the fits
           and stpyfits namespace."""

        hdul = stpyfits.open(self.data('cdva2.fits'))
        hdul1 = fits.open(self.data('cdva2.fits'))

        hdu = hdul[0]
        hdu1 = hdul1[0]

        assert_true((hdu.data == np.ones((10, 10), dtype=np.int32)).all())
        assert_equal(hdu1.data, None)

        hdul.close()
        hdul1.close()

    def testImageBaseHDUWriteToMethod(self):
        """Test the writeto method of _ConstantValueImageBaseHDU in the
        stpyfits namespace."""

        n = np.zeros(10)
        n = n + 1

        hdu = stpyfits.PrimaryHDU(n)
        hdu.header.set('PIXVALUE', 1., 'constant pixel value', after='EXTEND')

        hdu.writeto(self.temp('new.fits'), clobber=True)

        hdul = stpyfits.open(self.temp('new.fits'))
        hdul1 = fits.open(self.temp('new.fits'))

        assert_equal(hdul[0].header['NAXIS'], 1)
        assert_equal(hdul[0].header['NAXIS1'], 10)
        assert_equal(hdul[0].header['PIXVALUE'], 1.0)

        assert_raises(KeyError, lambda: hdul[0].header['NPIX1'])

        assert_true((hdul[0].data == np.ones(10, dtype=np.float32)).all())

        assert_equal(hdul1[0].header['NAXIS'], 0)
        assert_equal(hdul1[0].header['NPIX1'], 10)
        assert_equal(hdul1[0].header['PIXVALUE'], 1.0)

        assert_raises(KeyError, lambda: hdul1[0].header['NAXIS1'])

        assert_equal(hdul1[0].data, None)

        hdul.close()
        hdul1.close()

    def testStrayPixvalue(self):
        """Regression test for #885
        (https://svn.stsci.edu/trac/ssb/stsci_python/ticket/885)

        Tests that HDUs containing a non-zero NAXIS as well as a PIXVALUE
        keyword in their header are not treated as constant value HDUs.
        """

        data = np.arange(100).reshape((10, 10))
        phdu = fits.PrimaryHDU(data=data)
        hdu = fits.ImageHDU(data=data)

        phdu.header['PIXVALUE'] = 10
        hdu.header['PIXVALUE'] = 10

        hdul = fits.HDUList([phdu, hdu])
        hdul.writeto(self.temp('test.fits'))

        with stpyfits.open(self.temp('test.fits')) as h:
            assert_false(isinstance(h[0], stpyfits.ConstantValuePrimaryHDU))
            assert_false(isinstance(h[1], stpyfits.ConstantValueImageHDU))
            assert_true((h[0].data == data).all())
            assert_true((h[1].data == data).all())

    def testDimensionlessConstantValueArray(self):
        """Tests a case that was reported where an HDU can be a constant
        value HDU (it has a PIXVALUE and NAXIS=0) but NPIX1 = NPIX2 = 0 as
        well.
        """

        hdu = stpyfits.PrimaryHDU()
        hdu.header['NAXIS'] = 0
        hdu.header['BITPIX'] = 16
        hdu.header['NPIX1'] = 0
        hdu.header['NPIX2'] = 0
        hdu.header['PIXVALUE'] = 0

        hdu.writeto(self.temp('test.fits'))

        with stpyfits.open(self.temp('test.fits')) as h:
            assert_true(h[0].data is None)

            h.writeto(self.temp('test2.fits'))

    def testDeconvertConstantArray(self):
        """When a constant value array's data is overridden with non-
        constant data, test that when saving the file it removes
        all constant value array keywords and is treated as a normal image
        HDU.
        """

        data = np.ones((100, 100))
        hdu = stpyfits.PrimaryHDU(data=data)
        hdu.header['PIXVALUE'] = 1
        hdu.writeto(self.temp('test.fits'))

        with stpyfits.open(self.temp('test.fits'), mode='update') as h:
            assert_equal(h[0].header['PIXVALUE'], 1)
            h[0].data[20:80, 20:80] = 2

        with fits.open(self.temp('test.fits')) as h:
            assert_true('PIXVALUE' not in h[0].header)
            assert_true('NPIX1' not in h[0].header)
            assert_true('NPIX2' not in h[0].header)
            assert_equal(h[0].header.count('NAXIS'), 1)
            assert_equal(h[0].header['NAXIS'], 2)
            assert_equal(h[0].header['NAXIS1'], 100)
            assert_equal(h[0].header['NAXIS2'], 100)
            assert_equal(h[0].data.max(), 2)
            assert_equal(h[0].data.min(), 1)

    def testGetvalExtensionHDU(self):
        """Regression test for an issue that came up with the fact that
        ImageHDU has a different argument signature from PrimaryHDU.
        """

        data = np.ones((100, 100))
        hdu = stpyfits.ImageHDU(data=data)
        hdu.header['PIXVALUE'] = 1
        hdu.header['FOO'] = 'test'
        hdul = stpyfits.HDUList([stpyfits.PrimaryHDU(), hdu])
        hdul.writeto(self.temp('test.fits'))

        assert_equal(stpyfits.getval(self.temp('test.fits'), 'FOO', ext=1),
                     'test')
