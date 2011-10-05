""" Learn basic capabilities here (e.g. can we display graphics?).
This is meant to be fast and light, having no complicated dependencies, so
that any module can fearlessly import this without adverse affects or
performance concerns.

$Id$
"""

from __future__ import division # confidence high

import os, sys

OF_GRAPHICS = True

if 'PYRAF_NO_DISPLAY' in os.environ or 'PYTOOLS_NO_DISPLAY' in os.environ:
    OF_GRAPHICS = False

if OF_GRAPHICS and sys.platform == 'darwin':
   #
   # On OSX, there is an AppKit error where Python itself will abort if
   # Tkinter operations (e.g. Tkinter._test() ...) are attempted when running
   # from a remote terminal.  In these situations, it is not even safe to put
   # the code in a try/except block, since the AppKit error seems to happen
   # *asynchronously* within ObjectiveC code.  See PyRAF ticket #149.
   #
   # SO, let's try a quick simple test here (only on OSX) to find out if we
   # are the "console user".  If we are not, then we don't even want to attempt
   # any windows/graphics calls.  See "console user" here:
   #     http://developer.apple.com/library/mac/#technotes/tn2083/_index.html
   # If we are the console user, we own /dev/console and can read from it.
   #
   OF_GRAPHICS = os.access("/dev/console", os.R_OK)
