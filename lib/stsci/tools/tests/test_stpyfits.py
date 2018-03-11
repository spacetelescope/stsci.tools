#!/usr/bin/env python
from __future__ import absolute_import, division  # confidence high

import os
import tempfile

import astropy
import numpy as np
import pytest
from astropy.io import fits
from astropy.io.fits.tests import FitsTestCase
from distutils.version import LooseVersion

from .. import stpyfits

ASTROPY_VER_GE13 = LooseVersion(astropy.__version__) >= LooseVersion('1.3')
ASTROPY_VER_GE20 = LooseVersion(astropy.__version__) >= LooseVersion('2.0')


class TestStpyfitsFunctions(FitsTestCase):
    def setup(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.temp_dir = tempfile.mkdtemp(prefix='stpyfits-test-')

        if ASTROPY_VER_GE13:
            self.writekwargs = {'overwrite': True}
        else:
            self.writekwargs = {'clobber': True}

    def test_InfoConvienceFunction(self):
        """Test the info convience function in both the fits and stpyfits
        namespace."""

        if ASTROPY_VER_GE20:
            ans1 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 215, (), '', ''),
                    (1, 'SCI', 1, 'ImageHDU', 141, (62, 44), 'int16 (rescales to uint16)', ''),
                    (2, 'ERR', 1, 'ImageHDU', 71, (62, 44), 'int16', ''),
                    (3, 'DQ', 1, 'ImageHDU', 71, (62, 44), 'int16', ''),
                    (4, 'SCI', 2, 'ImageHDU', 141, (62, 44), 'int16 (rescales to uint16)', ''),
                    (5, 'ERR', 2, 'ImageHDU', 71, (62, 44), 'int16', ''),
                    (6, 'DQ', 2, 'ImageHDU', 71, (62, 44), 'int16', '')]
            ans2 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 215, (), '', ''),
                    (1, 'SCI', 1, 'ImageHDU', 141, (62, 44), 'int16 (rescales to uint16)', ''),
                    (2, 'ERR', 1, 'ImageHDU', 71, (), '', ''),
                    (3, 'DQ', 1, 'ImageHDU', 71, (), '', ''),
                    (4, 'SCI', 2, 'ImageHDU', 141, (62, 44), 'int16 (rescales to uint16)', ''),
                    (5, 'ERR', 2, 'ImageHDU', 71, (), '', ''),
                    (6, 'DQ', 2, 'ImageHDU', 71, (), '', '')]
            ans3 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 7, (10, 10), 'int32', '')]
            ans4 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 7, (), '', '')]
        else:
            ans1 = [(0, 'PRIMARY', 'PrimaryHDU', 215, (), '', ''),
                    (1, 'SCI', 'ImageHDU', 141, (62, 44), 'int16 (rescales to uint16)', ''),
                    (2, 'ERR', 'ImageHDU', 71, (62, 44), 'int16', ''),
                    (3, 'DQ', 'ImageHDU', 71, (62, 44), 'int16', ''),
                    (4, 'SCI', 'ImageHDU', 141, (62, 44), 'int16 (rescales to uint16)', ''),
                    (5, 'ERR', 'ImageHDU', 71, (62, 44), 'int16', ''),
                    (6, 'DQ', 'ImageHDU', 71, (62, 44), 'int16', '')]
            ans2 = [(0, 'PRIMARY', 'PrimaryHDU', 215, (), '', ''),
                    (1, 'SCI', 'ImageHDU', 141, (62, 44), 'int16 (rescales to uint16)', ''),
                    (2, 'ERR', 'ImageHDU', 71, (), '', ''),
                    (3, 'DQ', 'ImageHDU', 71, (), '', ''),
                    (4, 'SCI', 'ImageHDU', 141, (62, 44), 'int16 (rescales to uint16)', ''),
                    (5, 'ERR', 'ImageHDU', 71, (), '', ''),
                    (6, 'DQ', 'ImageHDU', 71, (), '', '')]
            ans3 = [(0, 'PRIMARY', 'PrimaryHDU', 7, (10, 10), 'int32', '')]
            ans4 = [(0, 'PRIMARY', 'PrimaryHDU', 7, (), '', '')]

        assert stpyfits.info(self.data('o4sp040b0_raw.fits'), output=False) == ans1
        assert fits.info(self.data('o4sp040b0_raw.fits'), output=False) == ans2

        assert stpyfits.info(self.data('cdva2.fits'), output=False) == ans3
        assert fits.info(self.data('cdva2.fits'), output=False) == ans4

    def test_OpenConvienceFunction(self):
        """Test the open convience function in both the fits and stpyfits
        namespace."""

        hdul = stpyfits.open(self.data('cdva2.fits'))
        hdul1 = fits.open(self.data('cdva2.fits'))

        assert hdul[0].header['NAXIS'] == 2
        assert hdul1[0].header['NAXIS'] == 0
        assert hdul[0].header['NAXIS1'] == 10
        assert hdul[0].header['NAXIS2'] == 10

        for k in ('NAXIS1', 'NAXIS2'):
            with pytest.raises(KeyError):
                hdul1[0].header[k]
        for k in ('NPIX1', 'NPIX2'):
            with pytest.raises(KeyError):
                hdul[0].header[k]

        assert hdul1[0].header['NPIX1'] == 10
        assert hdul1[0].header['NPIX2'] == 10

        assert (hdul[0].data == np.ones((10, 10), dtype=np.int32)).all()

        assert hdul1[0].data is None

        hdul.close()
        hdul1.close()

    @pytest.mark.parametrize(['filename', 'ext', 'naxis1', 'naxis2'],
                             [('cdva2.fits', None, 10, 10),
                              ('o4sp040b0_raw.fits', 2, 62, 44)])
    def test_GetHeaderConvienceFunction(self, filename, ext, naxis1, naxis2):
        """Test the getheader convience function in both the fits and
        stpyfits namespace."""

        if ext is None:
            hd = stpyfits.getheader(self.data(filename))
            hd1 = fits.getheader(self.data(filename))
        else:
            hd = stpyfits.getheader(self.data(filename), ext)
            hd1 = fits.getheader(self.data(filename), ext)

        assert hd['NAXIS'] == 2
        assert hd1['NAXIS'] == 0
        assert hd['NAXIS1'] == naxis1
        assert hd['NAXIS2'] == naxis2

        for k in ('NAXIS1', 'NAXIS2'):
            with pytest.raises(KeyError):
                hd1[k]
        for k in ('NPIX1', 'NPIX2'):
            with pytest.raises(KeyError):
                hd[k]

        assert hd1['NPIX1'] == naxis1
        assert hd1['NPIX2'] == naxis2

    def test_GetDataConvienceFunction(self):
        """Test the getdata convience function in both the fits and
        stpyfits namespace."""

        d = stpyfits.getdata(self.data('cdva2.fits'))
        assert (d == np.ones((10, 10), dtype=np.int32)).all()
        with pytest.raises(IndexError):
            fits.getdata(self.data('cdva2.fits'))

    def test_GetValConvienceFunction(self):
        """Test the getval convience function in both the fits and
        stpyfits namespace."""

        val = stpyfits.getval(self.data('cdva2.fits'), 'NAXIS', 0)
        val1 = fits.getval(self.data('cdva2.fits'), 'NAXIS', 0)
        assert val == 2
        assert val1 == 0

    def test_writetoConvienceFunction(self):
        """Test the writeto convience function in both the fits and stpyfits
        namespace."""

        hdul = stpyfits.open(self.data('cdva2.fits'))
        hdul1 = fits.open(self.data('cdva2.fits'))

        header = hdul[0].header.copy()
        header['NAXIS'] = 0

        stpyfits.writeto(self.temp('new.fits'), hdul[0].data, header,
                         **self.writekwargs)
        fits.writeto(self.temp('new1.fits'), hdul1[0].data, hdul1[0].header,
                     **self.writekwargs)

        hdul.close()
        hdul1.close()

        info1 = fits.info(self.temp('new.fits'), output=False)
        info2 = stpyfits.info(self.temp('new.fits'), output=False)
        info3 = fits.info(self.temp('new1.fits'), output=False)
        info4 = stpyfits.info(self.temp('new1.fits'), output=False)

        if ASTROPY_VER_GE20:
            ans1 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 6, (), '', '')]
            ans2 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 6, (10, 10), 'int32', '')]
            ans3 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 6, (), '', '')]
            ans4 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 6, (10, 10), 'uint8', '')]
        else:
            ans1 = [(0, 'PRIMARY', 'PrimaryHDU', 6, (), '', '')]
            ans2 = [(0, 'PRIMARY', 'PrimaryHDU', 6, (10, 10), 'int32', '')]
            ans3 = [(0, 'PRIMARY', 'PrimaryHDU', 6, (), '', '')]
            ans4 = [(0, 'PRIMARY', 'PrimaryHDU', 6, (10, 10), 'uint8', '')]

        assert info1 == ans1
        assert info2 == ans2
        assert info3 == ans3
        assert info4 == ans4

    def test_appendConvienceFunction(self):
        """Test the append convience function in both the fits and stpyfits
        namespace."""

        hdul = stpyfits.open(self.data('cdva2.fits'))
        hdul1 = fits.open(self.data('cdva2.fits'))

        stpyfits.writeto(self.temp('new.fits'), hdul[0].data, hdul[0].header,
                         **self.writekwargs)
        fits.writeto(self.temp('new1.fits'), hdul1[0].data, hdul1[0].header,
                     **self.writekwargs)

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

        if ASTROPY_VER_GE20:
            ans1 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 7, (10, 10), 'int32', ''),
                    (1, '', 1, 'ImageHDU', 8, (10, 10), 'int32', '')]
            ans2 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 7, (10, 10), 'uint8', ''),
                    (1, '', 1, 'ImageHDU', 8, (10, 10), 'uint8', '')]
            ans3 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 7, (10, 10), 'int32', ''),
                    (1, '', 1, 'ImageHDU', 8, (10, 10), 'int32', '')]
            ans4 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 7, (), '', ''),
                    (1, '', 1, 'ImageHDU', 8, (), '', '')]
        else:
            ans1 = [(0, 'PRIMARY', 'PrimaryHDU', 7, (10, 10), 'int32', ''),
                    (1, '', 'ImageHDU', 8, (10, 10), 'int32', '')]
            ans2 = [(0, 'PRIMARY', 'PrimaryHDU', 7, (10, 10), 'uint8', ''),
                    (1, '', 'ImageHDU', 8, (10, 10), 'uint8', '')]
            ans3 = [(0, 'PRIMARY', 'PrimaryHDU', 7, (10, 10), 'int32', ''),
                    (1, '', 'ImageHDU', 8, (10, 10), 'int32', '')]
            ans4 = [(0, 'PRIMARY', 'PrimaryHDU', 7, (), '', ''),
                    (1, '', 'ImageHDU', 8, (), '', '')]

        assert stpyfits.info(self.temp('new.fits'), output=False) == ans1
        assert stpyfits.info(self.temp('new1.fits'), output=False) == ans2
        assert fits.info(self.temp('new.fits'), output=False) == ans3
        assert fits.info(self.temp('new1.fits'), output=False) == ans4

        hdul5 = stpyfits.open(self.temp('new.fits'))
        hdul6 = fits.open(self.temp('new1.fits'))

        assert hdul5[1].header['NAXIS'] == 2
        assert hdul6[1].header['NAXIS'] == 0
        assert hdul5[1].header['NAXIS1'] == 10
        assert hdul5[1].header['NAXIS2'] == 10

        for k in ('NPIX1', 'NPIX2'):
            with pytest.raises(KeyError):
                hdul5[1].header[k]
        for k in ('NAXIS1', 'NAXIS2'):
            with pytest.raises(KeyError):
                hdul6[1].header[k]

        assert hdul6[1].header['NPIX1'] == 10
        assert hdul6[1].header['NPIX2'] == 10
        assert (hdul5[1].data == np.ones((10, 10), dtype=np.int32)).all()
        assert hdul6[1].data is None

        hdul5.close()
        hdul6.close()
        hdul.close()
        hdul1.close()

    def test_updateConvienceFunction(self):
        """Test the update convience function in both the fits and stpyfits
        namespace."""

        hdul = stpyfits.open(self.data('cdva2.fits'))
        hdul1 = fits.open(self.data('cdva2.fits'))

        header = hdul[0].header.copy()
        header['NAXIS'] = 0

        stpyfits.writeto(self.temp('new.fits'), hdul[0].data, header,
                         **self.writekwargs)

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

        d = np.zeros_like(hdu.data)

        stpyfits.update(self.temp('new.fits'), d, hdu.header, 1)

        if ASTROPY_VER_GE20:
            ans1 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 7, (), '', ''),
                    (1, '', 1, 'ImageHDU', 8, (), '', '')]
            ans2 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 7, (10, 10), 'int32', ''),
                    (1, '', 1, 'ImageHDU', 8, (10, 10), 'int32', '')]
        else:
            ans1 = [(0, 'PRIMARY', 'PrimaryHDU', 7, (), '', ''),
                    (1, '', 'ImageHDU', 8, (), '', '')]
            ans2 = [(0, 'PRIMARY', 'PrimaryHDU', 7, (10, 10), 'int32', ''),
                    (1, '', 'ImageHDU', 8, (10, 10), 'int32', '')]

        assert fits.info(self.temp('new.fits'), output=False) == ans1
        assert stpyfits.info(self.temp('new.fits'), output=False) == ans2

        hdul7 = stpyfits.open(self.temp('new.fits'))
        assert hdul7[1].header['NAXIS'] == 2
        assert hdul7[1].header['NAXIS1'] == 10
        assert hdul7[1].header['NAXIS2'] == 10
        assert hdul7[1].header['PIXVALUE'] == 0

        for k in ('NPIX1', 'NPIX2'):
            with pytest.raises(KeyError):
                hdul7[1].header[k]

        assert (hdul7[1].data == np.zeros((10, 10), dtype=np.int32)).all()

        hdul8 = fits.open(self.temp('new.fits'))
        assert hdul8[1].header['NAXIS'] == 0
        assert hdul8[1].header['NPIX1'] == 10
        assert hdul8[1].header['NPIX2'] == 10
        assert hdul8[1].header['PIXVALUE'] == 0

        for k in ('NAXIS1', 'NAXIS2'):
            with pytest.raises(KeyError):
                hdul8[1].header[k]

        assert hdul8[1].data is None

        hdul7.close()
        hdul8.close()
        hdul.close()
        hdul1.close()

    def test_ImageHDUConstructor(self):
        """Test the ImageHDU constructor in both the fits and stpyfits
        namespace."""

        hdu = stpyfits.ImageHDU()
        assert isinstance(hdu, stpyfits.ConstantValueImageHDU)
        assert isinstance(hdu, fits.ImageHDU)

    def test_PrimaryHDUConstructor(self):
        """Test the PrimaryHDU constructor in both the fits and stpyfits
        namespace.  Although stpyfits does not reimplement the
        constructor, it does add _ConstantValueImageBaseHDU to the
        inheritance hierarchy of fits.PrimaryHDU when accessed through the
        stpyfits namespace.  This method tests that that inheritance is
        working"""

        n = np.ones(10)

        hdu = stpyfits.PrimaryHDU(n)
        hdu.header.set('PIXVALUE', 1.0, 'Constant pixel value', after='EXTEND')
        hdu.header.set('NAXIS', 0)

        stpyfits.writeto(self.temp('new.fits'), hdu.data, hdu.header,
                         **self.writekwargs)

        hdul = stpyfits.open(self.temp('new.fits'))
        hdul1 = fits.open(self.temp('new.fits'))

        assert hdul[0].header['NAXIS'] == 1
        assert hdul[0].header['NAXIS1'] == 10
        assert hdul[0].header['PIXVALUE'] == 1.0

        with pytest.raises(KeyError):
            hdul[0].header['NPIX1']

        assert (hdul[0].data == np.ones(10, dtype=np.float32)).all()

        assert hdul1[0].header['NAXIS'] == 0
        assert hdul1[0].header['NPIX1'] == 10
        assert hdul1[0].header['PIXVALUE'] == 1.0

        with pytest.raises(KeyError):
            hdul1[0].header['NAXIS1']

        assert hdul1[0].data is None

        hdul.close()
        hdul1.close()

    def test_HDUListWritetoMethod(self):
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
        hdul = stpyfits.HDUList([hdu, hdu1])

        hdul.writeto(self.temp('new.fits'), **self.writekwargs)

        if ASTROPY_VER_GE20:
            ans1 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 7, (10, 10), 'int32', ''),
                    (1, '', 1, 'ImageHDU', 8, (10, 10), 'int32', '')]
            ans2 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 7, (), '', ''),
                    (1, '', 1, 'ImageHDU', 8, (), '', '')]
        else:
            ans1 = [(0, 'PRIMARY', 'PrimaryHDU', 7, (10, 10), 'int32', ''),
                    (1, '', 'ImageHDU', 8, (10, 10), 'int32', '')]
            ans2 = [(0, 'PRIMARY', 'PrimaryHDU', 7, (), '', ''),
                    (1, '', 'ImageHDU', 8, (), '', '')]

        assert stpyfits.info(self.temp('new.fits'), output=False) == ans1
        assert fits.info(self.temp('new.fits'), output=False) == ans2

        hdul1 = stpyfits.open(self.temp('new.fits'))
        hdul2 = fits.open(self.temp('new.fits'))

        assert hdul1[0].header['NAXIS'] == 2
        assert hdul1[0].header['NAXIS1'] == 10
        assert hdul1[0].header['NAXIS2'] == 10
        assert hdul1[0].header['PIXVALUE'] == 0

        assert (hdul1[0].data == np.zeros((10, 10), dtype=np.int32)).all()

        assert hdul1[1].header['NAXIS'] == 2
        assert hdul1[1].header['NAXIS1'] == 10
        assert hdul1[1].header['NAXIS2'] == 10
        assert hdul1[1].header['PIXVALUE'] == 2

        assert (hdul1[1].data == (np.zeros((10, 10), dtype=np.int32) + 2)).all()

        assert hdul2[0].header['NAXIS'] == 0
        assert hdul2[0].header['NPIX1'] == 10
        assert hdul2[0].header['NPIX2'] == 10
        assert hdul2[0].header['PIXVALUE'] == 0

        for i in range(2):
            for k in ('NPIX1', 'NPIX2'):
                with pytest.raises(KeyError):
                    hdul1[i].header[k]
            for k in ('NAXIS1', 'NAXIS2'):
                with pytest.raises(KeyError):
                    hdul2[i].header[k]

        assert hdul2[0].data is None

        assert hdul2[1].header['NAXIS'] == 0
        assert hdul2[1].header['NPIX1'] == 10
        assert hdul2[1].header['NPIX2'] == 10
        assert hdul2[1].header['PIXVALUE'] == 2

        hdul1.close()
        hdul2.close()

    def test_HDUList_getitem_Method(self):
        """Test the __getitem__ method of st_HDUList in the stpyfits
        namespace."""

        n = np.ones(10)

        hdu = stpyfits.PrimaryHDU(n)
        hdu.header.set('PIXVALUE', 1., 'constant pixel value', after='EXTEND')

        hdu.writeto(self.temp('new.fits'), **self.writekwargs)

        hdul = stpyfits.open(self.temp('new.fits'))
        hdul1 = fits.open(self.temp('new.fits'))

        hdu = hdul[0]
        hdu1 = hdul1[0]

        assert hdu.header['NAXIS'] == 1
        assert hdu.header['NAXIS1'] == 10
        assert hdu.header['PIXVALUE'] == 1.0

        with pytest.raises(KeyError):
            hdu.header['NPIX1']

        assert (hdu.data == np.ones(10, dtype=np.float32)).all()
        assert hdu1.header['NAXIS'] == 0
        assert hdu1.header['NPIX1'] == 10
        assert hdu1.header['PIXVALUE'] == 1.0

        with pytest.raises(KeyError):
            hdu1.header['NAXIS1']

        assert hdu1.data is None

        hdul.close()
        hdul1.close()

    def test_HDUListFlushMethod(self):
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

        hdul.writeto(self.temp('new.fits'), **self.writekwargs)

        hdul = stpyfits.open(self.temp('new.fits'), 'update')
        hdul[0].data = np.zeros(10, dtype=np.int32) + 3
        hdul.flush()
        hdul.close()

        if ASTROPY_VER_GE20:
            ans1 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 6, (10,), 'int32', ''),
                    (1, '', 1, 'ImageHDU', 8, (10, 10), 'int32', '')]
            ans2 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 6, (), '', ''),
                    (1, '', 1, 'ImageHDU', 8, (), '', '')]
            ans3 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 6, (15,), 'int32', ''),
                    (1, '', 1, 'ImageHDU', 8, (10, 10), 'int32', '')]
            ans4 = [(0, 'PRIMARY', 1, 'PrimaryHDU', 6, (), '', ''),
                    (1, '', 1, 'ImageHDU', 8, (), '', '')]
        else:
            ans1 = [(0, 'PRIMARY', 'PrimaryHDU', 6, (10,), 'int32', ''),
                    (1, '', 'ImageHDU', 8, (10, 10), 'int32', '')]
            ans2 = [(0, 'PRIMARY', 'PrimaryHDU', 6, (), '', ''),
                    (1, '', 'ImageHDU', 8, (), '', '')]
            ans3 = [(0, 'PRIMARY', 'PrimaryHDU', 6, (15,), 'int32', ''),
                    (1, '', 'ImageHDU', 8, (10, 10), 'int32', '')]
            ans4 = [(0, 'PRIMARY', 'PrimaryHDU', 6, (), '', ''),
                    (1, '', 'ImageHDU', 8, (), '', '')]

        assert stpyfits.info(self.temp('new.fits'), output=False) == ans1
        assert fits.info(self.temp('new.fits'), output=False) == ans2

        hdul1 = stpyfits.open(self.temp('new.fits'))
        hdul2 = fits.open(self.temp('new.fits'))

        assert hdul1[0].header['NAXIS'] == 1
        assert hdul1[0].header['NAXIS1'] == 10
        assert hdul1[0].header['PIXVALUE'] == 3

        with pytest.raises(KeyError):
            hdul1[0].header['NPIX1']

        assert (hdul1[0].data == (np.zeros(10, dtype=np.int32) + 3)).all()

        assert hdul2[0].header['NAXIS'] == 0
        assert hdul2[0].header['NPIX1'] == 10
        assert hdul2[0].header['PIXVALUE'] == 3

        with pytest.raises(KeyError):
            hdul2[0].header['NAXIS1']

        assert hdul2[0].data is None

        hdul1.close()
        hdul2.close()

        hdul3 = stpyfits.open(self.temp('new.fits'), 'update')
        hdul3[0].data = np.zeros(15, dtype=np.int32) + 4
        hdul3.close()  # Note that close calls flush

        assert stpyfits.info(self.temp('new.fits'), output=False) == ans3
        assert fits.info(self.temp('new.fits'), output=False) == ans4

        hdul1 = stpyfits.open(self.temp('new.fits'))
        hdul2 = fits.open(self.temp('new.fits'))

        assert hdul1[0].header['NAXIS'] == 1
        assert hdul1[0].header['NAXIS1'] == 15
        assert hdul1[0].header['PIXVALUE'] == 4

        with pytest.raises(KeyError):
            hdul1[0].header['NPIX1']

        assert (hdul1[0].data == (np.zeros(15, dtype=np.int32) + 4)).all()

        assert hdul2[0].header['NAXIS'] == 0
        assert hdul2[0].header['NPIX1'] == 15
        assert hdul2[0].header['PIXVALUE'] == 4

        with pytest.raises(KeyError):
            hdul2[0].header['NAXIS1']

        assert hdul2[0].data is None

        hdul1.close()
        hdul2.close()

    def test_ImageBaseHDU_getattr_Method(self):
        """Test the __getattr__ method of ImageBaseHDU in both the fits
        and stpyfits namespace."""

        hdul = stpyfits.open(self.data('cdva2.fits'))
        hdul1 = fits.open(self.data('cdva2.fits'))

        hdu = hdul[0]
        hdu1 = hdul1[0]

        assert (hdu.data == np.ones((10, 10), dtype=np.int32)).all()
        assert hdu1.data is None

        hdul.close()
        hdul1.close()

    def test_ImageBaseHDUWriteToMethod(self):
        """Test the writeto method of _ConstantValueImageBaseHDU in the
        stpyfits namespace."""

        n = np.ones(10)

        hdu = stpyfits.PrimaryHDU(n)
        hdu.header.set('PIXVALUE', 1., 'constant pixel value', after='EXTEND')

        hdu.writeto(self.temp('new.fits'), **self.writekwargs)

        hdul = stpyfits.open(self.temp('new.fits'))
        hdul1 = fits.open(self.temp('new.fits'))

        assert hdul[0].header['NAXIS'] == 1
        assert hdul[0].header['NAXIS1'] == 10
        assert hdul[0].header['PIXVALUE'] == 1.0

        with pytest.raises(KeyError):
            hdul[0].header['NPIX1']

        assert (hdul[0].data == np.ones(10, dtype=np.float32)).all()

        assert hdul1[0].header['NAXIS'] == 0
        assert hdul1[0].header['NPIX1'] == 10
        assert hdul1[0].header['PIXVALUE'] == 1.0

        with pytest.raises(KeyError):
            hdul1[0].header['NAXIS1']

        assert hdul1[0].data is None

        hdul.close()
        hdul1.close()

    def test_StrayPixvalue(self):
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
            assert not isinstance(h[0], stpyfits.ConstantValuePrimaryHDU)
            assert not isinstance(h[1], stpyfits.ConstantValueImageHDU)
            assert (h[0].data == data).all()
            assert (h[1].data == data).all()

    def test_DimensionlessConstantValueArray(self):
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
            assert h[0].data is None
            h.writeto(self.temp('test2.fits'))

    def test_DeconvertConstantArray(self):
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
            assert h[0].header['PIXVALUE'] == 1
            h[0].data[20:80, 20:80] = 2

        with fits.open(self.temp('test.fits')) as h:
            assert 'PIXVALUE' not in h[0].header
            assert 'NPIX1' not in h[0].header
            assert 'NPIX2' not in h[0].header
            assert h[0].header.count('NAXIS') == 1
            assert h[0].header['NAXIS'] == 2
            assert h[0].header['NAXIS1'] == 100
            assert h[0].header['NAXIS2'] == 100
            assert h[0].data.max() == 2
            assert h[0].data.min() == 1

    def test_GetvalExtensionHDU(self):
        """Regression test for an issue that came up with the fact that
        ImageHDU has a different argument signature from PrimaryHDU.
        """

        data = np.ones((100, 100))
        hdu = stpyfits.ImageHDU(data=data)
        hdu.header['PIXVALUE'] = 1
        hdu.header['FOO'] = 'test'
        hdul = stpyfits.HDUList([stpyfits.PrimaryHDU(), hdu])
        hdul.writeto(self.temp('test.fits'))

        assert stpyfits.getval(self.temp('test.fits'), 'FOO', ext=1) == 'test'
