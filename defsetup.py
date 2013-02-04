from __future__ import division # confidence high
import sys
PY3K = sys.version_info[0] > 2

# Don't copy this as an example - use any other package is stsci_python,
# such as sample_package

pkg = [ 'stsci', 'stsci.tools', 'stsci.tools.tests' ]

setupargs = {

    'version' :         '3.1',
    'description' :     "General Use Python Tools",
    'author' :          "Warren Hack, Christopher Hanley",
    'author_email' :    "help@stsci.edu",
    'license' :         "http://www.stsci.edu/resources/software_hardware/pyraf/LICENSE",
    'platforms' :       ["Linux","Solaris","Mac OS X","Win"],
    'scripts' :         ['scripts/convertwaiveredfits','scripts/stscidocs'] ,
    'package_dir' :     { 'stsci' : 'old_stsci', 'stsci.tools' : 'lib/stsci/tools', 'stsci.tools.tests' : 'lib/stsci/tools/tests' },
    'data_files' :      [ ( 'stsci/tools/tests', [ 'lib/stsci/tools/tests/*.fits' ] ) ],
    }

if PY3K:
    # TODO: in PY3K we get: "error: can't copy 'lib/stsci/tools/tests/*.fits' "
    setupargs['data_files'] = [ ( 'stsci/tools/tests', [] ) ]
