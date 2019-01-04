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
