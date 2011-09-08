"""teal_bttn.py: for defining the action "parameter" button widget
   to be used in TEAL.

$Id: teal_bttn.py 1 2011-08-30 03:19:02Z sontag $
"""
from __future__ import division # confidence high

# local modules
import eparoption


class TealActionParButton(eparoption.ActionEparButton):

    def clicked(self):  # use to be called childEparDialog()
        print "More to do in TealActionParButton!"
