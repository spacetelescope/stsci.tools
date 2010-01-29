#!/usr/bin/env python

"""
Package: pytools
Author: Christopher Hanley

Purpose:
========
Provide driver function for package tests.

Dependencies:
=============

- nose 0.10.4 or greater.

Usage Example:
==============
All packages will need to import pytools.tester and add the following
function to the __init__.py of their package:

import pytools.tester
def test(*args,**kwds):
    pytools.tester.test(modname=__name__, *args, **kwds)


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

import os,sys

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
    DIRS=['/test']

    args=[]
    for dirname in DIRS:
        args.append('-w')
        args.append(curdir+dirname)

    result = False

    try:
        import nose, nose.core
        result = nose.run(argv=args)
    except ImportError:
        print "Nose 0.10.4 or greater is required for running tests."
    return result

