#!/usr/bin/env python

"""
Package: stsci.tools
Author: Christopher Hanley

Purpose:
========
Provide driver function for package tests.

Dependencies:
=============

- nose 0.10.4 or greater.

Usage Example:
==============
All packages will need to import stsci.tools.tester and add the following
function to the __init__.py of their package:

import stsci.tools.tester
def test(*args,**kwds):
    return stsci.tools.tester.test(modname=__name__, *args, **kwds)


This assumes that all software packages are installed with the structure:

package/
    __init__.py
    modules.py
    tests/
    tests/__init__.py
    tests/test_whatever.py

Where the /tests subdirectory containts the python files that nose will
recognize as tests.

"""

from __future__ import division, print_function

import os
import os.path
import sys

pytools_tester_active = False

def test(modname, mode='nose', *args, **kwds):
    """
    Purpose:
    ========
    test: Run refcore nosetest suite of tests. The tests are located in the
    tests/ directory of the installed modules.

    """

    global pytools_tester_active

    if modname is not None :
        curdir = sys.modules[modname].__file__
        curdir = os.path.abspath(curdir)
        curdir = os.path.dirname(curdir)
    else:
        raise ValueError('name of module to test not given')

    DIRS = [os.path.join(curdir, testdir) for testdir in ['tests', 'test']]

    dirname = None
    for x in DIRS:
        if os.path.isdir(x) :
            dirname = x
            break

    if dirname is None :
            print('no tests found in: %s' % repr(DIRS))
            return False

    if mode == 'nose' :

        print("Testing with nose in %s\n"%dirname)
        try:
            import nose
        except ImportError:
            print("Nose 0.10.4 or greater is required for running tests.")
            raise

        # First arg is blank, since it's skipped by nose
        # --exe is needed because easy_install sets all .py files as executable for
        # some reason
        args = ['', '--exe', '-w', dirname ]

        result = False

        try :
            pytools_tester_active = True
            result = nose.run(argv=args)
        except :
            pytools_tester_active = False
            raise
        pytools_tester_active = False

        return result

    if mode == 'pytest' :

        print("Testing with pytest in %s\n"%dirname)

        try :
            import pytest
        except ImportError :
            print("py.test is required for running tests")
            raise

        # do not use --doctest-modules ; it doesn't work right
        args = [ dirname ]

        try :
            import pandokia
            args = ['-p', 'pandokia.helpers.pytest_plugin' ] + args
        except ImportError :
            pass

        result = False

        try :
            pytools_tester_active = True
            result = pytest.main(args)
        except :
            pytools_tester_active = False
            raise
        pytools_tester_active = False

        return result

    raise ValueError("invalid test specification - mode must be one of 'nose' or 'pytest'")

