from __future__ import absolute_import, print_function, division

import multiprocessing
import time

from ..mputil import launch_and_wait, best_tile_layout


def takes_time(x):
    """Example function which takes some time to run."""
    time.sleep(0.001)  # 1 ms is long by computer standards?


def test_launch_and_wait():
    """Illustrate use of launch_and_wait"""
    p = None
    subprocs = []

    for item in range(2, 10):
        # print(("mputil: instantiating Process for x = "+str(item)))
        p = multiprocessing.Process(target=takes_time, args=(item,),
                                    name='takes_time()')
        subprocs.append(p)

    # launch em, pool-fashion
    launch_and_wait(subprocs, 3)

    # NOTE: If no exception raised by now, considered passed.
    # by now, all should be finished
    # print("All subprocs should be finished and joined.")


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
