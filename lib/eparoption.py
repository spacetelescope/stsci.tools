"""eparoption.py: module for defining the various parameter display
   options to be used for the parameter editor task.  The widget that is used
   for entering the parameter value is the variant.  Instances should be
   created using the eparOptionFactory function defined at the end of the
   module.

   Parameter types:
   string  - Entry widget
   *gcur   - NOT IMPLEMENTED AT THIS TIME
   ukey    - NOT IMPLEMENTED AT THIS TIME
   pset    - Action button
   real    - Entry widget
   int     - Entry widget
   boolean - Radiobutton widget
   array real - NOT IMPLEMENTED AT THIS TIME
   array int  - NOT IMPLEMENTED AT THIS TIME

   Enumerated lists - Menubutton/Menu widget

$Id$

M.D. De La Pena, 1999 August 05
"""

# System level modules
from Tkinter import *
import os, sys, string, commands
import FileDialog, tkFileDialog

# Community modules
import filedlg

# Are we using X?
USING_X = sys.platform != 'darwin'

# Constants
MAXLIST  =  15
MAXLINES = 100
XSHIFT   = 110
DSCRPTN_FLAG = ' (***)'


class EparOption(object):

    """EparOption base class

    Implementation for a specific parameter type must implement
    the makeInputWidget method and must create an attribute `entry'
    with the base widget created.  The entry widget is used for
    focus setting and automatic scrolling.  doScroll is a callback to
    do the scrolling when tab changes focus.
    """

    # Chosen option
    choiceClass = StringVar

    def __init__(self, master, statusBar, paramInfo, defaultParamInfo,
                 doScroll, fieldWidths, defaultsVerb, bg):

        # Connect to the information/status Label
        self.status = statusBar

        # Hook to allow scroll when this widget gets focus
        self.doScroll = doScroll
        # Track selection at the last FocusOut event
        self.lastSelection = (0,END)

        # A new Frame is created for each parameter entry
        self.master       = master
        self.bkgColor     = bg
        self.master.frame = Frame(self.master, bg=self.bkgColor)
        self.paramInfo    = paramInfo
        self.defaultParamInfo = defaultParamInfo
        self.defaultsVerb = defaultsVerb
        self.inputWidth   = fieldWidths.get('inputWidth')
        self.valueWidth   = fieldWidths.get('valueWidth')
        self.promptWidth  = fieldWidths.get('promptWidth')

        self.choice = self.choiceClass(self.master.frame)

        self.name  = self.paramInfo.name
        self.value = self.paramInfo.get(field = "p_filename", native = 0,
                     prompt = 0)
        self.previousValue = self.value
        self._editedCallbackObj = None
        self._lastWidgetEditedVal = self.value

        # Generate the input label
        if (self.paramInfo.get(field = "p_mode") == "h"):
            self.inputLabel = Label(self.master.frame, anchor = W,
                                    text  = "(" + self.name + ")",
                                    width = self.inputWidth, bg=self.bkgColor)
        else:
            self.inputLabel = Label(self.master.frame, anchor = W,
                                    text  = self.name,
                                    width = self.inputWidth, bg=self.bkgColor)
        self.inputLabel.pack(side = LEFT, fill = X, expand = TRUE)

        # Get the prompt string and determine if special handling is needed
        self.prompt = self.paramInfo.get(field = "p_prompt", native = 0,
                      prompt = 0)

        # Check the prompt to determine how many lines of valid text exist
        lines       = string.split(self.prompt, "\n")
        nlines      = len(lines)
        promptLines = " " + lines[0]
        infoLines   = ""
        blankLineNo = MAXLINES
        if (nlines > 1):
            # Keep all the lines of text before the blank line for the prompt
            for i in range(1, nlines):
                ntokens = string.split(lines[i])
                if ntokens != []:
                    promptLines = string.join([promptLines, lines[i]], "\n")
                else:
                    blankLineNo = i
                    break
        self._flaggedDescription = False
        if promptLines.endswith(DSCRPTN_FLAG):
            promptLines = promptLines[:-len(DSCRPTN_FLAG)]
            self._flaggedDescription = True
        fgColor = "black"
        if self._flaggedDescription: fgColor = "red"

        # Generate the prompt label
        self.promptLabel = Label(self.master.frame, anchor=W, fg=fgColor,
                                 text=promptLines, width=self.promptWidth,
                                 bg=self.bkgColor)
        self.promptLabel.pack(side=RIGHT, fill=X, expand=TRUE)

        # Default is none of items on popup menu are activated
        # These can be changed by the makeInputWidget method to customize
        # behavior for each widget.
        self.browserEnabled = DISABLED
        self.clearEnabled = DISABLED
        self.unlearnEnabled = DISABLED

        # Generate the input widget depending upon the datatype
        self.makeInputWidget()

        self.entry.bind('<FocusOut>', self.focusOut, "+")
        self.entry.bind('<FocusIn>', self.focusIn, "+")

        # Trap keys that leave field and validate entry
        self.entry.bind('<Return>', self.entryCheck, "+")
        self.entry.bind('<Shift-Return>', self.entryCheck, "+")
        self.entry.bind('<Tab>', self.entryCheck, "+")
        self.entry.bind('<Shift-Tab>', self.entryCheck, "+")
        self.entry.bind('<Up>', self.entryCheck, "+")
        self.entry.bind('<Down>', self.entryCheck, "+")
        try:
            # special shift-tab binding needed for (some? all?) linux systems
            self.entry.bind('<KeyPress-ISO_Left_Tab>', self.entryCheck, "+")
        except TclError:
            # Ignore exception here, the binding can't be relevant
            # if ISO_Left_Tab is unknown.
            pass

        # Bind the right button to a popup menu of choices
        if USING_X:
            self.entry.bind('<Button-3>', self.popupChoices)
        else:
            self.entry.bind('<Button-2>', self.popupChoices)

        # Pack the parameter entry Frame
        self.master.frame.pack(side = TOP, ipady = 1)

        # If there is more text associated with this entry, join all the
        # lines of text with the blank line.  This is the "special" text
        # information.
        if (blankLineNo < (nlines - 1)):

            # Put the text after the blank line into its own Frame
            self.master.infoText = Frame(self.master)

            for j in range(blankLineNo + 1, nlines):
                ntokens = string.split(lines[j])
                if ntokens != []:
                    infoLines = string.join([infoLines, lines[j]], "\n")
                else:
                    break

            # Assign the informational text to the label and pack
            self.master.infoText.label = Label(self.master.infoText,
                                               text = infoLines,
                                               anchor = W,
                                               bg = self.bkgColor)
            self.master.infoText.label.pack(side = LEFT)
            self.master.infoText.pack(side = TOP, anchor = W)


    def convertToNative(self, aVal):
        """ The basic type is natively a string. """
        if aVal == None: return None
        return str(aVal)

    def focusOut(self, event=None):
        """Clear selection (if text is selected in this widget)"""
        if self.entryCheck(event) is None:
            # Entry value is OK
            # Save the last selection so it can be restored if we
            # come right back to this widget.  Then clear the selection
            # before moving on.
            entry = self.entry
            try:
                if not entry.selection_present():
                    self.lastSelection = None
                else:
                    self.lastSelection = (entry.index(SEL_FIRST),
                                          entry.index(SEL_LAST))
            except AttributeError:
                pass
            entry.selection_clear()
        else:
            return "break"

    def focusIn(self, event=None):
        """Select all text (if applicable) on taking focus"""
        try:
            # doScroll returns false if the call was ignored because the
            # last call also came from this widget.  That avoids unwanted
            # scrolls and text selection when the focus moves in and out
            # of the window.
            if self.doScroll(event):
                self.entry.selection_range(0, END)
            else:
                # restore selection to what it was on the last FocusOut
                if self.lastSelection:
                    self.entry.selection_range(*self.lastSelection)
        except AttributeError:
            pass

    # Check the validity of the entry
    # If valid, changes the value of the parameter (note that this
    # is a copy, so change is not permanent until save)
    # Parameter change also sets the isChanged flag.
    def entryCheck(self, event = None):

        # Make sure the input is legal
        value = self.choice.get()
        try:
            if value != self.previousValue:
                self.paramInfo.set(value)
            # fire any applicable triggers, whether value has changed or not
            self.widgetEdited()
            return None
        except ValueError, exceptionInfo:
            # Reset the entry to the previous (presumably valid) value
            self.choice.set(self.previousValue)
            errorMsg = str(exceptionInfo)
            self.status.bell()
            if (event != None):
                self.status.config(text = errorMsg)
            # highlight the text again and terminate processing so
            # focus stays in this widget
            self.focusIn(event)
            return "break"


    def widgetEdited(self, event=None, val=None):
        """ A general method for firing any applicable triggers when
            a value has been set.  This is meant to be easily callable from any
            part of this class (or its subclasses), so that it can be called
            as soon as need be (immed. on click?).  This *should* be able to
            be called multiple times, itself handling the removal of
            duplicate successive calls. """

        # be as lightweight as possible if obj doesn't care about this stuff
        if not self._editedCallbackObj: return
        # get the current value
        curVal = val # take this first, if it is given
        if curVal == None:
            curVal = self.choice.get()
        # see if this is a duplicate successive call for the same value
        if curVal == self._lastWidgetEditedVal: return
        # pull trigger
        self._editedCallbackObj.edited(self.paramInfo.scope,
                                       self.paramInfo.name,
                                       self.previousValue, curVal)
        # for our duplicate checker
        self._lastWidgetEditedVal = curVal


    def focus_set(self, event=None):
        """Set focus to input widget"""
        self.entry.focus_set()


    # Generate the the input widget as appropriate to the parameter datatype
    def makeInputWidget(self):
        pass

    def popupChoices(self, event=None):
        """Popup right-click menu of special parameter operations

        Relies on browserEnabled, clearEnabled, unlearnEnabled
        instance attributes to determine which items are available.
        """
        # don't bother if all items are disabled
        if NORMAL not in [self.browserEnabled,
                          self.clearEnabled,
                          self.unlearnEnabled]:
            return

        self.menu = Menu(self.entry, tearoff = 0)
        if self.browserEnabled != DISABLED:
            self.menu.add_command(label   = "File Browser",
                                  state   = self.browserEnabled,
                                  command = self.fileBrowser)
            self.menu.add_separator()
        self.menu.add_command(label   = "Clear",
                              state   = self.clearEnabled,
                              command = self.clearEntry)
        self.menu.add_command(label   = self.defaultsVerb,
                              state   = self.unlearnEnabled,
                              command = self.unlearnValue)

        # Get the current y-coordinate of the Entry
        ycoord = self.entry.winfo_rooty()

        # Get the current x-coordinate of the cursor
        xcoord = self.entry.winfo_pointerx() - XSHIFT

        # Display the Menu as a popup as it is not associated with a Button
        self.menu.tk_popup(xcoord, ycoord)

    def fileBrowser(self):
        """Invoke a Community Tkinter generic File Dialog"""
        self.fd = filedlg.PersistLoadFileDialog(self.entry,
                        "Directory Browser", "*")
        if self.fd.Show() != 1:
            self.fd.DialogCleanup()
            return
        self.fname = self.fd.GetFileName()
        self.fd.DialogCleanup()
        self.choice.set(self.fname)
        # don't select when we go back to widget to reduce risk of
        # accidentally typing over the filename
        self.lastSelection = None

    def clearEntry(self):
        """Clear just this Entry"""
        self.entry.delete(0, END)

    def forceValue(self, newVal):
        """Force-set a parameter entry to the given value"""
        if newVal == None: newVal = ""
        self.choice.set(newVal)

    def unlearnValue(self):
        """Unlearn a parameter value by setting it back to its default"""
        defaultValue = self.defaultParamInfo.get(field = "p_filename",
                            native = 0, prompt = 0)
        self.choice.set(defaultValue)

    def setEditedCallbackObj(self, ecbo):
        """ Sets a callback object to be triggred when this option/parameter
            is edited.  The object is expected to have an "edited()" method
            which takes args as shown where it is called in entryCheck(). """
        self._editedCallbackObj = ecbo


