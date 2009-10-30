""" Learn basic capabilities here (e.g. can we display graphics?).
This is meant to be fast and light, having no complicated dependencies, so
that any module can fearlessly import this without adverse affects or
performance concerns.

$Id$
"""

from __future__ import division # confidence high

import os

OF_GRAPHICS = True
if 'PYRAF_NO_DISPLAY' in os.environ or 'PYTOOLS_NO_DISPLAY' in os.environ:
    OF_GRAPHICS = False
