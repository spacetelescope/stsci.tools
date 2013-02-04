# from __future__ import absolute_import
from __future__ import division # confidence high

from .version import __version__

import stsci.tools.tester
def test(*args,**kwds):
    stsci.tools.tester.test(modname=__name__, *args, **kwds)


