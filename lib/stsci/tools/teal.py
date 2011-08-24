""" Main module for the ConfigObj version of the parameter task editor: TEAL.
$Id$
"""
from __future__ import division # confidence high

import glob, os, sys
import configobj, cfgpars, editpar, filedlg, vtor_checks
from cfgpars import APP_NAME
from irafutils import rglob
import capable
if capable.OF_GRAPHICS:
    import tkMessageBox

# tool help
tealHelpString = """\
The TEAL (Task Editor And Launcher) GUI is used to edit task parameters in a
parameter-dependent way.  After editing, it allows the user to launch
(execute) the task.  It also allows the user to view task help in a separate
window that remains accessible while the parameters are being edited.


Editing Parameters
--------------------

Parameter values are modified using various GUI widgets that depend on the
parameter properties.  It is possible to edit parameters using either the mouse
or the keyboard.  Most parameters have a context-dependent menu accessible via
right-clicking that enables resetting the parameter (restoring its value to
the task default), clearing the value, or even activating a file browser that
allows a filename to be selected and entered into the parameter field.  Some
items on the right-click pop-up menu may be disabled depending on the parameter
type (e.g. the file browser cannot be used for numeric parameters.)

The mouse-editing behavior should be intuitive, so the notes below focus on
keyboard-editing.  When the editor starts, the first parameter is selected.  To
select another parameter, use the Tab key (Shift-Tab to go backwards) or Return
to move the focus from item to item. The Up and Down arrow keys also move
between fields.  The toolbar buttons can also be selected with Tab.  Use the
space bar to "push" buttons or activate menus.

Enumerated Parameters
        Parameters that have a list of choices use a drop-down menu.  The space
        bar causes the menu to appear; once it is present, the up/down arrow
        keys can be used to select different items.  Items in the list have
        accelerators (underlined, generally the first letter) that can be typed
        to jump directly to that item.  When editing is complete, hit Return or
        Tab to accept the changes, or type Escape to close the menu without
        changing the current parameter value.

Boolean Parameters
        Boolean parameters appear as Yes/No radio buttons.  Hitting the space
        bar toggles the setting, while 'y' and 'n' can be typed to select the
        desired value.

Text Entry Fields
        Strings, integers, floats, etc. appear as text-entry fields.  Values
        are verified to to be legal before being stored in the parameter. If an
        an attempt is made to set a parameter to an illegal value, the program
        beeps and a warning message appears in the status bar at the bottom of
        the window.

        To see the value of a string that is longer than the entry widget,
        either use the left mouse button to do a slow "scroll" through the
        entry or use the middle mouse button to "pull" the value in the entry
        back and forth quickly.  In either case, just click in the entry widget
        with the mouse and then drag to the left or right.  If there is a
        selection highlighted, the middle mouse button may paste it in when
        clicked.  It may be necessary to click once with the left mouse
        button to undo the selection before using the middle button.

        You can also use the left and right arrow keys to scroll through the
        selection.  Control-A jumps to the beginning of the entry, and
        Control-E jumps to the end of the entry.


The Menu Bar
--------------

File menu:
    Execute
             Start the task running with the currently edited parameter values.
             If the Option "Save and Close on Execute" is set, this will save
             all the parameters and close the editor window.
    Save
             Save the parameters to the file named in the title bar.  This
             does not close the editor window, nor does it execute the task.
             If however, this button appears as "Save & Quit", then it will
             in fact close the editor window after saving.
    Save As...
             Save the parameters to a user-specified file.  This does not
             close the editor window, nor does it execute the task.
    Defaults
             Reset all parameters to the system default values for this
             task.  Note that individual parameters can be reset using the
             menu shown by right-clicking on the parameter entry.
    Close
             Close the parameter editor.  If there are unsaved changes, the
             user is prompted to save them.  Either way, this action returns
             to the calling routine a Python dict of the currently selected
             parameter values.
    Cancel
             Cancel the editing session by exiting the parameter editor.  All
             recent changes that were made to the parameters are lost (going
             back until the last Save or Save As).  This action returns
             a Python None to the calling routine.

Open... menu:
     Load and edit parameters from any applicable file found for the current
     task.  This changes the current file being edited (see the name listed
     in the title bar) to the one selected to be opened.  If no such files
     are found, this menu is not shown.

Options menu:
    Display Task Help in a Window
             Help on the task is available through the Help menu.  If this
             option is selected, the help text is displayed in a pop-up window.
             This is the default behavior.
    Display Task Help in a Browser
             If this option is selected, instead of a pop-up window, help is
             displayed in the user's web browser.  This requires access to
             the internet and is a somewhat experimental feature.  Any HTML
             version of the task's help need to be provided by the task.
    Save and Close on Execute
             If this option is selected, the parameter editing window will be
             closed right before task execution as if the Close button had
             been clicked.  This is the default behavior.  For short-running
             tasks, it may be interesting to leave TEAL open and continue to
             execute while tweaking certain parameter values.

Help menu:
    Task Help
             Display help on the task whose parameters are being edited.
             By default the help pops up in a new window, but the help can also
             be displayed in a web browser by modifying the Options.
    TEAL Help
             Display this help.
    Show Log
             Display the historical log of all the status messages that so
             far have been displayed in the status area at the very bottom
             of the user interface.


Toolbar Buttons
-----------------

The Toolbar contains a set of buttons that provide shortcuts for the most
common menu bar actions.  Their names are the same as the menu items given
above: Execute, Save (or Save & Quit), Close, Cancel, and Defaults.

Note that the toolbar buttons are accessible from the keyboard using the Tab
and Shift-Tab keys.  They are located in sequence before the first parameter.
If the first parameter is selected, Shift-Tab backs up to the "Task Help"
button, and if the last parameter is selected then Tab wraps around and selects
the "Execute" button.
"""


