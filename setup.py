#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name = 'stsci.tools',
    use_scm_version={'write_to': 'lib/stsci/tools/version.py'},
    author = 'STScI',
    author_email = 'help@stsci.edu',
    description = 'Collection of STScI utility functions',
    url = 'https://github.com/spacetelescope/stsci.tools',
    classifiers = [
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires = [
        'astropy',
        'numpy',
    ],
    setup_requires = [
        'setuptools_scm',
        'pytest-runner'
    ],
    tests_require = [
        'pytest',
        'pytest-doctestplus'
    ],
    package_dir = {
        '': 'lib',
    },
    packages = find_packages('lib'),
    package_data = {
        '': ['LICENSE.txt'],
        'stsci/tools/tests': ['data/*.*']
    },
    entry_points = {
        'console_scripts': [
            'convertwaiveredfits=stsci.tools.convertwaiveredfits:main',
            'convertlog=stsci.tools.convertlog:main'
        ],
    },
)
