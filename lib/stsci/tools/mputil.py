#!/usr/bin/env python
#
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
    num_total = len(procs)

    # Launch all of them, but only so pool_size are running at any time
    keep_going = True
    while (keep_going):
        # Before we start any more, find out how many are running.  First go
        # through the list of those started and see if alive.  Update state.
        for p in procs:
            if p.state == 1: # been started
                if not p.process.is_alive():
                    p.state = 2 # process has finished or been terminated
                    assert p.process.exitcode != None, \
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


def takes_time(x):
    """ Example function which takes some time to run - just here for testing. """

    import numpy
    START = time.time()
    s = numpy.float64(1)
    #s = numpy.float32(1)
    #s = 1.0

    assert x not in (3, 7,9), "Simulate some errors"

    for i in range(10000000):
        s = (s + x) * s % 2399232

    elap = time.time() - START
    print('Done "takes_time" x='+str(x)+': s = '+str(s)+', elapsed time = %.2f s' % elap)


def do_main():
    """ Illustrate use of launch_and_wait """
    # load em up
    import multiprocessing
    p = None
    subprocs = []
    for item in [2,3,4,5,6,7,8,9]:
        print("mputil: instantiating Process for x = "+str(item))
        p = multiprocessing.Process(target=takes_time, args=(item,),
                                    name='takes_time()')
        subprocs.append(p)

    # launch em, pool-fashion
    launch_and_wait(subprocs, 3)

    # by now, all should be finished
    print("All subprocs should be finished and joined.")


if __name__=='__main__':
    do_main()
