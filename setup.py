#!/usr/bin/env python
import os
import subprocess
import sys
from setuptools import setup, find_packages

if os.path.exists('relic'):
    sys.path.insert(1, 'relic')
    import relic.release
else:
    try:
        import relic.release
    except ImportError:
        try:
            subprocess.check_call(
                ['git', 'clone', 'https://github.com/jhunkeler/relic.git'])
            sys.path.insert(1, 'relic')
            import relic.release
        except subprocess.CalledProcessError as e:
            print(e)
            exit(1)

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []
version = relic.release.get_info()
relic.release.write_template(version, 'lib/stsci/tools')

setup(
    name = 'stsci.tools',
    version = version.pep386,
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
    setup_requires = pytest_runner,
    install_requires = [
        'astropy',
        'nose',
        'numpy',
    ],
    package_dir = {
        '': 'lib',
    },
    packages = find_packages('lib'),
    package_data = {
        '': ['LICENSE.txt'],
        'stsci/tools/tests': ['*.fits']
    },
    entry_points = {
        'console_scripts': [
            'convertwaiveredfits=stsci.tools.convertwaiveredfits:main',
            'convertlog=stsci.tools.convertlog:main'
        ],
    },
)
