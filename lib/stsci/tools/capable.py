""" Learn basic capabilities here (e.g. can we display graphics?).
This is meant to be fast and light, having no complicated dependencies, so
that any module can fearlessly import this without adverse affects or
performance concerns.

$Id$
"""

from __future__ import division # confidence high

import os, sys

def is_darwin_and_x():
    """ Convenience function.  Returns True if is an X11-linked Python/Tkinter
    build on OSX.  This is intended to be quick and easy without further
    imports.  As a result, this relies on the assumption that on OSX, PyObjC
    is installed (only) in the Framework builds of Python. """
    if not sys.platform == 'darwin':
        return False
    # Is OSX.
    # There will *usually* be PyObjC modules on sys.path on the natively-
    # linked Python. (could also shell out a call to otool on exec)
    junk = ",".join(sys.path)
    return junk.lower().find('/pyobjc') < 0


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

    # Add a double-check for remote X11 users.  We *think* this is a smaller
    # set of cases, so we do it last minute here:
    if not OF_GRAPHICS:
        # On OSX, but logged in remotely. Normally (with native build) this
        # means there are no graphics.  But, what if they're calling an
        # X11-linked Python?  Then we should allow graphics to be attempted.
        OF_GRAPHICS = is_darwin_and_x()

        # OF_GRAPHICS will be True here in only two cases (2nd should be rare):
        #    An OSX Python build linked with X11, or
        #    An OSX Python build linked natively where PyObjC was left out

# After all that, we may have decided that we want graphics.  Now
# that we know it is ok to try to import Tkinter, we can test if it
# is there.  If it is not, we are not capable of graphics.
if OF_GRAPHICS :
    try :
        import Tkinter
    except ImportError :
        OF_GRAPHICS = False

# Using tkFileDialog from PyRAF (and maybe in straight TEAL) is crashing python
# itself on OSX only.  Allow on Linux.  Mac: use this until PyRAF #171 fixed.
OF_TKFD_IN_EPAR = True
if sys.platform == 'darwin' and not is_darwin_and_x(): # if framework ver
    OF_TKFD_IN_EPAR = 'TEAL_TRY_TKFD' in os.environ
