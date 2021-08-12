import multiprocessing
import time
import pytest
from itertools import product

from astropy.io import fits
from astropy.utils.data import get_pkg_data_filename

from stsci.tools.mputil import launch_and_wait, best_tile_layout


SUPPORTED_START_METHODS = []
for sm in ['spawn', 'fork', 'forkserver']:
    try:
        multiprocessing.get_context(sm)
        SUPPORTED_START_METHODS.append(sm)
    except ValueError:
        pass


def takes_time(x, img):
    """Example function which takes some time to run."""
    time.sleep(0.001)  # 1 ms is long by computer standards?


@pytest.mark.parametrize('fname, method', (
    x for x in product([None, 'data/o4sp040b0_raw.fits'],
                       SUPPORTED_START_METHODS)
))
def test_launch_and_wait(fname, method):
    """Illustrate use of launch_and_wait"""
    p = None
    subprocs = []
    # Passing fits.HDUList in Python 3.8 would cause crash due to spawn start
    # method:
    #
    if fname is None:
        img = None
    else:
        img = fits.open(get_pkg_data_filename(fname))

    for item in range(2, 5):
        mp_ctx = multiprocessing.get_context(method)
        p = mp_ctx.Process(target=takes_time, args=(item, img),
                           name='takes_time()')
        subprocs.append(p)

    if method != 'fork' and fname:
        with pytest.raises(TypeError):
            # launch em, pool-fashion
            launch_and_wait(subprocs, 3)
    else:
        launch_and_wait(subprocs, 3)

    if img:
        img.close()


def test_best_tile_layout():
    """Loop though some numbers and make sure we get expected results."""
    for i in range(257):
        x, y = best_tile_layout(i)
        assert (x * y <= i) or (i == 0), \
            "Total num resulting tiles > pool_size"
        unused_cores = i - (x * y)
        # print(i, (x,y), unused_cores)
        if i < 10:
            assert unused_cores <= 1, "Too many idle cores at i = " + str(i)
        else:
            percent_unused = 100. * ((unused_cores * 1.) / i)
            assert percent_unused < 14., "Too many idles cores at i: " + str(i)
