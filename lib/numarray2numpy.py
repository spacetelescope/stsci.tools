#!/usr/bin/env python

import sys
import os
import re
import glob

#--------------------------------------------------------------------------

"""
conversiondict: 
    dictionary used to store mappings of numarray syntax to its
    corresponding numpy syntax.
"""

conversiondict = {
    'numarray'   :'numpy',
    'itemsize()' :'itemsize',
    'typecode()' :'dtype.char',
    'type()'     :'dtype.type',
    'Float'      :'float',
    'Int'        :'int',
    'NumArray'   :'ndarray',
    'ComplexType':'complexfloating',
    'Numerixtype':'number',
    'type='      :'dtype=',
    'UInit'      :'unit',
    
    }

#--------------------------------------------------------------------------

def convertCode(inputfile, conversionlog, mode="identify"):

    """
    convertCode(inputfile, conversionlog, mode="identify"): 
        Program used the convert existing code from using numarray to 
        numpy syntax.
    
        This is a two function program.  In "itentify" mode the program
        will generate a change file listing required program changes 
        given an input program listing the line number of a line the 
        needs to be changed, the current line, and the suggested change 
        for that line.
    
        In "convert" mode the program will take the change file created by
        this application in "identify" mode and use the suggested changes
        to actually update the program.  The updated program will be written
        to file in the form "ROOTNAME_numpy.py".
    
        In "auto" mode the program will identify changes and convert the
        program in a single step.
        
        inputfile - Name of program file to have syntax converted from
                    numarray to numpy.
                    
        conversionlog - Name of change log file to be either generated
                        or applied.
                        
        mode - Operation mode of the program.  Valid operation modes are
                 "identify", "convert", or "auto".

    """

    if (mode == "identify"):
        #use input program to identify changes and create log file
        _identify(inputfile,conversionlog)
        
    elif (mode == "convert"):
        #use log file to update program code
        _convert(inputfile,conversionlog)
        
    elif (mode == "auto"):
        #create log file and update program code
        _identify(inputfile,conversionlog)
        _convert(inputfile,conversionlog)
        
    else:
        raise ValueError, "Not supported program mode."

#--------------------------------------------------------------------------    

def _identify(inputfile,conversionlog):

    """
    _identify(inputfile,conversionlog):
        do stuff
    """
    
    #create new conversion log file
    logfilefid = _openfile(conversionlog,mode='w')
    
    #open the program file for processing
    programfid = _openfile(inputfile,mode='r')
    
    #Identify changes
        #do stuff
    
    #write out the conversionlog
    _writefile(logfilefid,changelist)
    

#--------------------------------------------------------------------------

def _convert(inputfile,conversionlog):
    
    """
    _convert(inputfile,conversionlog):
        Apply the changes identified in the conversion log to the input
        program.  The converted program will be written out as 
        "rootname_numpy.py".
    """
    
    # open the conversion log for reading
    logfilefid = _openfile(conversionlog,mode='r')
        
    # open the input program for reading
    inputfilefid = _openfile(inputfile,mode='r')

    # create the output file for writing
    outputfilefid = _createOutputFile(inputfile)
    

    _writefile(logfilefid,changelist)

#--------------------------------------------------------------------------

def _openfile(filename,mode='r'):
    
    """
    _openfile(filename,mode='r'):
        Open the specified file for reading or writing.  Return the file
        id handle (fid) to the calling program.
        
        filename - Name of file to open.
        mode - Mode specified file is to be opened in.  There are two
                supported options.  Mode 'r' for reading.  Mode 'w' for
                writing.
    """
    fid = file(filename,mode=mode)
    return fid

#--------------------------------------------------------------------------
    
def _createOutputFile(filename):

    """
    _createOutputFile(filename):

    """

    base,ext = os.path.splitext(filename)
    outputfilename = base+"_numpy"+ext
    
    outputfilefid = _openfile(outputfilename,mode='w')
    
    return outputfilefid

#--------------------------------------------------------------------------

def _writefile(fid,outputlist):

    """
    _writefile(fid,outputlist):
        Write the specified list object to the specified file identifier
        handle.
        
        fid - File id handle.
        outputlist - list object to be written to file.
        
    """
    
    fid.writelines(outputlist)
    fid.close()
    
#--------------------------------------------------------------------------

def _applyChanges(filename,logfile):

    """
    _applyChanges(filename,logfile):
        do stuff
    """
    
    logfile = _openfile(logfile,mode='r')
    programfile = _openfile(filename,mode='w')



"""
Copyright (C) 2003 Association of Universities for Research in Astronomy (AURA)

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above
      copyright notice, this list of conditions and the following
      disclaimer in the documentation and/or other materials provided
      with the distribution.

    3. The name of AURA and its representatives may not be used to
      endorse or promote products derived from this software without
      specific prior written permission.

THIS SOFTWARE IS PROVIDED BY AURA ``AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL AURA BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
DAMAGE.
"""
