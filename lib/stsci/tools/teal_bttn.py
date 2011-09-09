"""teal_bttn.py: for defining the action "parameter" button widget
   to be used in TEAL.

$Id: teal_bttn.py 1 2011-08-30 03:19:02Z sontag $
"""
from __future__ import division # confidence high

import eparoption

class TealActionParButton(eparoption.ActionEparButton):

    def getButtonLabel(self):
        """ Return string to be used on as button label - "value" of par. """
        # If the value has a comma, return the 2nd part, else use whole thing
        return self.value.split(',')[-1]

    def getShowName(self):
        """ Return string to be used on LHS of button - "name" of par. """
        # If the value has a comma, return the 1st part, else leave empty
        if self.value.find(',') >= 0:
            return self.value.split(',')[0]
        else:
            return ''

    def clicked(self):  # use to be called childEparDialog()
        # if needed, we *could* use self._helpCallbackObj.getTaskParsObj
        # or design in some better way to get to the actual ConfigObj ...
        print "More to do in TealActionParButton!"
