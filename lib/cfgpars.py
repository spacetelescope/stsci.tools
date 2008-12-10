""" Contains the ConfigPars class and any related functionality.

$Id$
"""

import os, sys

# ConfigObj modules
import configobj, validate

# Local modules
import basicpar, taskpars, vtor_checks


class ConfigPars(taskpars.TaskPars, configobj.ConfigObj):
    """ This represents a task's dict of ConfigObj parameters. """

    def __init__(self, cfgFileName, forUseWithEpar=True):

        self._forUseWithEpar = forUseWithEpar

        # Set up ConfigObj stuff
        cfgSpecPath = cfgFileName+'spc' # ! assumption during development
        assert os.path.isfile(cfgFileName), "Config file not found: "+ \
               cfgFileName
        assert os.path.exists(cfgSpecPath), \
               "Matching configspec not found!  Expected: "+cfgSpecPath
        configobj.ConfigObj.__init__(self, cfgFileName, configspec=cfgSpecPath)

        # Validate it here for now
        self._vtor = validate.Validator(vtor_checks.FUNC_DICT)
        ans = self.validate(self._vtor, preserve_errors=True)
        if ans != True:
            flatStr = "All values are invalid!"
            if ans != False:
                flatStr = str(configobj.flatten_errors(self, ans))
            raise RuntimeError("Validation errors in : "+cfgFileName+" \n "+ \
                               flatStr)

        # could also get task and pkg name from keywords inside file ... 
        self.__taskName = os.path.splitext(os.path.basename(cfgFileName))[0]

        # get the initial param list out of the ConfigObj dict
        self.__paramList = self.getParamsFromConfigDict(self) # start w/ us

        # May have to add this odd last one for the sake of the GUI
        if self._forUseWithEpar:
            self.__paramList.append(basicpar.IrafParS(['$nargs','s','h','N']))

    def getName(self): return self.__taskName

    def getPkgname(self):  return '' # subclasses override w/ a sensible value

    def getParList(self, docopy=False):
        """ Return a list of parameter objects.  docopy is ignored as the
        returned value is not a copy. """
        return self.__paramList

    def getDefaultParList(self): return self.__paramList # !!! unfinished

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
        # This update probably really slows things down:
        self.__paramList = self.getParamsFromConfigDict(self)
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
            if not os.path.isdir(absDir): os.makedirs(absDir)
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

    def getParamsFromConfigDict(self, cfgObj, scopePrefix=''):
        """ Walk the ConfigObj dict pulling out IRAF-like parameters into a
        list. Since this operates on a dict this can be called recursively."""
        retval = []
        for key in cfgObj:
            val = cfgObj[key]
            if key.startswith('_') and key.endswith('_'):
                continue # skip this, not a param, its a rule or something

            if isinstance(val, dict):
                if len(val.keys())>0 and len(retval)>0:
                    # Here is where we sneak in the section comment
                    # This is so incredibly kludgy (as the code was), it MUST
                    # be revamped eventually. (!!!)  This is for the epar GUI.
                    prevPar = retval[-1]
                    # Use the key (or its comment?) as the section header
                    prevPar.set(prevPar.get('p_prompt')+'\n\n'+key,
                                field='p_prompt', check=0)
                # a logical grouping (append its params)
                retval = retval + self.getParamsFromConfigDict(val, key) # recurse
            else:
                # a param
                fields = []
                choicesOrMin = None
                fields.append(key) # name
                dtype = 's'
                cspc = None
                if key in cfgObj.configspec: cspc = cfgObj.configspec[key]
                if cspc and cspc.find('option') >= 0:
                    dtype = 's'
                    # convert the choices string to a list (to weed out kwds)
                    x = cspc[cspc.find('(')+1:-1] # just the options() args
                    x = x.split(',') # tokenize
                    # rm spaces, extra quotes; rm kywd arg pairs
                    x = [i.strip("' ") for i in x if i.find('=')<0]
                    choicesOrMin = '|'+'|'.join(x)+'|' # IRAF format for enums
                elif cspc and cspc.find('boolean') >= 0:
                    dtype = 'b'
                fields.append(dtype)
                fields.append('a')
                if type(val)==bool:
                    if val: fields.append('yes')
                    else:   fields.append('no')
                else:
                    fields.append(val)
                fields.append(choicesOrMin)
                fields.append(None)
                dscrp = cfgObj.inline_comments[key]
                if dscrp==None:
                    dscrp = ''
                else:
                    while len(dscrp)>0 and dscrp[0] in (' ','#'):
                        dscrp = dscrp[1:]
                fields.append(dscrp)
                par = basicpar.basicParFactory(fields, True) # !!! parScope
                par.setScope(scopePrefix)
                retval.append(par)
        return retval


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


