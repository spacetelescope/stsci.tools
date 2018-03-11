#!/usr/bin/env python
#
from __future__ import division, print_function

import math
import time


class WatchedProcess(object):
    """ MINIMAL wrapper around multiprocessing.Process so we can more easily track/time them. """

    def __init__(self, proc):
        self.process = proc
        self.state = 0 # 0=not-yet-started; 1=started; 2=finished-or-terminated
        self._start_time = None

    def start_process(self):
        assert self.state == 0, "Already started: "+str(self.process)
        self._start_time = time.time()
        self.process.start()
        self.state = 1

    def join_process(self):
        assert self.state >= 1, "Not started: "+str(self.process)
        self.process.join()
        self.state = 2

    def time_since_started(self):
        assert self.state > 0, "Not yet started: "+str(self.process)
        return time.time() - self._start_time

    def __repr__(self):
        return "WatchedProcess for: "+str(self.process)+', state='+str(self.state)


def launch_and_wait(mp_proc_list, pool_size):
    """ Given a list of multiprocessing.Process objects which have not yet
    been started, this function launches them and blocks until the last
    finishes.  This makes sure that only <pool_size> processes are ever
    working at any one time (this number does not include the main process
    which called this function, since that will not tax the CPU).
    The idea here is roughly analogous to multiprocessing.Pool
    with the exceptions that:
        1 - The caller will get to use the multiprocessing.Process model of
            using shared memory (inheritance) to pass arg data to the child,
        2 - maxtasksperchild is always 1,
        3 - no function return value is kept/tranferred (not yet implemented)
    """

    # Sanity check
    if len(mp_proc_list) < 1:
        return

    # Create or own list with easy state watching
    procs = []
    for p in mp_proc_list:
        procs.append(WatchedProcess(p))

    # Launch all of them, but only so pool_size are running at any time
    keep_going = True
    while (keep_going):
        # Before we start any more, find out how many are running.  First go
        # through the list of those started and see if alive.  Update state.
        for p in procs:
            if p.state == 1: # been started
                if not p.process.is_alive():
                    p.state = 2 # process has finished or been terminated
                    assert p.process.exitcode is not None, \
                           "Process is not alive but has no exitcode? "+ \
                           str(p.process)

        # now figure num_running
        num_running = len([p for p in procs if p.state == 1])

        # Start some.  Only as many as pool_size should ever be running.
        num_avail_cpus = pool_size - num_running
        num_to_start = len([p for p in procs if p.state == 0])
        if num_to_start < 1:
            # all have been started, can finally leave loop and go wait
            break
        if num_avail_cpus > 0 and num_to_start > 0:
            num_to_start_now = min(num_avail_cpus, num_to_start)
            started_now = 0
            for p in procs:
                if started_now < num_to_start_now and p.state == 0:
                    p.start_process()
                    # debug "launch_and_wait: started: "+str(p.process)
                    started_now += 1
        # else: otherwise, all cpus are in use, just wait ...

        # sleep to tame loop activity, but also must sleep a bit after each
        # start call so that the call to is_alive() woorks correctly
        time.sleep(1)

    # Out of the launching loop, can now wait on all procs left.
    for p in procs:
        p.join_process()

    # Check all exit codes before returning
    for p in procs:
        if 0 != p.process.exitcode:
            raise RuntimeError("Problem during: "+str(p.process.name)+ \
                  ', exitcode: '+str(p.process.exitcode)+'. Check log.')
    # all is well, can return


def best_tile_layout(pool_size):
    """ Determine and return the best layout of "tiles" for fastest
    overall parallel processing of a rectangular image broken up into N
    smaller equally-sized rectangular tiles, given as input the number
    of processes/chunks which can be run/worked at the same time (pool_size).

    This attempts to return a layout whose total number of tiles is as
    close as possible to pool_size, without going over (and thus not
    really taking advantage of pooling).  Since we can vary the
    size of the rectangles, there is not much (any?) benefit to pooling.

    Returns a tuple of ( <num tiles in X dir>, <num in Y direction> )

    This assumes the image in question is relatively close to square, and
    so the returned tuple attempts to give a layout which is as
    squarishly-blocked as possible, except in cases where speed would be
    sacrificed.

    EXAMPLES:

    For pool_size of 4, the best result is 2x2.

    For pool_size of 6, the best result is 2x3.

    For pool_size of 5, a result of 1x5 is better than a result of
    2x2 (which would leave one core unused), and 1x5 is also better than
    a result of 2x3 (which would require one core to work twice while all
    others wait).

    For higher, odd pool_size values (say 39), it is deemed best to
    sacrifice a few unused cores to satisfy our other constraints, and thus
    the result of 6x6 is best (giving 36 tiles and 3 unused cores).
    """
    # Easy answer sanity-checks
    if pool_size < 2:
        return (1, 1)

    # Next, use a small mapping of hard-coded results.  While we agree
    # that many of these are unlikely pool_size values, they are easy
    # to accomodate.
    mapping = { 0:(1,1), 1:(1,1), 2:(1,2), 3:(1,3), 4:(2,2), 5:(1,5),
                6:(2,3), 7:(2,3), 8:(2,4), 9:(3,3), 10:(2,5), 11:(2,5),
                14:(2,7), 18:(3,6), 19:(3,6), 28:(4,7), 29:(4,7),
                32:(4,8), 33:(4,8), 34:(4,8), 40:(4,10), 41:(4,10) }
    if pool_size in mapping:
        return mapping[pool_size]

    # Next, take a guess using the square root and (for the sake of
    # simplicity), go with it.  We *could* get much fancier here...
    # Use floor-rounding (not ceil) so that the total number of resulting
    # tiles is <= pool_size.
    xnum = int(math.sqrt(pool_size))
    ynum = int((1.*pool_size)/xnum)
    return (xnum, ynum)
