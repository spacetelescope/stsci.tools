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
    stsci.tools.tester.test(modname=__name__, *args, **kwds)


This assumes that all software packages are installed with the structure:

package/
    __init__.py
    modules.py
    test/
    test/__init__.py
    test/test_whatever.py
    
Where the /test subdirectory containts the python files that nose will
recognize as tests.

"""

from __future__ import division

import os
import os.path
import sys

pytools_tester_active = False

def test(modname,*args,**kwds):
    """
    Purpose:
    ========
    test: Run refcore nosetest suite of tests. The tests are located in the
    test/ directory of the installed modules.

    """

    if modname != None :
        curdir = sys.modules[modname].__file__
        curdir = os.path.abspath(curdir)
        curdir = os.path.dirname(curdir)
    DIRS=[ curdir + '/test', curdir + '/tests' ]

    args=[]
    found_one = 0
    for dirname in DIRS:
        if os.path.isdir(dirname) :
            args.append('-w')
            args.append(dirname)
            found_one = 1

    if not found_one :
        print "no tests found in:"
        for x in DIRS :
            print "  ",x
        return False

    result = False

    try:
        import nose, nose.core
    except ImportError:
        print "Nose 0.10.4 or greater is required for running tests."
        raise

    try :
        pytools_tester_active = True

        result = nose.run(argv=args)

    except :
        pytools_tester_active = False
        raise

    pytools_tester_active = False

    return result