class EnumEparOption(EparOption):

    def makeInputWidget(self):

        self.unlearnEnabled = NORMAL

        # Set the initial value for the button
        self.choice.set(self.value)

        # Need to adjust the value width so the menu button is
        # aligned properly
        if USING_X:
            self.valueWidth = self.valueWidth - 4
        else:
            self.valueWidth = self.valueWidth - 9 # looks right on Aqua

        # Generate the button
        self.entry = Menubutton(self.master.frame,
                                 width  = self.valueWidth,
                                 text   = self.choice.get(),      # label
                                 relief = RAISED,
                                 anchor = W,                      # alignment
                                 textvariable = self.choice,      # var to sync
                                 indicatoron  = 1,
                                 takefocus    = 1,
                                 highlightthickness = 1,
                                 bg=self.bkgColor)

        self.entry.menu = Menu(self.entry, tearoff=0, postcommand=self.postcmd,
                               bg=self.bkgColor)

        # Generate the dictionary of shortcuts using first letter,
        # second if first not available, etc.
        self.shortcuts = {}
        trylist = self.paramInfo.choice
        underline = {}
        charset = string.lowercase + string.digits
        i = 0
        while trylist:
            trylist2 = []
            for option in trylist:
                # shortcuts dictionary is case-insensitive
                letter = option[i:i+1].lower()
                if self.shortcuts.has_key(letter):
                    # will try again with next letter
                    trylist2.append(option)
                elif letter:
                    if letter in charset:
                        self.shortcuts[letter] = option
                        self.shortcuts[letter.upper()] = option
                        underline[option] = i
                    else:
                        # only allow letters, numbers to be shortcuts
                        # keep going in case this is an embedded blank (e.g.)
                        trylist2.append(option)
                else:
                    # no letters left, so no shortcut for this item
                    underline[option] = -1
            trylist = trylist2
            i = i+1

        # Generate the menu options with shortcuts underlined
        for option in self.paramInfo.choice:
            self.entry.menu.add_radiobutton(label    = option,
                                             value    = option,
                                             variable = self.choice,
                                             indicatoron = 0,
                                             underline = underline[option])

        # set up a pointer from the menubutton back to the menu
        self.entry['menu'] = self.entry.menu

        self.entry.pack(side = LEFT)

        # shortcut keys jump to items
        for letter in self.shortcuts.keys():
            self.entry.bind('<%s>' % letter, self.keypress)

        # Left button sets focus (as well as popping up menu)
        self.entry.bind('<Button-1>', self.focus_set)

    def keypress(self, event):
        """Allow keys typed in widget to select items"""
        try:
            self.choice.set(self.shortcuts[event.keysym])
        except KeyError:
            # key not found (probably a bug, since we intend to catch
            # only events from shortcut keys, but ignore it anyway)
            pass

    def postcmd(self):
        """Make sure proper entry is activated when menu is posted"""
        value = self.choice.get()
        try:
            index = self.paramInfo.choice.index(value)
            self.entry.menu.activate(index)
        except ValueError:
            # initial null value may not be in list
            pass


