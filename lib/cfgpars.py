""" Contains the ConfigObjPars class and any related functionality.

$Id$
"""

import glob, os, sys

# ConfigObj modules
import configobj, validate

# Local modules
import basicpar, eparoption, irafutils, taskpars, vtor_checks


def findObjFor(pkgName, forUseWithEpar):
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

    else: # otherwise, cobble together a stand-in;  find the .cfg file
        path = os.path.dirname(thePkg.__file__)
        flist  = glob.glob(path+"/cfg/*.cfg")
        flist += glob.glob(path+"/config/*.cfg")  # !! do we need all these?
        flist += glob.glob(path+"/pars/*.cfg")    # trim down when mdriz is
        flist += glob.glob(path+"/*.cfg")         # finalized and stable
        assert len(flist) > 0, "Unfound .cfg file for package: "+pkgName
        return ConfigObjPars(flist[0], forUseWithEpar=True)


class ConfigObjPars(taskpars.TaskPars, configobj.ConfigObj):
    """ This represents a task's dict of ConfigObj parameters. """

    def __init__(self, cfgFileName, forUseWithEpar=True,
                 setAllToDefaults=False, resourceDir=''):

        self._forUseWithEpar = forUseWithEpar
        self._resourceDir = resourceDir
        self._triggers = None

        # Set up ConfigObj stuff
        assert setAllToDefaults or os.path.isfile(cfgFileName), \
               "Config file not found: "+cfgFileName
        cfgSpecPath = self._findAssociatedConfigSpecFile(cfgFileName)
        assert os.path.exists(cfgSpecPath), \
               "Matching configspec not found!  Expected: "+cfgSpecPath
        if setAllToDefaults:
            configobj.ConfigObj.__init__(self, configspec=cfgSpecPath)
        else:
            configobj.ConfigObj.__init__(self, cfgFileName,
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

        # could also get task and pkg name from keywords inside file ... 
        self.__taskName = os.path.splitext(os.path.basename(cfgFileName))[0]

        # get the initial param list out of the ConfigObj dict
        self.__paramList = self._getParamsFromConfigDict(self,
                                collectTriggers=True) #,dumpCfgspcTo=sys.stdout)

        # May have to add this odd last one for the sake of the GUI
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
        return retval

    def run(self, *args, **kw):
        """ This is meant to be overridden by a subclass. """
        pass

    def _findAssociatedConfigSpecFile(self, cfgFileName):
        """ Given a config file, find its associated config-spec file, and
        return the full pathname of the file. """

        # Handle simplest case first - local .cfgspc file
        retval = cfgFileName+'spc'
        if os.path.isfile(retval): return retval

        # If there is a dash or underscore in the name, look for a .cfgspc
        # file with same "root" name
        rootname = os.path.splitext(os.path.basename(cfgFileName))[0]
        rootroot = rootname # just orig. trunk (eg. "driz", not "driz-updated")
        for sep in ('_','-'):
            idx = rootname.find(sep)
            if idx > 0:
                rootroot = rootname[:idx]
                retval = os.path.dirname(cfgFileName)+'/'+rootroot+".cfgspc"
                if os.path.isfile(retval): return retval

        # As a last resort, try _resourceDir
        retval = self._resourceDir+'/'+rootname+".cfgspc"
        if os.path.isfile(retval): return retval
        # and shortest version
        retval = self._resourceDir+'/'+rootroot+".cfgspc"
        if os.path.isfile(retval): return retval

        # unfound
        return os.path.basename(cfgFileName)+'spc' # will fail


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
                            print 'Description of "'+key+'" overridden; was: '+\
                                  repr(dscrp0)
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
