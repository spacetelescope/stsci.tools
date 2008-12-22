""" Main module for the ConfigObj version of the EPAR task editor

$Id: cfgepar.py 1 2008-12-17 18:51:04Z sontag $
"""

import os, tkMessageBox
import cfgpars, editpar, filedlg


# Starts a GUI session
def epar(theTask, parent=None, isChild=0):

    ConfigObjEparDialog(theTask, parent, isChild)


# Main class
class ConfigObjEparDialog(editpar.EditParDialog):

    def __init__(self, theTask, parent=None, isChild=0,
                 title="Config Parameter Editor", childList=None):

        # Init base - calls _setTaskParsObj(), sets self.taskName, etc
        editpar.EditParDialog.__init__(self, theTask, parent, isChild,
                                       title, childList, resourceDir='')

    # Always allow the Open button ?
    def _showOpenButton(self): return True


    def _setTaskParsObj(self, theTask):
        """ Overridden version for ConfigObj. theTask can be either
            a .cfg file name or a ConfigObjPars object. """

        if isinstance(theTask, cfgpars.ConfigObjPars):
            self._taskParsObj = theTask

        else: # it must be a filename
            # stringify first as user may pass an object
            assert os.path.isfile(str(theTask)), \
                "Error finding config file for: "+str(theTask)
            self._taskParsObj=cfgpars.ConfigObjPars(theTask,forUseWithEpar=True)


    def _getSaveAsFilter(self):
        """ Return a string to be used as the filter arg to the save file
            dialog during Save-As. """
        filt = '*.cfg'
        if 'UPARM_AUX' in os.environ:
            upx = os.environ['UPARM_AUX']
            if len(upx) > 0:  filt = upx+"/*.cfg" 
        return filt


    # OPEN: load parameter settings from a user-specified file
    def pfopen(self, event=None):
        """ Load the parameter settings from a user-specified file. """

        # could use Tkinter's FileDialog, but this one is prettier
        fd = filedlg.PersistLoadFileDialog(self.top, "Load Config File",
                                           self._getSaveAsFilter())
        if fd.Show() != 1:
            fd.DialogCleanup()
            return
        fname = fd.GetFileName()
        fd.DialogCleanup()
        if fname == None: return

        # Now load it: "Loading "+self.taskName+" param values from: "+fname
        print "Loading "+self.taskName+" param values from: "+fname
        tmpObj = cfgpars.ConfigObjPars(fname, forUseWithEpar=True)

        # check it to make sure it is a match
# !     self._taskParsObj.isSameTaskAs(tmpObj)

        # Set the GUI entries to these values (let the user Save after)
        newParList = tmpObj.getParList()
        try:
            self.setAllEntriesFromParList(newParList)
        except editpar.UnfoundParamError, pe:
            tkMessageBox.showwarning(message=pe.message, title="Error in "+\
                                     fname)