class BooleanEparOption(EparOption):

    def convertToNative(self, aVal):
        """ Convert to native bool; interpret certain strings. """
        if aVal == None: return None
        if isinstance(aVal, bool): return aVal
        # otherwise interpret strings
        return str(aVal).lower() in ('1','on','yes','true')

    def makeInputWidget(self):

        self.unlearnEnabled = NORMAL

        # Need to buffer the value width so the radio buttons and
        # the adjoining labels are aligned properly
        self.valueWidth = self.valueWidth + 10
        self.padWidth   = self.valueWidth / 2

        # boolean parameters have 3 values: yes, no & undefined
        # Just display two choices (but variable may initially be
        # undefined)
        self.choice.set(self.value)

        self.entry = Frame(self.master.frame,
                           relief    = FLAT,
                           width     = self.valueWidth,
                           takefocus = 1,
                           highlightthickness = 1,
                           bg=self.bkgColor,
                           highlightbackground=self.bkgColor)
        self.rbyes = Radiobutton(self.entry, text = "Yes",
                                 variable    = self.choice,
                                 value       = "yes",
                                 anchor      = W,
                                 takefocus   = 0,
                                 underline   = 0,
                                 bg = self.bkgColor,
                                 highlightbackground=self.bkgColor)
        self.rbyes.pack(side = LEFT, ipadx = self.padWidth)
        self.rbno  = Radiobutton(self.entry, text = "No",
                                 variable    = self.choice,
                                 value       = "no",
                                 anchor      = W,
                                 takefocus   = 0,
                                 underline   = 0,
                                 bg = self.bkgColor,
                                 highlightbackground=self.bkgColor)
        self.rbno.pack(side = RIGHT, ipadx = self.padWidth)
        self.entry.pack(side = LEFT)

        # keyboard accelerators
        # Y/y sets yes, N/n sets no, space toggles selection
        self.entry.bind('<y>', self.set)
        self.entry.bind('<Y>', self.set)
        self.entry.bind('<n>', self.unset)
        self.entry.bind('<N>', self.unset)
        self.entry.bind('<space>', self.toggle)
        # When variable changes, make sure widget gets focus
        self.choice.trace("w", self.trace)

        # Right-click menu is bound to individual widgets too
        if USING_X:
            self.rbno.bind('<Button-3>', self.popupChoices)
            self.rbyes.bind('<Button-3>', self.popupChoices)
        else:
            self.rbno.bind('<Button-2>', self.popupChoices)
            self.rbyes.bind('<Button-2>', self.popupChoices)

        # Regular selection - allow immediate trigger/check
        self.rbyes.bind('<Button-1>', self.widgetEditedYes)
        self.rbno.bind('<Button-1>', self.widgetEditedNo)

    def trace(self, *args):
        self.entry.focus_set()

    # Only needed over widgetEdited because the Yes isn't set yet
    def widgetEditedYes(self, event=None): self.widgetEdited(val="yes")

    # Only needed over widgetEdited because the No isn't set yet
    def widgetEditedNo(self, event=None): self.widgetEdited(val="no")

    def set(self, event=None):
        """Set value to Yes"""
        self.rbyes.select()
        self.widgetEdited()

    def unset(self, event=None):
        """Set value to No"""
        self.rbno.select()
        self.widgetEdited()

    def toggle(self, event=None):
        """Toggle value between Yes and No"""
        if self.choice.get() == "yes":
            self.rbno.select()
        else:
            self.rbyes.select()
        self.widgetEdited()

