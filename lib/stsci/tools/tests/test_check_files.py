import os
import shutil

from astropy.io import fits
from astropy.io.fits import diff

from stsci.tools import fileutil as fu
from stsci.tools import check_files

data_dir = os.path.join(os.path.dirname(__file__), 'data')


def test_exptime():
    fobj = fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU()])
    fobj[0].header['INSTRUME'] = 'ACS'
    fobj[0].header['filename'] = 'junk.fits'
    fobj[0].header['EXPTIME'] = 0.0

    assert check_files.check_exptime([fobj]) == [fobj]

    fobj[0].header['EXPTIME'] = 10.0

    assert check_files.check_exptime([fobj]) == []


def test_n_goodpix():
    fobj = fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU()])
    fobj[0].header['INSTRUME'] = 'ACS'
    fobj[0].header['filename'] = 'junk.fits'
    fobj[1].header['NGOODPIX'] = 0
    fobj[1].name = 'SCI'
    assert check_files.checkNGOODPIX([fobj]) == [fobj]

    fobj[1].header['NGOODPIX'] = 23
    assert check_files.checkNGOODPIX([fobj]) == []
    fobj.close()


def test_check_files():
    """ Test that ``checkFiles`` works with both file names and file objects."""

    fname = os.path.join(data_dir, 'acs_test.fits')
    result = check_files.checkFiles([fname])
    assert result == ([os.path.join(data_dir, 'acs_test.fits')], [None])

    with fits.open(fname) as fobj:
        result = check_files.checkFiles([fobj])
        assert isinstance(result[0][0], fits.HDUList)
        assert result[0][0].filename() == os.path.join(data_dir, 'acs_test.fits')
        assert result[1] == [None]

    fname = os.path.join(data_dir, 'o4sp040b0_raw.fits')
    assert check_files.checkFiles([fname]) == ([], [])


def test_waivered_fits(tmpdir):
    """
    Test converting wavered FITS to multiextension FITS.
    """
    c0f_name = 'u40x010hm_c0f.fits'
    c0h_name = 'u40x010hm_c0h.fits'
    path_name = os.path.join(data_dir, c0f_name)
    current_dir = os.getcwd()
    try:
        os.chdir(tmpdir)
        shutil.copyfile(path_name, c0f_name)
        check_files.checkFiles([c0f_name])
        with fits.open(c0f_name, mode='update') as fobj:
            fnew, _ = check_files.checkFiles([fobj])
            assert fu.isFits(fnew[0]) == (True, 'mef')
            report = diff.FITSDiff(fnew[0], c0h_name).report()
            assert report.splitlines()[-1] == 'No differences found.'
    finally:
        os.chdir(current_dir)
