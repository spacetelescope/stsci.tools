"""teal_bttn.py: for defining the action "parameter" button widget
   to be used in TEAL.

$Id$
"""
from __future__ import division # confidence high

import sys, traceback
import eparoption

class TealActionParButton(eparoption.ActionEparButton):

    def getButtonLabel(self):
        """ Return string to be used on as button label - "value" of par. """
        # If the value has a comma, return the 2nd part, else use whole thing
        return self.value.split(',')[-1].strip()

    def getShowName(self):
        """ Return string to be used on LHS of button - "name" of par. """
        # If the value has a comma, return the 1st part, else leave empty
        if self.value.find(',') >= 0:
            return self.value.split(',')[0]
        else:
            return ''

    def clicked(self):
        """ Called when this button is clicked. Execute code from .cfgspc """
        try:
            tealGui = self._mainGuiObj
            code = 'print "Need to get code from .cfgspc..."'
            tealGui.showStatus('Clicked "'+self.getButtonLabel()+'"', keep=1)
            import teal
            teal.execEmbCode(self.paramInfo.scope,
                             self.paramInfo.name,
                             self.getButtonLabel(),
                             tealGui,
                             code)
        except Exception, ex:
            msg = 'Error executing: "'+self.getButtonLabel()+'"\n'+ex.message
            msgFull = msg+'\n'+''.join(traceback.format_exc())
            msgFull+= "CODE:\n"+code
            if tealGui:
                teal.popUpErr(tealGui.top, msg, "Action Button Error")
                tealGui.debug(msgFull)
            else:
                teal.popUpErr(None, msg, "Action Button Error")
                print msgFull
