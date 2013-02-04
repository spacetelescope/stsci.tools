#!/usr/bin/env python

import d2to1
print("d2to1 is",d2to1.__file__)

try:
    from setuptools import setup
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

setup(
    setup_requires=['d2to1>=0.2.3'],
    namespace_packages=['stsci'], packages=['stsci'],
    d2to1=True,
    use_2to3=True,
    zip_safe=False
)
