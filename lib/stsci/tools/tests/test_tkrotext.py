from __future__ import absolute_import

import sys
import time

import pytest

from ..tkrotext import ROText

PY3K = sys.version_info[0] > 2

if PY3K:
    import tkinter as TKNTR
else:
    import Tkinter as TKNTR


def test_rotest():
    rot = None

    def quit():
        with pytest.raises(SystemExit):
            sys.exit()

    def clicked():
        rot.insert(TKNTR.END, "\nClicked at " + time.asctime(), force=True)
        rot.see(TKNTR.END)

    # make our test window
    try:
        top = TKNTR.Tk()
    except Exception as e:
        pytest.xfail(str(e))  # Travis does not have interactive session
    f = TKNTR.Frame(top)

    sc = TKNTR.Scrollbar(f)
    sc.pack(side=TKNTR.RIGHT, fill=TKNTR.Y)
    rot = ROText(f, wrap=TKNTR.WORD, height=10, yscrollcommand=sc.set,
                 focusBackTo=top)
    rot.pack(side=TKNTR.TOP, fill=TKNTR.X, expand=True)
    sc.config(command=rot.yview)
    f.pack(side=TKNTR.TOP, fill=TKNTR.X)

    b = TKNTR.Button(top, text='Click Me', command=clicked)
    b.pack(side=TKNTR.TOP, fill=TKNTR.X, expand=1)

    q = TKNTR.Button(top, text='Quit', command=quit)
    q.pack(side=TKNTR.TOP)

    # start
    top.mainloop()
