import os
import tempfile

import pytest
from astropy.io.fits.tests import FitsTestCase

from stsci.tools import fileutil as F
from stsci.tools import stpyfits


class TestIsFits(FitsTestCase):
    def setup(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.temp_dir = tempfile.mkdtemp(prefix='isfits-test-')

    def test_isFits_fname(self):
        assert F.isFits(self.data('cdva2.fits')) == (True, 'simple')
        assert F.isFits(self.data('o4sp040b0_raw.fits')) == (True, 'mef')
        assert F.isFits(self.data('waivered.fits')) == (True, 'waiver')

        # isFits only verifies files with valid FITS extensions (.fits,...)
        # Does not matter if file does not exist.
        assert F.isFits(self.data('simple')) == (False, None)

        # But if it has FITS extension, should raise error if nonexistent.
        with pytest.raises(IOError):
            F.isFits('isfits/no_such_file.fits')

    def test_isFits_file_object(self):
        with stpyfits.open(self.data('cdva2.fits')) as f:
            assert F.isFits(f) == (True, 'simple')
        with stpyfits.open(self.data('o4sp040b0_raw.fits')) as f:
            assert F.isFits(f) == (True, 'mef')
        with stpyfits.open(self.data('waivered.fits')) as f:
            assert F.isFits(f) == (True, 'waiver')
