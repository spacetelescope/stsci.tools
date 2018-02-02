#!/usr/bin/env python

import sys
try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []

setup(
    setup_requires=['d2to1>=0.2.11', 'stsci.distutils>=0.3'] + pytest_runner,
    namespace_packages=['stsci'], packages=['stsci'],
    tests_require=['pytest'], d2to1=True,
)
