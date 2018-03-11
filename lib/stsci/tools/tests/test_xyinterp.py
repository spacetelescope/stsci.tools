from __future__ import absolute_import, division

import numpy as np
import pytest

from ..xyinterp import xyinterp


class TestXYInterp(object):
    def setup_class(self):
        self.x = np.arange(1, 6)
        self.y = self.x.copy()

    @pytest.mark.parametrize('val', [3, 3.5])
    def test_same_arr(self, val):
        assert xyinterp(self.x, self.y, val) == val

    @pytest.mark.parametrize('val', [-3, 5.6])
    def test_same_arr_err(self, val):
        with pytest.raises(ValueError):
            xyinterp(self.x, self.y, val)


def test_diff_arr():
    x = np.array([1, 3, 7, 9, 12])
    y = np.array([5, 10, 15, 20, 25])
    assert xyinterp(x, y, 8) == 17.5


@pytest.mark.parametrize(
    ('x', 'y'),
    [(np.array([5, 3, 6, 2, 7, 0]), np.array([4, 6, 2, 4, 6, 2])),
     (np.arange(1, 6), np.arange(20))])
def test_diff_arr_err(x, y):
    with pytest.raises(ValueError):
        xyinterp(x, y, 2)
