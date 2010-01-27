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
All packages will need to import jwtools.tester and add the following
function to the __init__.py of their package:

def test(*args,**kwds):
    thisdir = os.path.dirname(os.path.abspath(__file__))
    pytools.tester.test(curdir=thisdir)


This assumes that all software packages are installed with the structure:

package/
    __init__.py
    modules.py
    /tests

Where the /tests subdirectory containts the nose tests.



"""


from __future__ import division

import os,sys

def test(*args,**kwds):
    """
    Purpose:
    ========
    test: Run refcore nosetest suite of tests. The tests are located in the
    /test directory of the installed modules.

    """

    try:
        thisdir = kwds['curdir']
    except KeyError:
        thisdir = os.path.dirname(os.path.abspath(__file__))
    DIRS=['/tests']

    args=[]
    for dirname in DIRS:
        args.append('-w')
        args.append(thisdir+dirname)

    result = False

    try:
        import nose, nose.core
        result = nose.run(argv=args)
    except ImportError:
        print "Nose 0.10.4 or greater is required for running tests."
    return result

