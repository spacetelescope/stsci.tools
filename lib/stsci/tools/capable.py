""" Learn basic capabilities here (e.g. can we display graphics?).
This is meant to be fast and light, having no complicated dependencies, so
that any module can fearlessly import this without adverse affects or
performance concerns.

$Id$
"""

from __future__ import division # confidence high

import os, sys
PY3K = sys.version_info[0] > 2


def is_darwin_and_x():
    """ Convenience function.  Returns True if is an X11-linked Python/Tkinter
    build on OSX.  This is intended to be quick and easy without further
    imports.  As a result, this relies on the assumption that on OSX, PyObjC
    is installed (only) in the Framework builds of Python. """
    if not sys.platform == 'darwin':
        return False

    return which_darwin_linkage() == "x11"


def which_darwin_linkage(force_otool_check=False):
    """ Convenience function.  Returns one of ('x11', 'aqua') in answer to the
    question of whether this is an X11-linked Python/Tkinter, or a natively
    built (framework, Aqua) one.  This is only for OSX.
    On Python 2.*, this relies on the assumption that on OSX, PyObjC
    is installed only in the Framework builds of Python.  On Python 3.*,
    this inspects the actual tkinter library binary via otool. """

    # sanity check
    assert sys.platform=='darwin', 'Incorrect usage, not on OSX'

    # There will *usually* be PyObjC modules on sys.path on the natively-
    # linked Python. This is assumed to be always correct on Python 2.x, as
    # of 2012.  This is kludgy but quick and effective.
    if not force_otool_check:
        junk = ",".join(sys.path)
        if junk.lower().find('/pyobjc') >= 0:
            return "aqua"

    # OK, no PyObjC found.  What we do next is different per Python ver.
    if not PY3K and not force_otool_check:
        return "x11"

    # Is PY3K, use otool shell command (requires 2.7+)
    import Tkinter, subprocess
    libs = subprocess.check_output(('/usr/bin/otool', '-L', Tkinter._tkinter.__file__)).decode()
    if libs.find('/libX11.') >= 0:
        return "x11"
    else:
        return "aqua"


def get_dc_owner(raises, mask_if_self):
    """ Convenience function to return owner of /dev/console.
    If raises is True, this raises an exception on any error.
    If not, it returns any error string as the owner name.
    If owner is self, and if mask_if_self, returns "<self>"."""
    try:
        from pwd import getpwuid
        owner_uid = os.stat('/dev/console').st_uid
        self_uid  = os.getuid()
        if mask_if_self and owner_uid == self_uid:
            return "<self>"
        owner_name = getpwuid(owner_uid).pw_name
        return owner_name
    except Exception as e:
        if raises:
            raise e
        else:
            return str(e)


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
    # When no one is logged in, /dev/console is owned by "root". When user "bob"
    # is logged in locally/physically, /dev/console is owned by "bob".
    # However, if "bob" restarts the X server while logged in, /dev/console
    # may be owned by "sysadmin" - so we check for that.
    #
    if 'PYRAF_YES_DISPLAY' not in os.environ:
        # the use of PYRAF_YES_DISPLAY is a temporary override while we
        # debug why a user might have no read-acces to /dev/console
        dc_owner = get_dc_owner(False, False)
        OF_GRAPHICS = dc_owner == 'sysadmin' or os.access("/dev/console", os.R_OK)

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
        TKINTER_IMPORT_FAILED = 1
        OF_GRAPHICS = False

# Using tkFileDialog from PyRAF (and maybe in straight TEAL) is crashing python
# itself on OSX only.  Allow on Linux.  Mac: use this until PyRAF #171 fixed.
OF_TKFD_IN_EPAR = True
if sys.platform == 'darwin' and OF_GRAPHICS and \
   not is_darwin_and_x(): # if framework ver
    OF_TKFD_IN_EPAR = 'TEAL_TRY_TKFD' in os.environ
