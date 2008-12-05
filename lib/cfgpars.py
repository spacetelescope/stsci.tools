""" Contains the ConfigPars class and any related functionality.

$Id: cfgpars.py 1 2008-11-14 21:40:16Z sontag $
"""

import os, sys

# ConfigObj modules
import configobj, validate

# Local modules
import basicpar, taskpars, vtor_checks


class ConfigPars(taskpars.TaskPars, configobj.ConfigObj):
    """ This represents a task's dict of ConfigObj parameters. """

    def __init__(self, cfgFileName):
        cfgSpecPath = cfgFileName+'spc' # ! assumption during development
        assert os.path.isfile(cfgFileName), "Config file not found: "+ \
               cfgFileName
        assert os.path.exists(cfgSpecPath), \
               "Matching configspec not found!  Expected: "+cfgSpecPath
        configobj.ConfigObj.__init__(self, cfgFileName, configspec=cfgSpecPath)

        # Validate it for now
        vtor = validate.Validator(vtor_checks.FUNC_DICT)
        ans = self.validate(vtor, preserve_errors=True)
        assert ans == True, "Validation ERRORS: "+str(ans)

        # could also get task and pkg name from keywords inside file ... 
        self.__taskName = os.path.splitext(os.path.basename(cfgFileName))[0]

        # get the initial param list out of the ConfigObj dict
        self.__paramList = self.getParamsFromConfigDict(self) # start w/ us

    def getName(self): return self.__taskName

    def getPkgname(self):  return '' # subclasses override w/ a sensible value

    def getParList(self, docopy=True):
        """ Return a list of parameter objects.  docopy is ignored as the
        returned value is not a copy. """
        return self.__paramList

    def getDefaultParList(self): return self.__paramList # !!! unfinished

    def getFilename(self): return self.filename

    def setParam(self, *args, **kw):
        print "UNFINISHED: ConfigPars.setParam(), "+repr(args)+", "+str(kw)

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
        retval = str(len(self.__paramList)) + " parameters written to " + \
                 absFileName
        self.write(fh) # delegate to ConfigObj
        fh.close()
        return retval

    def run(self, *args, **kw):
        """ This is meant to be overridden by a subclass. """
        pass

    def getParamsFromConfigDict(self, cfgObj):
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
                retval = retval + self.getParamsFromConfigDict(val) # recurse
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
                par = basicpar.basicParFactory(fields, True)
                retval.append(par)
        return retval
