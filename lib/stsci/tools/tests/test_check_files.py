import os
import tempfile

import pytest
from astropy.io import fits

from .. import fileutil as fu
from .. import check_files

data_dir = os.path.join(os.path.dirname(__file__), 'data')

def test_n_goodpix():
    fobj = fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU()])
    fobj[0].header['INSTRUME'] = 'ACS'
    fobj[0].header['filename'] = 'junk.fits'
    fobj[1].header['NGOODPIX'] = 0
    fobj[1].name = 'SCI'
    assert check_files.checkNGOODPIX([fobj]) == ['']

    fobj[1].header['NGOODPIX'] = 23
    assert check_files.checkNGOODPIX([fobj]) == []
    fobj.close()


def test_check_files():
    """ Test that ``checkFiles`` works with both file names and file objects."""

    fname = os.path.join(data_dir, 'acs_test.fits')
    result = check_files.checkFiles([fname])
    assert  result == ([os.path.join(data_dir, 'acs_test.fits')], [None])

    fobj = fits.open(fname)
    result = check_files.checkFiles([fobj])
    assert isinstance(result[0][0], fits.HDUList)
    assert result[0][0].filename() == os.path.join(data_dir, 'acs_test.fits')
    assert result[1] == [None]

    fname = os.path.join(data_dir, 'o4sp040b0_raw.fits')
    assert check_files.checkFiles([fname]) == ([], [])
