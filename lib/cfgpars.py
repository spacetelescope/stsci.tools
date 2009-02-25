""" Contains the ConfigObjPars class and any related functionality.

$Id$
"""

import glob, os, sys

# ConfigObj modules
import configobj, validate

# Local modules
import basicpar, eparoption, irafutils, taskpars, vtor_checks


def getObjectFromTaskArg(theTask):
    """ Take the arg (usually called theTask), which can be either a subclass
    of ConfigObjPars, or a string package name, or a .cfg filename - no matter
    what it is - take it and return a ConfigObjPars object. """

    # Already in the form we need (instance of us or of subclass)
    if isinstance(theTask, ConfigObjPars):
        # If it is an existing object, make sure it's internal param list is
        # up to date with it's ConfigObj dict, since the user may have manually
        # edited the dict before calling us.
        theTask.syncParamList()
        # Note - some validation is done here in IrafPar creation, but it is
        # not the same validation done by the ConfigObj s/w (no check funcs).
        # Do we want to do that too here?
        return theTask

    # For example, a .cfg file
    if os.path.isfile(str(theTask)):
        return ConfigObjPars(theTask)

    # Else it must be a package name to load
    return findObjFor(theTask)


def getEmbeddedKeyVal(cfgFileName, kwdName, defaultVal=None):
    """ Read a config file and pull out the value of a given keyword. """
    # Assume this is a ConfigObj file.  Use that s/w to quickly read it and
    # put it in dict format.  Assume kwd is at top level (not in a section).
    junkObj = configobj.ConfigObj(cfgFileName) # no configspec needed here
    if kwdName in junkObj:
        retval = junkObj[kwdName]
        del junkObj
        return retval
    # Not found
    if defaultVal:
        del junkObj
        return defaultVal
    else:
        raise KeyError('Unfound item: "'+kwdName+'" in: '+cfgFileName)

def findObjFor(pkgName):
    """ Locate the appropriate ConfigObjPars (or subclass) within the given
        package. """
    try:
        thePkg = __import__(str(pkgName))
    except:
        raise RuntimeError("Unfound package or config file for: "+\
                           str(pkgName))

    # So it was a package name - make/get a ConfigObjPars out of it
    if hasattr(thePkg, 'getConfigObjPars'):
        return thePkg.getConfigObjPars() # use their ConfigObjPars subclass

    # Otherwise we'll create a stand-in instance; first find the .cfg file
    path = os.path.dirname(thePkg.__file__)
    flist  = glob.glob(path+"/cfg/*.cfg")
    flist += glob.glob(path+"/config/*.cfg")  # !! do we need all these?
    flist += glob.glob(path+"/pars/*.cfg")    # trim down when mdriz is
    flist += glob.glob(path+"/*.cfg")         # finalized and stable
    assert len(flist) > 0, "Unfound .cfg file for package: "+pkgName
    # Now go through these and find the first one for the assumed task name
    # The task name for 'BigBlackBox.drizzle' would be 'drizzle'
    assumedTaskName = pkgName.split(".")[-1]
    flist.sort()
    for f in flist:
        itsTask = getEmbeddedKeyVal(f, '_task_name_', '')
        if itsTask == assumedTaskName:
            return ConfigObjPars(f, findFuncsUnder=thePkg)
    raise RuntimeError('No .cfg files found in package: "'+pkgName+ \
                       '" for task: "'+assumedTaskName+'"')


