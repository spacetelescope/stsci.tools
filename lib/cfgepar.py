""" Main module for the ConfigObj version of the EPAR task editor

$Id$
"""

import configobj, glob, os, tkMessageBox
import cfgpars, editpar, filedlg
from cfgpars import APP_NAME


# Starts a GUI session
def epar(theTask, parent=None, isChild=0, loadOnly=False):
    if loadOnly:
        return cfgpars.getObjectFromTaskArg(theTask)
    else:
        dlg = ConfigObjEparDialog(theTask, parent, isChild)
        if dlg.canceled():
            return None
        else:
            return dlg.getTaskParsObj()


# Main class
class ConfigObjEparDialog(editpar.EditParDialog):

    def __init__(self, theTask, parent=None, isChild=0,
                 title=APP_NAME, childList=None):

        # Init base - calls _setTaskParsObj(), sets self.taskName, etc
        editpar.EditParDialog.__init__(self, theTask, parent, isChild,
                                       title, childList,
                                       resourceDir=cfgpars.getAppDir())
        # We don't return from this until the GUI is closed


    def _overrideMasterSettings(self):
        """ Override so that we can run in a different mode. """
        # config-obj dict of defaults
        cod = self._getGuiSettings()

        # our own GUI setup
        self._appName             = APP_NAME
        self._useSimpleAutoClose  = False # is a fundamental issue here
        self._showExtraHelpButton = False
        self._saveAndCloseOnExec  = cod.get('saveAndCloseOnExec', True)
        self._showHelpInBrowser   = cod.get('showHelpInBrowser', False)
        self._optFile             = APP_NAME.lower()+".optionDB"

        # our own colors
        # prmdrss teal: #00ffaa, pure cyan (teal) #00ffff
        # "#aaaaee" is a darker but good blue, but "#bbbbff" pops
        ltblu = "#ccccff" # light blue
        drktl = "#008888" # darkish teal
        self._frmeColor = cod.get('frameColor', drktl)
        self._taskColor = cod.get('taskBoxColor', ltblu)
        self._bboxColor = cod.get('buttonBoxColor', ltblu)
        self._entsColor = cod.get('entriesColor', ltblu)


    def _preMainLoop(self):
        """ Override so that we can do some things right before activating. """
        # Put the fname in the title. EditParDialog doesn't do this by default
        self.updateTitle(self._taskParsObj.filename)


    def _doActualSave(self, fname, comment):
        """ Override this so we can handle case of file not writable, as
            well as to make our _lastSavedState copy. """
        try:
            rv=self._taskParsObj.saveParList(filename=fname,comment=comment)
        except IOError:
            # User does not have privs to write to this file. Get name of local
            # choice and try to use that.
            if not fname:
                fname = self._taskParsObj.filename
            mine = self._rcDir+os.sep+os.path.basename(fname)
            # Tell them the context is changing, and where we are saving
            msg = 'Installed config file for task "'+ \
                  self._taskParsObj.getName()+'" is not to be overwritten.'+ \
                  '  Values will be saved to: \n\n\t"'+mine+'".'
            tkMessageBox.showwarning(message=msg, title="Will not overwrite!")
            # Try saving to their local copy
            rv=self._taskParsObj.saveParList(filename=mine, comment=comment)
            # Treat like a save-as
            self._saveAsPostSave_Hook(mine)

        # Before returning, make a copy so we know what was last saved.
        # The dict() method returns a deep-copy dict of the keyvals.
        self._lastSavedState = self._taskParsObj.dict()
        return rv


    def _saveAsPostSave_Hook(self, fnameToBeUsed_UNUSED):
        """ Override this so we can update the title bar. """
        self.updateTitle(self._taskParsObj.filename) # _taskParsObj is correct


    def hasUnsavedChanges(self):
        """ Determine if there are any edits in the GUI that have not yet been
        saved (e.g. to a file). """
        
        # Sanity check - this case shouldn't occur
        assert self._lastSavedState != None, \
               "BUG: Please report this as it should never occur."

        # Force the current GUI values into our model in memory, but don't
        # change anything.  Don't save to file, don't even convert bad
        # values to their previous state in the gui.  Note that this can
        # leave the GUI in a half-saved state, but since we are about to exit
        # this is OK.  We only want prompting to occur if they decide to save.
        badList = self.checkSetSaveEntries(doSave=False, fleeOnBadVals=True,
                                           allowGuiChanges=False)
        if badList:
            return True

        # Then compare our data to the last known saved state.  MAKE SURE
        # the LHS is the actual dict (and not 'self') to invoke the dict
        # comparison only.
        return self._lastSavedState != self._taskParsObj

    # Employ an edited callback for a given item?
    def _defineEditedCallbackObjectFor(self, parScope, parName):
        """ Override to allow us to use an edited callback. """

        # We know that the _taskParsObj is a ConfigObjPars
        triggerStr = self._taskParsObj.getTriggerStr(parScope, parName)

        # Some items will have a trigger, but likely most won't
        if triggerStr:
            return self
        else:
            return None


    def edited(self, scope, name, lastSavedVal, newVal):
        """ This is the callback function invoked when an item is edited.
            This is only called for those items which were previously
            specified to use this mechanism.  We do not turn this on for
            all items because the performance might be prohibitive. """
        # the print line is a stand-in
        triggerStr = self._taskParsObj.getTriggerStr(scope, name)
        # call triggers in a general way, not directly here # !!!
        if triggerStr.find('_section_switch_')>=0:
            state = str(newVal).lower() in ('on','yes','true')
            self._toggleSectionActiveState(scope, state, (name,))
        else:
            print "val: "+newVal+", trigger: "+triggerStr
    

    def _setTaskParsObj(self, theTask):
        """ Overridden version for ConfigObj. theTask can be either
            a .cfg file name or a ConfigObjPars object. """
        # Create the ConfigObjPars obj
        self._taskParsObj = cfgpars.getObjectFromTaskArg(theTask)
        # Immediately make a copy of it's un-tampered internal dict.
        # The dict() method returns a deep-copy dict of the keyvals.
        self._lastSavedState = self._taskParsObj.dict()


    def _getSaveAsFilter(self):
        """ Return a string to be used as the filter arg to the save file
            dialog during Save-As. """
        filt = os.path.dirname(self._taskParsObj.filename)+'/*.cfg'
        envVarName = APP_NAME.upper()+'_CFG'
        if envVarName in os.environ:
            upx = os.environ[envVarName]
            if len(upx) > 0:  filt = upx+"/*.cfg" 
        return filt


    def _getOpenChoices(self):
        """ Go through all possible sites to find applicable .cfg files.
            Return as an iterable. """
        tsk = self._taskParsObj.getName()
        taskFiles = set()
        dirsSoFar = [] # this helps speed this up (skip unneeded globs)

        # last dir
        aDir = os.path.dirname(self._taskParsObj.filename)
        if len(aDir) < 1: aDir = os.curdir
        dirsSoFar.append(aDir)
        taskFiles.update(cfgpars.getCfgFilesInDirForTask(aDir, tsk))

        # current dir
        aDir = os.getcwd()
        if aDir not in dirsSoFar:
            dirsSoFar.append(aDir)
            taskFiles.update(cfgpars.getCfgFilesInDirForTask(aDir, tsk))

        # task's python pkg dir (if tsk == python pkg name)
        try:
            pkgf = cfgpars.findCfgFileForPkg(tsk, '.cfg', taskName=tsk)[1]
            taskFiles.update( (pkgf,) )
        except:
            pass # no big deal - maybe there is no python package

        # user's own resourceDir
        aDir = self._rcDir
        if aDir not in dirsSoFar:
            dirsSoFar.append(aDir)
            taskFiles.update(cfgpars.getCfgFilesInDirForTask(aDir, tsk))

        # extra loc - see if they used the app's env. var
        aDir = dirsSoFar[0] # flag to skip this if no env var found
        envVarName = APP_NAME.upper()+'_CFG'
        if envVarName in os.environ: aDir = os.environ[envVarName]
        if aDir not in dirsSoFar:
            dirsSoFar.append(aDir)
            taskFiles.update(cfgpars.getCfgFilesInDirForTask(aDir, tsk))

        # At the very end, add an option which we will later interpret to mean
        # to open the file dialog.
        taskFiles = list(taskFiles) # so as to keep next item at end of seq
        taskFiles.sort()
        taskFiles.append("Other ...")

        return taskFiles


    # OPEN: load parameter settings from a user-specified file
    def pfopen(self, event=None):
        """ Load the parameter settings from a user-specified file. """

        # Get the selected file name
        fname = self._openMenuChoice.get()

        # Also allow them to simply find any file - do not check _task_name_...
        # (could use Tkinter's FileDialog, but this one is prettier)
        if fname[-3:] == '...':
            fd = filedlg.PersistLoadFileDialog(self.top, "Load Config File",
                                               self._getSaveAsFilter())
            if fd.Show() != 1:
                fd.DialogCleanup()
                return
            fname = fd.GetFileName()
            fd.DialogCleanup()
            if fname == None: return # canceled

        # load it into a tmp object
        tmpObj = cfgpars.ConfigObjPars(fname)

        # check it to make sure it is a match
        if not self._taskParsObj.isSameTaskAs(tmpObj):
            msg = 'The current task is "'+self._taskParsObj.getName()+ \
                  '", but the selected file is for task "'+tmpObj.getName()+ \
                  '".  This file was not loaded.'
            tkMessageBox.showerror(message=msg,
                title="Error in "+os.path.basename(fname))
            return

        # Set the GUI entries to these values (let the user Save after)
        newParList = tmpObj.getParList()
        try:
            self.setAllEntriesFromParList(newParList)
        except editpar.UnfoundParamError, pe:
            tkMessageBox.showwarning(message=pe.message, title="Error in "+\
                                     os.path.basename(fname))

        # This new fname is our current context
        self.updateTitle(fname)
        self._taskParsObj.filename = fname # !! maybe try setCurrentContext() ?

        # Since we are in a new context (and have made no changes yet), make
        # a copy so we know what the last state was.
        # The dict() method returns a deep-copy dict of the keyvals.
        self._lastSavedState = self._taskParsObj.dict()


    def unlearn(self, event=None):
        """ Override this so that we can set to default values our way. """
        self._setToDefaults()


    def _setToDefaults(self):
        """ Load the default parameter settings into the GUI. """

        # Create an empty object, where every item is set to it's default value
        try:
            tmpObj = cfgpars.ConfigObjPars(self._taskParsObj.filename,
                                           setAllToDefaults=True)
            self.showStatus("Loading default "+self.taskName+" values via: "+ \
                 os.path.basename(tmpObj._original_configspec), keep=2)
        except Exception, ex:
            msg = "Error Determining Defaults"
            tkMessageBox.showerror(message=msg+'\n\n'+ex.message,
                                   title="Error Determining Defaults")
            return

        # Set the GUI entries to these values (let the user Save after)
        newParList = tmpObj.getParList()
        try:
            self.setAllEntriesFromParList(newParList)
        except editpar.UnfoundParamError, pe:
            tkMessageBox.showerror(message=pe.message,
                                   title="Error Setting to Default Values")

    def _getGuiSettings(self):
        """ Return a dict (ConfigObj) of all user settings found in rcFile. """
        # Put the settings into a ConfigObj dict (don't use a config-spec)
        rcFile = self._rcDir+os.sep+APP_NAME.lower()+'.cfg'
        if os.path.exists(rcFile):
            return configobj.ConfigObj(rcFile, unrepr=True)
            # unrepr: for simple types, eliminates need for .cfgspc
        else:
            return {}


    def _saveGuiSettings(self):
        """ The base class doesn't implement this, so we will - save settings
        (only GUI stuff, not task related) to a file. """
        # Put the settings into a ConfigObj dict (don't use a config-spec)
        rcFile = self._rcDir+os.sep+APP_NAME.lower()+'.cfg'
        #
        if os.path.exists(rcFile): os.remove(rcFile)
        co = configobj.ConfigObj(rcFile)

        co['showHelpInBrowser']  = self._showHelpInBrowser
        co['saveAndCloseOnExec'] = self._saveAndCloseOnExec
        co['frameColor']         = self._frmeColor
        co['taskBoxColor']       = self._taskColor
        co['buttonBoxColor']     = self._bboxColor
        co['entriesColor']       = self._entsColor

        co.initial_comment = ['Automatically generated by '+\
            APP_NAME+'.  All edits will eventually be overwritten.']
        co.initial_comment.append('To use platform default colors, set each color to: None')
        co.final_comment = [''] # ensure \n at EOF
        co.unrepr = True # for simple types, eliminates need for .cfgspc
        co.write()
