from __future__ import division # confidence high

pkg = [ 'pytools', 'pytools.tests' ]

setupargs = {

    'version' :         '3.0',
    'description' :     "General Use Python Tools",
    'author' :          "Warren Hack, Christopher Hanley",
    'author_email' :    "help@stsci.edu",
    'license' :         "http://www.stsci.edu/resources/software_hardware/pyraf/LICENSE",
    'platforms' :       ["Linux","Solaris","Mac OS X","Win"],
    'scripts' :         [ 'lib/fitsdiff','lib/convertwaiveredfits'] ,
    'package_dir' :     { 'pytools' : 'lib', 'pytools.tests' : 'lib/tests' },
    'data_files' :      [ ( 'pytools/tests', [ 'lib/tests/*.fits' ] ) ],
    }