class StringEparOption(EparOption):

    def makeInputWidget(self):

        self.browserEnabled = NORMAL
        self.clearEnabled = NORMAL
        self.unlearnEnabled = NORMAL

        self.choice.set(self.value)
        self.entry = Entry(self.master.frame, width = self.valueWidth,
                     textvariable = self.choice) # , bg=self.bkgColor)
        self.entry.pack(side = LEFT, fill = X, expand = TRUE)

# widget class that works for numbers and arrays of numbers

class NumberEparOption(EparOption):

    def convertToNative(self, aVal):
        """ Natively as an int. """
        if aVal in (None, '', 'None'): return None
        return int(aVal)

    def notNull(self, value):
        vsplit = value.split()
        return vsplit.count("INDEF") != len(vsplit)

    def makeInputWidget(self):

        self.clearEnabled = NORMAL
        self.unlearnEnabled = NORMAL

        # Retain the original parameter value in case of bad entry
        self.previousValue = self.value

        self.choice.set(self.value)
        self.entry = Entry(self.master.frame, width = self.valueWidth,
                           textvariable = self.choice) #, bg=self.bkgColor)
        self.entry.pack(side = LEFT)

    # Check the validity of the entry
    # Note that doing this using the parameter set method automatically
    # checks max, min, special value (INDEF, parameter indirection), etc.
    def entryCheck(self, event = None):
        """ Ensure any INDEF entry is uppercase, before base class behavior """
        self.choice.set(self.choice.get().upper())
        return EparOption.entryCheck(self, event)