class ConfigObjPars(taskpars.TaskPars, configobj.ConfigObj):
    """ This represents a task's dict of ConfigObj parameters. """

    def __init__(self, cfgFileName, forUseWithEpar=True,
                 setAllToDefaults=False, resourceDir='',
                 findFuncsUnder=None):

        self._forUseWithEpar = forUseWithEpar
        self._resourceDir = resourceDir
        self._triggers = None

        # Set up ConfigObj stuff
        assert setAllToDefaults or os.path.isfile(cfgFileName), \
               "Config file not found: "+cfgFileName
        self.__taskName = ''
        if setAllToDefaults:
            # they may not have given us a real file name here since they
            # just want defaults (in .cfgspc) so don't be too picky about
            # finding and reading the file.
            possible = os.path.splitext(os.path.basename(cfgFileName))[0]
            if os.path.isfile(cfgFileName):
                self.__taskName = getEmbeddedKeyVal(cfgFileName, '_task_name_',
                                                    possible)
            else:
                self.__taskName = possible
        else:
            # this is the real deal, expect a real file name
            self.__taskName = getEmbeddedKeyVal(cfgFileName, '_task_name_')

        cfgSpecPath = self._findAssociatedConfigSpecFile(cfgFileName)
        assert os.path.exists(cfgSpecPath), \
               "Matching configspec not found!  Expected: "+cfgSpecPath
        if setAllToDefaults:
            configobj.ConfigObj.__init__(self, configspec=cfgSpecPath)
        else:
            configobj.ConfigObj.__init__(self, os.path.abspath(cfgFileName),
                                         configspec=cfgSpecPath)

        # Validate it here for now
        self._vtor = validate.Validator(vtor_checks.FUNC_DICT)
        ans = self.validate(self._vtor, preserve_errors=True,
                            copy=setAllToDefaults)
        if ans != True:
            flatStr = "All values are invalid!"
            if ans != False:
                flatStr = str(configobj.flatten_errors(self, ans))
            raise RuntimeError("Validation errors for: "+\
                               os.path.splitext(cfgFileName)[0]+"\n\n"+\
                               flatStr.replace(', (',', \n('))

        # get the initial param list out of the ConfigObj dict
        self.syncParamList()

        # see if we are using a package with it's own run() function
        self._runFunc = None
        self._helpFunc = None
        if findFuncsUnder != None:
            if hasattr(findFuncsUnder, 'run'):
                self._runFunc = findFuncsUnder.run
            if hasattr(findFuncsUnder, 'getHelpAsString'):
                self._helpFunc = findFuncsUnder.getHelpAsString


    def syncParamList(self):
        """ Set or reset the internal __paramList from the dict's contents. """
        # See the note in setParam about this design needing to change...
        self.__paramList = self._getParamsFromConfigDict(self,
                                collectTriggers=True) #,dumpCfgspcTo=sys.stdout)
        # Have to add this odd last one for the sake of the GUI (still?)
        if self._forUseWithEpar:
            self.__paramList.append(basicpar.IrafParS(['$nargs','s','h','N']))


    def getName(self): return self.__taskName

    def getPkgname(self):  return '' # subclasses override w/ a sensible value

    def getParList(self, docopy=False):
        """ Return a list of parameter objects.  docopy is ignored as the
        returned value is not a copy. """
        return self.__paramList

    def getDefaultParList(self):
        return self.__paramList # !!! unfinished

    def getFilename(self): return self.filename

    def setParam(self, name, val, scope='', check=1):
        """ Find the ConfigObj entry.  Update the __paramList. """
        theDict = self
        if len(scope):
            theDict = theDict[scope] # ! only goes one level deep - enhance !
        assert name in theDict, "KeyError: "+scope+'.'+name+" unfound"

        # Set the value, even if invalid.  It needs to be set before
        # the validation step (next).
        theDict[name] = val

        # If need be, check the proposed value.  Ideally, we'd like to
        # (somehow elgantly) only check this one item. For now, the 
        # shortcut is to only validate this section.
        if check:
            ans=self.validate(self._vtor,preserve_errors=True,section=theDict)
            if ans != True:
                flatStr = "All values are invalid!"
                if ans != False:
                    flatStr = str(configobj.flatten_errors(self, ans))
                raise RuntimeError("Validation error: "+flatStr)

        # ! NOTE ! This design needs work.  Right now there are two copies
        # of the data:  the ConfigObj dict, and the __paramList ...
        # Since this step is done for each parameter, this update probably
        # really slows things down.
        self.__paramList = self._getParamsFromConfigDict(self)
        if self._forUseWithEpar:
            self.__paramList.append(basicpar.IrafParS(['$nargs','s','h','N']))

    def saveParList(self, *args, **kw):
        """Write parameter data to filename (string or filehandle)"""
        if 'filename' in kw:
            filename = kw['filename']
        if not filename:
            filename = self.getFilename()
        if not filename:
            raise ValueError("No filename specified to save parameters")

        if hasattr(filename,'write'):
            fh = filename
            absFileName = os.path.abspath(fh.name)
        else:
            absFileName = os.path.expanduser(filename)
            absDir = os.path.dirname(absFileName)
            if len(absDir) and not os.path.isdir(absDir): os.makedirs(absDir)
            fh = open(absFileName,'w')
        numpars = len(self.__paramList)
        if self._forUseWithEpar: numpars -= 1
        retval = str(numpars) + " parameters written to " + absFileName
        self.write(fh) # delegate to ConfigObj
        fh.close()
        self.filename = absFileName # reset our own ConfigObj filename attr
        return retval

    def run(self, *args, **kw):
        """ This may be overridden by a subclass. """
        if self._runFunc != None:
            # remove the two args sent by EditParDialog which we do not use
            if 'mode' in kw: kw.pop('mode')
            if '_save' in kw: kw.pop('_save')
            return self._runFunc(self, *args, **kw)
        else:
            raise RuntimeError('No way to run task "'+self.__taskName+ \
                '". You must either override the "run" method in your '+ \
                'ConfigObjPars subclass, or you must supply a "run" '+ \
                'function in your package.')

    def getHelpAsString(self):
        """ This may be overridden by a subclass. """
        if self._helpFunc != None:
            return self._helpFunc()
        else:
            return 'No help string found for task "'+self.__taskName+ \
                '". You must either override the getHelpAsString method in '+ \
                'your ConfigObjPars subclass, or you must supply such a '+ \
                'function in your package.'

    def _findAssociatedConfigSpecFile(self, cfgFileName):
        """ Given a config file, find its associated config-spec file, and
        return the full pathname of the file. """

        # Handle simplest 2 cases first: co-located or local .cfgspc file
        retval = "."+os.sep+self.__taskName+".cfgspc"
        if os.path.isfile(retval): return retval

        retval = os.path.dirname(cfgFileName)+os.sep+self.__taskName+".cfgspc"
        if os.path.isfile(retval): return retval

        # Also try _resourceDir
        retval = self._resourceDir+os.sep+self.__taskName+".cfgspc"
        if os.path.isfile(retval): return retval

        # unfound
        raise RuntimeError("Unfound config-spec file: "+self.__taskName+".cfgspc")


    def _getParamsFromConfigDict(self, cfgObj, scopePrefix='',
                                 collectTriggers=False, dumpCfgspcTo=None):
        """ Walk the ConfigObj dict pulling out IRAF-like parameters into a
        list. Since this operates on a dict this can be called recursively."""
        # init
        retval = []
        if collectTriggers and len(scopePrefix) < 1:
            self._triggers = {}
        # start walking
        for key in cfgObj:
            val = cfgObj[key]
            if key.startswith('_') and key.endswith('_'):
                continue # skip this, not a param, its a rule or something

            if isinstance(val, dict):
                if len(val.keys())>0 and len(retval)>0:
                    # Here is where we sneak in the section comment
                    # This is so incredibly kludgy (as the code was), it MUST
                    # be revamped eventually!  This is for the epar GUI.
                    prevPar = retval[-1]
                    # Use the key (or its comment?) as the section header
                    prevPar.set(prevPar.get('p_prompt')+'\n\n'+key,
                                field='p_prompt', check=0)
                if dumpCfgspcTo:
                    dumpCfgspcTo.write('\n['+key+']\n')
                # a logical grouping (append its params)
                pfx = scopePrefix+'.'+key
                pfx = pfx.strip('.')
                retval = retval + self._getParamsFromConfigDict(val, pfx,
                                       collectTriggers, dumpCfgspcTo) # recurse
            else:
                # a param
                fields = []
                choicesOrMin = None
                fields.append(key) # name
                dtype = 's'
                cspc = None
                if key in cfgObj.configspec: cspc = cfgObj.configspec[key]
                chk_func_name = ''
                chk_args_dict = {}
                if cspc:
                    chk_func_name = cspc[:cspc.find('(')]
                    chk_args_dict = vtor_checks.sigStrToKwArgsDict(cspc)
                if chk_func_name.find('option') >= 0:
                    dtype = 's'
                    # convert the choices string to a list (to weed out kwds)
                    x = cspc[cspc.find('(')+1:-1] # just the options() args
                    x = x.split(',') # tokenize
                    # rm spaces, extra quotes; rm kywd arg pairs
                    x = [i.strip("' ") for i in x if i.find('=')<0]
                    choicesOrMin = '|'+'|'.join(x)+'|' # IRAF format for enums
                elif chk_func_name.find('boolean') >= 0: dtype = 'b'
                elif chk_func_name.find('float') >= 0:   dtype = 'r'
                elif chk_func_name.find('integer') >= 0: dtype = 'i'
                fields.append(dtype)
                fields.append('a')
                if type(val)==bool:
                    if val: fields.append('yes')
                    else:   fields.append('no')
                else:
                    fields.append(val)
                fields.append(choicesOrMin)
                fields.append(None)
                # Primarily use description from .cfgspc file (0). But, allow
                # overrides from .cfg file (1) if different.
                dscrp0 = chk_args_dict.get('comment','').strip() # ok if missing
                dscrp1 = cfgObj.inline_comments[key]
                if dscrp1==None: dscrp1 = ''
                while len(dscrp1)>0 and dscrp1[0] in (' ','#'):
                    dscrp1 = dscrp1[1:] # .cfg file comments start with '#'
                dscrp1 = dscrp1.strip()
                # Now, decide what to do/say about the descriptions
                if len(dscrp1) > 0:
                    dscrp = dscrp0
                    if dscrp0 != dscrp1: # allow override if different
                        dscrp = dscrp1+eparoption.DSCRPTN_FLAG # flag it
                        if collectTriggers: # if first time through
                            print 'Description of "'+key+'" overridden; '+\
                                  'from:\n'+repr(dscrp0)+', to:\n'+repr(dscrp1)
                    fields.append(dscrp)
                else:
                    # set the field for the GUI
                    fields.append(dscrp0)
                    # ALSO set it in the dict so it is written to file later
                    cfgObj.inline_comments[key] = '# '+dscrp0
                # This little section, while never intended to be used during
                # normal operation, could save a lot of manual work.
                if dumpCfgspcTo:
                    junk = cspc
                    junk = key+' = '+junk.strip()
                    if junk.find(' comment=')<0:
                        junk = junk[:-1]+", comment="+ \
                               repr(irafutils.stripQuotes(dscrp1.strip()))+")"
                    dumpCfgspcTo.write(junk+'\n')
                # Create the par
                par = basicpar.parFactory(fields, True)
                par.setScope(scopePrefix)
                retval.append(par)
                # check for triggers
                if cspc and cspc.find('trigger')>0:
                    self._triggers[scopePrefix+'.'+key] = cspc

        return retval


    def getTriggerStr(self, parScope, parName):
        """ For a given item (scope + name), return the string (or None) of
        it's associated trigger, if one exists. """
        fullName = parScope+'.'+parName
        if fullName in self._triggers:
            return self._triggers[fullName]
        else:
            return None


    def canPerformValidation(self):
        """ Override this so we can do our own validation. tryValue() will
            be called as a result. """
        return True


    def tryValue(self, name, val, scope=''):
        """ For the given item name (and scope), we are being asked to try
            the given value to see if it would pass validation.  We are not
            to set it, but just try it.  We return a tuple:
            If it fails, we return: (False,  the last known valid value).
            On success, we return: (True, None). """

        # SIMILARITY BETWEEN THIS AND setParam() SHOULD BE CONSOLIDATED!

        theDict = self
        if len(scope):
            theDict = theDict[scope] # ! only goes one level deep - enhance !
        assert name in theDict, "KeyError: "+scope+'.'+name+" unfound"

        # Set the value, even if invalid.  It needs to be set before
        # the validation step (next).
        oldVal = theDict[name]
        if oldVal == val: return (True, None) # assume oldVal is valid
        theDict[name] = val

        # Check the proposed value.  Ideally, we'd like to
        # (somehow elgantly) only check this one item. For now, the 
        # shortcut is to only validate this section.
        ans=self.validate(self._vtor,preserve_errors=True,section=theDict)

        # No matter what ans is, immediately return the item to its original
        # value since we are only checking the value here - not setting.
        theDict[name] = oldVal

        # Now see what the validation check said
        errStr = ''
        if ans != True:
            flatStr = "All values are invalid!"
            if ans != False:
                flatStr = str(configobj.flatten_errors(self, ans))
            errStr = "Validation error: "+flatStr # for now this info is unused

        # Done
        if len(errStr): return (False, oldVal) # was an error
        else:           return (True, None)    # val is OK