# Starts a GUI session, or simply loads a file
def teal(theTask, parent=None, loadOnly=False, returnDict=True,
         canExecute=True, strict=False, errorsToTerm=False):
#        overrides=None):
    """ Start the GUI session, or simply load a task's ConfigObj. """
    if loadOnly:
        obj = None
        try:
            obj = cfgpars.getObjectFromTaskArg(theTask, strict=strict)
#           obj.strictUpdate(overrides) # ! would need to re-verify after this !
        except RuntimeError, re:
            # Since we are loadOnly, don't pop up the GUI for this
            if strict:
                raise
            else:
                print(str(re).replace('\n\n','\n'))
        return obj
    else:
        dlg = None
        try:
            dlg = ConfigObjEparDialog(theTask, parent=parent,
                                      returnDict=returnDict,
                                      strict=strict,
                                      canExecute=canExecute)
#                                     overrides=overrides)
        except cfgpars.NoCfgFileError, ncf:
            if strict:
                raise
            elif errorsToTerm:
                print(str(ncf).replace('\n\n','\n'))
            else:
                popUpErr(parent=parent,message=str(ncf),title="Unfound Task")
        except RuntimeError, re:
            if errorsToTerm:
                print(str(re).replace('\n\n','\n'))
            else:
                popUpErr(parent=parent,message=str(re),title="Bad Parameters")

        # Return, depending on the mode in which we are operating
        if not returnDict:
            return
        if dlg is None or dlg.canceled():
            return None
        else:
            return dlg.getTaskParsObj()


def load(theTask, canExecute=True, strict=True):
    """ Shortcut to load TEAL .cfg files for non-GUI access where
    loadOnly=True. """
    return teal(theTask, parent=None, loadOnly=True, returnDict=True,
                canExecute=canExecute, strict=strict, errorsToTerm=True)


def unlearn(taskPkgName, deleteAll=False):
    """ Find the task named taskPkgName, and delete any/all user-owned
    .cfg files in the user's resource directory which apply to that task.
    Like a unix utility, this returns 0 on success (no files found or only
    1 found but deleted).  For multiple files found, this uses deleteAll,
    returning the file-name-list if deleteAll is False (to indicate the
    problem) and without deleting any files.  MUST check return value.
    This does not prompt the user or print to the screen. """

    # this WILL throw an exception if the taskPkgName isn't found
    flist = cfgpars.getUsrCfgFilesForPyPkg(taskPkgName) # can raise
    if flist == None or len(flist) == 0:
        return 0
    if len(flist) == 1:
        os.remove(flist[0])
        return 0
    # at this point, we know more than one matching file was found
    if deleteAll:
        for f in flist:
            os.remove(f)
        return 0
    else:
        return flist # let the caller know this is an issue