# numeric widget class specific to floats

class FloatEparOption(NumberEparOption):

    def convertToNative(self, aVal):
        """ Natively as a float. """
        if aVal in (None, '', 'None'): return None
        return float(aVal)


# EparOption values for non-string types
_eparOptionDict = { "b": BooleanEparOption,
                    "r": FloatEparOption,
                    "d": FloatEparOption,
                    "i": NumberEparOption,
                    "ar": FloatEparOption,
                    "ai": NumberEparOption,
                  }

def eparOptionFactory(master, statusBar, param, defaultParam,
                      doScroll, fieldWidths,
                      plugIn=None, editedCallbackObj=None,
                      defaultsVerb="Default", bg=None):

    """Return EparOption item of appropriate type for the parameter param"""

    # Allow passed-in overrides
    if plugIn != None:
        eparOption = plugIn

    # If there is an enumerated list, regardless of datatype use EnumEparOption
    elif param.choice != None:
        eparOption = EnumEparOption

    else:
        # Use String for types not in the dictionary
        eparOption = _eparOptionDict.get(param.type, StringEparOption)

    # Create it
    eo = eparOption(master, statusBar, param, defaultParam, doScroll,
                    fieldWidths, defaultsVerb, bg)
    eo.setEditedCallbackObj(editedCallbackObj)
    return eo
