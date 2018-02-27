import doctest
import numpy as np
import pytest
from stsci.tools import gfit
from stsci.tools.gfit import gfit1d


''' TODO: Which one do we keep? Why run a doctest of the same test that's already here?
'''

def test_gaussfit():
    ''' Performs the doctest, but here, not there
    '''
    x = np.arange(10, 20, 0.1)
    y = 10 * np.e**(-(15 - x)**2 / 4)
    result = gfit1d(y, x, maxiter=20)

    assert result.status
    assert str(result.params) == '[10.         15.          1.41421356]'


def test_gfit_doctest():
    ''' Performs the doctest, but there, not here
    '''
    return doctest.testmod(gfit)
