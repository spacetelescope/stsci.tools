# from __future__ import absolute_import
from __future__ import division # confidence high

__version__ = ''
__svn_version__ = 'Unable to determine SVN revision'
__full_svn_info__ = ''
__setup_datetime__ = None

try:
    __version__ = __import__('pkg_resources').\
                      get_distribution('stsci.tools').version
except:
    pass

try:
    from stsci.tools.svninfo import (__svn_version__, __full_svn_info__,
                                     __setup_datetime__)
except ImportError:
    pass

import stsci.tools.tester
def test(*args,**kwds):
    stsci.tools.tester.test(modname=__name__, *args, **kwds)