def popUpErr(parent=None, message="", title="Error"):
    # withdraw root, could standardize w/ EditParDialog.__init__()
    if parent == None:
        import Tkinter
        root = Tkinter.Tk()
#       root.lift()
        root.after_idle(root.withdraw)
    tkMessageBox.showerror(message=message, title=title, parent=parent)

# We'd love to somehow force the dialog to the front here in popUpErr (on OSX)
# butt cannot since the Python process started from the Terminal is not an
# Aqua app (unless it became so within PyRAF).  This thread
#    http://objectmix.com/python/350288-tkinter-osx-lift.html
# describes it well.



def execTriggerCode(SCOPE, NAME, VAL, PARENT, codeStr):
    """ .cfgspc embedded code execution is done here, in a relatively confined
        space.  The variables available to the code to be executed are:
              SCOPE, NAME, VAL
        The code string itself is expected to set a var named OUT
    """
    # This was all we needed in Python 2.x
#   OUT = None
#   exec codeStr
#   return OUT

    # In Python 3 (& 2.x) be more explicit:  http://bugs.python.org/issue4831
    OUT = None
    ldict = locals() # will have OUT in it
    exec(codeStr, globals(), ldict)
    return ldict['OUT']



def print_tasknames(pkgName, aDir, term_width=80, always=False):
    """ Print a message listing TEAL-enabled tasks available under a
        given installation directory (where pkgName resides).
        If always is True, this will always print when tasks are
        found; otherwise it will only print found tasks when in interactive
        mode.
    """
    # See if we can bail out early
    if not always:
        # We can't use the sys.ps1 check if in PyRAF since it changes sys
        if 'pyraf' not in sys.modules:
           # sys.ps1 is only defined in interactive mode
           if not hasattr(sys, 'ps1'):
               return # leave here, we're in someone's script

    # Check for tasks
    taskDict = cfgpars.findAllCfgTasksUnderDir(aDir)
    tasks = [x for x in taskDict.values() if len(x) > 0]
    # only be verbose if there something found
    if len(tasks) > 0:
        sortedUniqTasks = sorted(set(tasks))
        if len(sortedUniqTasks) == 1:
            tlines = 'The following task in the '+pkgName+\
                     ' package can be run with TEAL:\n'
        else:
            tlines = 'The following tasks in the '+pkgName+\
                     ' package can be run with TEAL:\n'
        # Pad list for len == 1, 2, 3
        if len(sortedUniqTasks) in (2, 3):
            sortedUniqTasks.insert(0, '')
        elif len(sortedUniqTasks) == 1:
            sortedUniqTasks = ['', ''] + sortedUniqTasks
        # Loop over tasks
        i = 0
        for ttt in sortedUniqTasks:
            if i >= 5:
                i = 0
                tlines += '\n'
            tlines += ttt.center(term_width//5)
            i += 1

        print(tlines)

def getHelpFileAsString(taskname,taskpath):
    """
    This functions will return useful help as a string read from a file
    in the task's installed directory called "<module>.help".

    If no such file can be found, it will simply return an empty string.

    Notes
    -----
    The location of the actual help file will be found under the task's
    installed directory using 'irafutils.rglob' to search all sub-dirs to
    find the file. This allows the help file to be either in the tasks
    installed directory or in any sub-directory, such as a "help/" directory.

    Parameters
    ----------
    taskname: string
        Value of `__taskname__` for a module/task

    taskpath: string
        Value of `__file__` for an installed module which defines the task

    Returns
    -------
    helpString: string
        multi-line string read from the file '<taskname>.help'

    """
    #get the local library directory where the code is stored
    pathsplit=os.path.split(taskpath) # taskpath should be task's __file__
    if taskname.find('.') > -1: # if taskname is given as package.taskname...
        helpname=taskname.split(".")[1]    # taskname should be __taskname__ from task's module
    else:
        helpname = taskname
    localdir = pathsplit[0]
    if localdir == '':
       localdir = '.'
    helpfile=rglob(localdir,helpname+".help")[0]

    if os.access(helpfile,os.R_OK):
        fh=open(helpfile,'r')
        ss=fh.readlines()
        fh.close()
        helpString=""
        for line in ss:
            helpString+=line
    else:
        helpString= ''

    return helpString


def cfgGetBool(theObj, name, dflt):
    """ Get a stringified val from a ConfigObj obj and return it as bool """
    strval = theObj.get(name, None)
    if strval is None:
        return dflt
    return strval.lower().strip() == 'true'


# Main class
class ConfigObjEparDialog(editpar.EditParDialog):

    FALSEVALS = (None, False, '', 0, 0.0, '0', '0.0', 'OFF', 'Off', 'off',
                 'NO', 'No', 'no', 'N', 'n', 'FALSE', 'False', 'false')

    def __init__(self, theTask, parent=None, title=APP_NAME,
                 isChild=0, childList=None, returnDict=True,
                 strict=False, canExecute=True):
#                overrides=None,

        # returnDict is fundamental to this GUI.  If True, then a dict is
        # returned to the caller when it is Closed (None is returned if it
        # is Canceled).  If False, we operate in an auto-close mode (like EPAR)
        self._returnDict = returnDict

        # Keep track of any passed-in args before creating the _taskParsObj
#       self._overrides = overrides
        self._canExecute = canExecute
        self._strict = strict

        # Init base - calls _setTaskParsObj(), sets self.taskName, etc
        # Note that this calls _overrideMasterSettings()
        editpar.EditParDialog.__init__(self, theTask, parent, isChild,
                                       title, childList,
                                       resourceDir=cfgpars.getAppDir())
        # We don't return from this until the GUI is closed


    def _overrideMasterSettings(self):
        """ Override so that we can run in a different mode. """
        # config-obj dict of defaults
        cod = self._getGuiSettings()

        # our own GUI setup
        self._appName              = APP_NAME
        self._appHelpString        = tealHelpString
        self._useSimpleAutoClose   = not self._returnDict
        self._showExtraHelpButton  = False
        self._saveAndCloseOnExec   = cfgGetBool(cod, 'saveAndCloseOnExec', True)
        self._showHelpInBrowser    = cfgGetBool(cod, 'showHelpInBrowser', False)
        self._writeProtectOnSaveAs = cfgGetBool(cod, 'writeProtectOnSaveAs', False)
        self._optFile              = APP_NAME.lower()+".optionDB"

        # our own colors
        # prmdrss teal: #00ffaa, pure cyan (teal) #00ffff (darker) #008080
        # "#aaaaee" is a darker but good blue, but "#bbbbff" pops
        ltblu = "#ccccff" # light blue
        drktl = "#008888" # darkish teal
        self._frmeColor = cod.get('frameColor', drktl)
        self._taskColor = cod.get('taskBoxColor', ltblu)
        self._bboxColor = cod.get('buttonBoxColor', ltblu)
        self._entsColor = cod.get('entriesColor', ltblu)

        self._showExecuteButton = self._canExecute

        # check on the help string - just to see if it is HTML
        # (could use HTMLParser here if need be, be quick and simple tho)
        hhh = self.getHelpString(self.pkgName+'.'+self.taskName)
        if hhh:
            hhh = hhh.lower()
            if hhh.find('<html') >= 0 or hhh.find('</html>') > 0:
                self._knowTaskHelpIsHtml = True
            elif hhh.startswith('http:') or hhh.startswith('https:'):
                self._knowTaskHelpIsHtml = True
            elif hhh.startswith('file:') and \
                 (hhh.endswith('.htm') or hhh.endswith('.html')):
                self._knowTaskHelpIsHtml = True


    def _preMainLoop(self):
        """ Override so that we can do some things right before activating. """
        # Put the fname in the title. EditParDialog doesn't do this by default
        self.updateTitle(self._taskParsObj.filename)


    def _doActualSave(self, fname, comment, set_ro=False):
        """ Override this so we can handle case of file not writable, as
            well as to make our _lastSavedState copy. """
        self.debug('Saving, file name given: '+str(fname))
        try:
            rv=self._taskParsObj.saveParList(filename=fname,comment=comment)
        except IOError:
            # User does not have privs to write to this file. Get name of local
            # choice and try to use that.
            if not fname:
                fname = self._taskParsObj.filename
            fname = self._rcDir+os.sep+os.path.basename(fname)
            # Tell them the context is changing, and where we are saving
            msg = 'Installed config file for task "'+ \
                  self._taskParsObj.getName()+'" is not to be overwritten.'+ \
                  '  Values will be saved to: \n\n\t"'+fname+'".'
            tkMessageBox.showwarning(message=msg, title="Will not overwrite!")
            # Try saving to their local copy
            rv=self._taskParsObj.saveParList(filename=fname, comment=comment)
            # Treat like a save-as
            self._saveAsPostSave_Hook(fname)

        # Limit write privs if requested (only if not in _rcDir)
        if set_ro and os.path.dirname(os.path.abspath(fname)) != \
                                      os.path.abspath(self._rcDir):
            cfgpars.checkSetReadOnly(fname)

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
        triggerStrs = self._taskParsObj.getTriggerStrings(parScope, parName)

        # Some items will have a trigger, but likely most won't
        if triggerStrs and len(triggerStrs) > 0:
            return self
        else:
            return None


    def edited(self, scope, name, lastSavedVal, newVal, action):
        """ This is the callback function invoked when an item is edited.
            This is only called for those items which were previously
            specified to use this mechanism.  We do not turn this on for
            all items because the performance might be prohibitive.
            This kicks off any previously registered triggers. """

        # Get name(s) of any triggers that this par triggers
        triggerNamesTup = self._taskParsObj.getTriggerStrings(scope, name)
        assert triggerNamesTup != None and len(triggerNamesTup) > 0, \
               'Empty trigger name for: "'+name+'", consult the .cfgspc file.'

        # Loop through all trigger names - each one is a trigger to kick off -
        # in the order that they appear in the tuple we got.  Most cases will
        # probably only have a single trigger in the tuple.
        for triggerName in triggerNamesTup:
            # First handle the known/canned trigger names
#           print (scope, name, newVal, action, triggerName) # DBG: debug line

            # _section_switch_
            if triggerName == '_section_switch_':
                # Try to uniformly handle all possible par types here, not
                # just boolean (e.g. str, int, float, etc.)
                # Also, see logic in _BooleanMixin._coerceOneValue()
                state = newVal not in self.FALSEVALS
                self._toggleSectionActiveState(scope, state, (name,))
                continue

            # _2_section_switch_ (see notes above in _section_switch_)
            if triggerName == '_2_section_switch_':
                state = newVal not in self.FALSEVALS
                # toggle most of 1st section (as usual) and ALL of next section
                self._toggleSectionActiveState(scope, state, (name,))
                # get first par of next section (fpons) - is a tuple
                fpons = self.findNextSection(scope, name)
                nextSectScope = fpons[0]
                if nextSectScope:
                    self._toggleSectionActiveState(nextSectScope, state, None)
                continue

            # Now handle rules with embedded code (eg. triggerName=='_rule1_')
            if '_RULES_' in self._taskParsObj and \
               triggerName in self._taskParsObj['_RULES_'].configspec:
                # Get codeStr to execute it, but before we do so, check 'when' -
                # make sure this is an action that is allowed to cause a trigger
                ruleSig = self._taskParsObj['_RULES_'].configspec[triggerName]
                chkArgsDict = vtor_checks.sigStrToKwArgsDict(ruleSig)
                codeStr = chkArgsDict.get('code') # or None if didn't specify
                when2run = chkArgsDict.get('when') # or None if didn't specify

                greenlight = False # do we have a green light to eval the rule?
                if when2run is None:
                    greenlight = True # means run rule for any possible action
                else: # 'when' was set to something so we need to check action
                    # check value of action (poor man's enum)
                    assert action in editpar.GROUP_ACTIONS, \
                        "Unknown action: "+str(action)+', expected one of: '+ \
                        str(editpar.GROUP_ACTIONS)
                    # check value of 'when' (allow them to use comma-sep'd str)
                    # (readers be aware that values must be those possible for
                    #  'action', and 'always' is also allowed)
                    whenlist = when2run.split(',')
                    # warn for invalid values
                    for w in whenlist:
                        if not w in editpar.GROUP_ACTIONS and w != 'always':
                           print('WARNING: skipping bad value for when kwd: "'+\
                                  w+'" in trigger/rule: '+triggerName)
                    # finally, do the correlation
                    greenlight = 'always' in whenlist or action in whenlist

                # SECURITY NOTE: because this part executes arbitrary code, that
                # code string must always be found only in the configspec file,
                # which is intended to only ever be root-installed w/ the pkg.
                if codeStr:
                    if not greenlight:
                        continue # not an error, just skip this one
                    self.showStatus("Evaluating "+triggerName+' ...') #dont keep
                    self.top.update_idletasks() #allow msg to draw prior to exec
                    # execute it and retrieve the outcome
                    outval = execTriggerCode(scope, name, newVal, self.top, codeStr)
                    # Leave this debug line in until it annoys someone
                    msg = 'Value of "'+name+'" triggered "'+triggerName+'"'
                    stroutval = str(outval)
                    if len(stroutval) < 30: msg += '  -->  "'+stroutval+'"'
                    self.showStatus(msg, keep=0)
                    # Now that we have triggerName evaluated to outval, we need
                    # to look through all the parameters and see if there are
                    # any items to be affected by triggerName (e.g. '_rule1_')
                    self._applyTriggerValue(triggerName, outval)
                    continue

            # If we get here, we have an unknown/unusable trigger
            raise RuntimeError('Unknown trigger for: "'+name+'", named: "'+ \
                  str(triggerName)+'".  Please consult the .cfgspc file.')


    def findNextSection(self, scope, name):
        """ Starts with given par (scope+name) and looks further down the list
        of parameters until one of a different non-null scope is found.  Upon
        success, returns the (scope, name) tuple, otherwise (None, None). """
        # first find index of starting point
        plist = self._taskParsObj.getParList()
        start = 0
        for i in range(len(plist)):
            if scope == plist[i].scope and name == plist[i].name:
                start = i
                break
        else:
            print('WARNING: could not find starting par: '+scope+'.'+name)
            return (None, None)

        # now find first different (non-null) scope in a par, after start
        for i in range(start, len(plist)):
            if len(plist[i].scope) > 0 and plist[i].scope != scope:
                return (plist[i].scope, plist[i].name)
        # else didn't find it
        return (None, None)


    def _setTaskParsObj(self, theTask):
        """ Overridden version for ConfigObj. theTask can be either
            a .cfg file name or a ConfigObjPars object. """
        # Create the ConfigObjPars obj
        self._taskParsObj = cfgpars.getObjectFromTaskArg(theTask,
                                                         strict=self._strict)
        # Tell it that we can be used for catching debug lines
        self._taskParsObj.setDebugLogger(self)

        # Immediately make a copy of it's un-tampered internal dict.
        # The dict() method returns a deep-copy dict of the keyvals.
        self._lastSavedState = self._taskParsObj.dict()
        # do this here ??!! or before _lastSavedState ??!!
#       self._taskParsObj.strictUpdate(self._overrides)


    def _getSaveAsFilter(self):
        """ Return a string to be used as the filter arg to the save file
            dialog during Save-As. """
        # figure the dir to use, start with the one from the file
        thedir = os.path.dirname(self._taskParsObj.filename)
        # decide to skip if not writeable
        if not os.access(thedir, os.W_OK) or os.path.exists(self._rcDir):
            thedir = self._rcDir
        # create save-as filter string
        filt = thedir+'/*.cfg'
        envVarName = APP_NAME.upper()+'_CFG'
        if envVarName in os.environ:
            upx = os.environ[envVarName]
            if len(upx) > 0:  filt = upx+"/*.cfg"
        # done
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
            x, pkgf = cfgpars.findCfgFileForPkg(tsk, '.cfg', taskName=tsk,
                              pkgObj=self._taskParsObj.getAssocPkg())
            taskFiles.update( (pkgf,) )
        except cfgpars.NoCfgFileError:
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

        self.debug('Loading from: '+fname)

        # load it into a tmp object (use associatedPkg if we have one)
        try:
            tmpObj = cfgpars.ConfigObjPars(fname, associatedPkg=\
                                           self._taskParsObj.getAssocPkg(),
                                           strict=self._strict)
        except Exception, ex:
            tkMessageBox.showerror(message=str(ex),
                title="Error in "+os.path.basename(fname))
            return

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
            self.setAllEntriesFromParList(newParList, updateModel=True)
                # go ahead and updateModel, even though it will take longer,
                # we need it updated for the copy of the dict we make below
        except editpar.UnfoundParamError, pe:
            tkMessageBox.showwarning(message=str(pe), title="Error in "+\
                                     os.path.basename(fname))
        # trip any triggers
        self.checkAllTriggers('fopen')

        # This new fname is our current context
        self.updateTitle(fname)
        self._taskParsObj.filename = fname # !! maybe try setCurrentContext() ?
        self.freshenFocus()
        self.showStatus("Loaded values from: "+fname, keep=2)

        # Since we are in a new context (and have made no changes yet), make
        # a copy so we know what the last state was.
        # The dict() method returns a deep-copy dict of the keyvals.
        self._lastSavedState = self._taskParsObj.dict()


    def unlearn(self, event=None):
        """ Override this so that we can set to default values our way. """
        self.debug('Clicked defaults')
        self._setToDefaults()
        self.freshenFocus()


    def _handleParListMismatch(self, probStr, extra=False):
        """ Override to include ConfigObj filename and specific errors.
        Note that this only handles "missing" pars and "extra" pars, not
        wrong-type pars.  So it isn't that big of a deal. """

        # keep down the duplicate errors
        if extra:
            return True # the base class is already stating it will be ignored

        # find the actual errors, and then add that to the generic message
        errmsg = 'Warning: '
        if self._strict:
            errmsg = 'ERROR: '
        errmsg = errmsg+'mismatch between default and current par lists ' + \
                 'for task "'+self.taskName+'".'
        if probStr:
            errmsg += '\n\t'+probStr
        errmsg += '\nTry editing/deleting: "' + \
                  self._taskParsObj.filename+'" (or, if in PyRAF: "unlearn ' + \
                  self.taskName+'").'
        print(errmsg)
        return True # as we said, not that big a deal


    def _setToDefaults(self):
        """ Load the default parameter settings into the GUI. """

        # Create an empty object, where every item is set to it's default value
        try:
            tmpObj = cfgpars.ConfigObjPars(self._taskParsObj.filename,
                                           associatedPkg=\
                                           self._taskParsObj.getAssocPkg(),
                                           setAllToDefaults=True, strict=False)
        except Exception, ex:
            msg = "Error Determining Defaults"
            tkMessageBox.showerror(message=msg+'\n\n'+str(ex),
                                   title="Error Determining Defaults")
            return

        # Set the GUI entries to these values (let the user Save after)
        newParList = tmpObj.getParList()
        try:
            self.setAllEntriesFromParList(newParList) # needn't updateModel yet
            self.checkAllTriggers('defaults')
            self.showStatus("Loaded default "+self.taskName+" values via: "+ \
                 os.path.basename(tmpObj._original_configspec), keep=1)
        except editpar.UnfoundParamError, pe:
            tkMessageBox.showerror(message=str(pe),
                                   title="Error Setting to Default Values")

    def _getGuiSettings(self):
        """ Return a dict (ConfigObj) of all user settings found in rcFile. """
        # Put the settings into a ConfigObj dict (don't use a config-spec)
        rcFile = self._rcDir+os.sep+APP_NAME.lower()+'.cfg'
        if os.path.exists(rcFile):
            return configobj.ConfigObj(rcFile)
            # tho, for simple types, unrepr=True eliminates need for .cfgspc
            # also, if we turn unrepr on, we don't need cfgGetBool
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

        co['showHelpInBrowser']    = self._showHelpInBrowser
        co['saveAndCloseOnExec']   = self._saveAndCloseOnExec
        co['writeProtectOnSaveAs'] = self._writeProtectOnSaveAs
        co['frameColor']           = self._frmeColor
        co['taskBoxColor']         = self._taskColor
        co['buttonBoxColor']       = self._bboxColor
        co['entriesColor']         = self._entsColor

        co.initial_comment = ['Automatically generated by '+\
            APP_NAME+'.  All edits will eventually be overwritten.']
        co.initial_comment.append('To use platform default colors, delete each color line below.')
        co.final_comment = [''] # ensure \n at EOF
        co.write()


    def _applyTriggerValue(self, triggerName, outval):
        """ Here we look through the entire .cfgspc to see if any parameters
        are affected by this trigger. For those that are, we apply the action
        to the GUI widget.  The action is specified by depType. """
        # First find which items are dependent upon this trigger (cached)
        # e.g. { scope1.name1 : dep'cy-type, scope2.name2 : dep'cy-type, ... }
        depParsDict = self._taskParsObj.getParsWhoDependOn(triggerName)
        if not depParsDict: return
        if 0: print "Dependent parameters:\n"+str(depParsDict)+"\n"

        # Then go through the dependent pars and apply the trigger to them
        settingMsg = ''
        for absName in depParsDict:
            used = False
            # For each dep par, loop to find the widget for that scope.name
            for i in range(self.numParams):
                scopedName = self.paramList[i].scope+'.'+self.paramList[i].name
                if absName == scopedName: # a match was found
                    depType = depParsDict[absName]
                    if depType == 'active_if':
                        self.entryNo[i].setActiveState(outval)
                    elif depType == 'inactive_if':
                        self.entryNo[i].setActiveState(not outval)
                    elif depType == 'is_set_by':
                        self.entryNo[i].forceValue(outval, noteEdited=True)
                        # WARNING! noteEdited=True may start recursion!
                        if len(settingMsg) > 0: settingMsg += ", "
                        settingMsg += '"'+self.paramList[i].name+'" to "'+\
                                      outval+'"'
                    elif depType in ('set_yes_if', 'set_no_if'):
                        if bool(outval):
                            newval = 'yes'
                            if depType == 'set_no_if': newval = 'no'
                            self.entryNo[i].forceValue(newval, noteEdited=True)
                            # WARNING! noteEdited=True may start recursion!
                            if len(settingMsg) > 0: settingMsg += ", "
                            settingMsg += '"'+self.paramList[i].name+'" to "'+\
                                          newval+'"'
                        else:
                            if len(settingMsg) > 0: settingMsg += ", "
                            settingMsg += '"'+self.paramList[i].name+\
                                          '" (no change)'
                    elif depType == 'is_disabled_by':
                        # this one is only used with boolean types
                        on = self.entryNo[i].convertToNative(outval)
                        if on:
                            # do not activate whole section or change
                            # any values, only activate this one
                            self.entryNo[i].setActiveState(True)
                        else:
                            # for off, set the bool par AND grey WHOLE section
                            self.entryNo[i].forceValue(outval, noteEdited=True)
                            self.entryNo[i].setActiveState(False)
                            # we'd need this if the par had no _section_switch_
#                           self._toggleSectionActiveState(
#                                self.paramList[i].scope, False, None)
                            if len(settingMsg) > 0: settingMsg += ", "
                            settingMsg += '"'+self.paramList[i].name+'" to "'+\
                                          outval+'"'
                    else:
                        raise RuntimeError('Unknown dependency: "'+depType+ \
                                           '" for par: "'+scopedName+'"')
                    used = True
                    break

            # Or maybe it is a whole section
            if absName.endswith('._section_'):
                scope = absName[:-10]
                depType = depParsDict[absName]
                if depType == 'active_if':
                    self._toggleSectionActiveState(scope, outval, None)
                elif depType == 'inactive_if':
                    self._toggleSectionActiveState(scope, not outval, None)
                used = True

            # Help to debug the .cfgspc rules
            if not used:
                raise RuntimeError('UNUSED "'+triggerName+'" dependency: '+ \
                      str({absName:depParsDict[absName]}))

        if len(settingMsg) > 0:
# why ?!    self.freshenFocus()
            self.showStatus('Automatically set '+settingMsg, keep=1)
