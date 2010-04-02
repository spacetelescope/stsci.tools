# from __future__ import absolute_import
from __future__ import division # confidence high

__version__ = "3.0"

#revision based svn info
try:
    # from .svn_version import __svn_version__, __full_svn_info__
    from svn_version import __svn_version__, __full_svn_info__
except:
    __svn_version__ = 'Unable to determine SVN revision'
    __full_svn_info__ = __svn_version__

import pytools.tester
def test(*args,**kwds):
    pytools.tester.test(modname=__name__, *args, **kwds)

