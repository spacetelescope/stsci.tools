#!/usr/local/bin/python

""" This file holds our own over-rides for the standard Validator check
    functions.  We over-ride them so that we may add our own special keywords
    to them in the config_spec.

$Id$
"""

import configobj, validate
import irafutils

STANDARD_KEYS = ['min', 'max', 'missing', 'default']
OVCDBG = False


def sigStrToKwArgsDict(checkFuncSig):
    """ Take a check function signature (string), and parse it to get a dict
        of the keyword args and their values. """
    p1 = checkFuncSig.find('(')
    p2 = checkFuncSig.rfind(')')
    assert p1 > 0 and p2 > 0 and p2 > p1, "Invalid signature: "+checkFuncSig
    argParts = irafutils.csvSplit(checkFuncSig[p1+1:p2], ',', True)
    argParts = [x.strip() for x in argParts]
    retval = {}
    for argPair in argParts:
        argSpl = argPair.split('=')
        if len(argSpl) > 1:
            retval[argSpl[0]] = irafutils.stripQuotes(argSpl[1])
        else:
            retval[argSpl[0]] = None
    return retval


def separateKeywords(kwArgsDict):
    """ Look through the keywords passed and separate the special ones we
        have added from the legal/standard ones.  Return both sets as two
        dicts (in a tuple), as (standardKws, ourKws) """
    standardKws = {}
    ourKws = {}
    for k in kwArgsDict:
        if k in STANDARD_KEYS:
            standardKws[k]=kwArgsDict[k]
        else:
            ourKws[k]=kwArgsDict[k]
    return (standardKws, ourKws)


def addKwdArgsToSig(sigStr, kwArgsDict):
    """ Alter the passed function signature string to add the given kewords """
    retval = sigStr
    if len(kwArgsDict) > 0:
        retval = retval.strip(' ,)') # open up the r.h.s. for more args
        for k in kwArgsDict:
            if retval[-1] != '(': retval += ", "
            retval += str(k)+"="+str(kwArgsDict[k])
        retval += ')'
    retval = retval
    return retval


def boolean_check_kw(val, *args, **kw):
    if OVCDBG: print "boolean_kw for: "+str(val)+", args: "+str(args)+", kw: "+str(kw)
    vtor = validate.Validator()
    checkFuncStr = "boolean"+str(tuple(args))
    checkFuncStr = addKwdArgsToSig(checkFuncStr, separateKeywords(kw)[0])
    if OVCDBG: print "CFS: "+checkFuncStr+'\n'
    return vtor.check(checkFuncStr, val)


def option_check_kw(val, *args, **kw):
    if OVCDBG: print "option_kw for: "+str(val)+", args: "+str(args)+", kw: "+str(kw)
    vtor = validate.Validator()
    checkFuncStr = "option"+str(tuple(args))
    checkFuncStr = addKwdArgsToSig(checkFuncStr, separateKeywords(kw)[0])
    if OVCDBG: print "CFS: "+checkFuncStr+'\n'
    return vtor.check(checkFuncStr, val)


def integer_check_kw(val, *args, **kw):
    if OVCDBG: print "integer_kw for: "+str(val)+", args: "+str(args)+", kw: "+str(kw)
    vtor = validate.Validator()
    checkFuncStr = "integer"+str(tuple(args))
    checkFuncStr = addKwdArgsToSig(checkFuncStr, separateKeywords(kw)[0])
    if OVCDBG: print "CFS: "+checkFuncStr+'\n'
    return vtor.check(checkFuncStr, val)


def float_check_kw(val, *args, **kw):
    if OVCDBG: print "float_kw for: "+str(val)+", args: "+str(args)+", kw: "+str(kw)
    vtor = validate.Validator()
    checkFuncStr = "float"+str(tuple(args))
    checkFuncStr = addKwdArgsToSig(checkFuncStr, separateKeywords(kw)[0])
    if OVCDBG: print "CFS: "+checkFuncStr+'\n'
    return vtor.check(checkFuncStr, val)


def float_or_none_check_kw(val, *args, **kw):
    if OVCDBG: print "float_or_none_kw for: "+str(val)+", args: "+str(args)+", kw: "+str(kw)
    vtor = validate.Validator()
    if val in (None, '', 'None'): return None # only diff from float_check_kw
    checkFuncStr = "float"+str(tuple(args))
    checkFuncStr = addKwdArgsToSig(checkFuncStr, separateKeywords(kw)[0])
    if OVCDBG: print "CFS: "+checkFuncStr+'\n'
    return vtor.check(checkFuncStr, val)


def string_check_kw(val, *args, **kw):
    if OVCDBG: print "string_kw for: "+str(val)+", args: "+str(args)+", kw: "+str(kw)
    vtor = validate.Validator()
    checkFuncStr = "string"+str(tuple(args))
    checkFuncStr = addKwdArgsToSig(checkFuncStr, separateKeywords(kw)[0])
    if OVCDBG: print "CFS: "+checkFuncStr+'\n'
    return vtor.check(checkFuncStr, val)


FUNC_DICT = {'boolean_kw':       boolean_check_kw,
             'option_kw':        option_check_kw,
             'integer_kw':       integer_check_kw,
             'float_kw':         float_check_kw,
             'float_or_none_kw': float_or_none_check_kw,
             'string_kw':        string_check_kw }
