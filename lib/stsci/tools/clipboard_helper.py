""" Usually copying to and from the clipboard in an app is handled automatically
and correctly on a given platform, when the user applies the right keystrokes
or mouse events for that platform.  In some corner cases this might not be
true, so this module exists to help facilitate any needed copying or pasting.
For now, this is tkinter based, but it is imported lazily.

$Id$
"""

from __future__ import division, print_function # confidence high

import sys
from . import irafutils

_theRoot = None
_lastSel = '' # our own copy of the last selected text (for PRIMARY)

# Install our own PRIMARY request handler.
def ch_handler(offset=0, length=-1, **kw):
    """ Handle standard PRIMARY clipboard access.  Note that offset and length
    are passed as strings.  This differs from CLIPBOARD. """
    global _lastSel

    offset = int(offset)
    length = int(length)
    if length < 0: length = len(_lastSel)
    return _lastSel[offset:offset+length]


# X11 apps (e.g. xterm) seem to use PRIMARY for select=copy and midmouse=paste
# Other X11 apps        seem to use CLIPBOARD for ctl-c=copy and ?ctl-v?=paste
# OS X seems to use CLIPBOARD for everything, which is Cmd-C and Cmd-V
# Described here:  http://wiki.tcl.tk/1217 "Primary Transfer vs. the Clipboard"
# See also:  http://www.tcl.tk/man/tcl8.5/TkCmd/selection.htm
#      and:  http://www.tcl.tk/man/tcl8.5/TkCmd/clipboard.htm


def put(text, cbname):
    """ Put the given string into the given clipboard. """
    global _lastSel
    _checkTkInit()
    if cbname == 'CLIPBOARD':
        _theRoot.clipboard_clear()
        if text:
            # for clipboard_append, kwds can be -displayof, -format, or -type
            _theRoot.clipboard_append(text)
        return
    if cbname == 'PRIMARY':
        _lastSel = text
        _theRoot.selection_handle(ch_handler, selection='PRIMARY')
        # we need to claim/own it so that ch_handler is used
        _theRoot.selection_own(selection='PRIMARY')
        # could add command arg for a func to be called when we lose ownership
        return
    raise RuntimeError("Unexpected clipboard name: "+str(cbname))


def get(cbname):
    """ Get the contents of the given clipboard. """
    _checkTkInit()
    if cbname == 'PRIMARY':
        try:
            return _theRoot.selection_get(selection='PRIMARY')
        except:
            return None
    if cbname == 'CLIPBOARD':
        try:
            return _theRoot.selection_get(selection='CLIPBOARD')
        except:
            return None
    raise RuntimeError("Unexpected clipboard name: "+str(cbname))


def dump():
    _checkTkInit()
    print ('primary   = '+str(get('PRIMARY')))
    print ('clipboard = '+str(get('CLIPBOARD')))
    print ('owner     = '+str(_theRoot.selection_own_get()))


def _checkTkInit():
    """ Make sure the tkinter root is defined. """
    global _theRoot
    _theRoot = irafutils.init_tk_default_root()
