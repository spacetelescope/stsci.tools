#!/usr/bin/env python

# $Id: readgeis.py 8609 2010-01-19 16:22:48Z dencheva $

"""
    update_npol:  Update the header of ACS file(s) with the names of new
                NPOLFILE and D2IMFILE reference files for use with the 
                C version of MultiDrizzle.
    
        License: http://www.stsci.edu/resources/software_hardware/pyraf/LICENSE
        
        Usage:
            update_npol [options] input refdir
            
                'input' is the specification of the files to be updated, either
                as a single filename, an ASN table name, or wild-card specification
                of a list of files
                
                'refdir' is the name of the directory containing all the new
                reference files (*_npl.fits and *_d2i.fits files).
                
                Option:

                -h
                        print the help (this text)
                -l
                        if specified, copy NPOLFILEs and D2IMFILEs to
                        local directory for use with the input files

        Examples:
            update_npol *flt.fits myjref$
            
            This command will update all the FLT files in the current directory
            with the new NPOLFILE and D2IMFILE reference files found in the 'myjref' 
            directory as defined in the environment.  
    
        Python Syntax:
            >>> import update_npol
            >>> update_npol.update('*flt.fits','myjref$')
            
            Another use under Python would be to feed it a specific list of files
            to be updated using:
            >>> update_npol.update(['file1_flt.fits','file2_flt.fits'],'myjref$')
            
            Files in another directory can also be processed using:
            >>> update_npol.update('data$*flt.fits','../new/ref/')
            
"""

from __future__ import division
__docformat__ = 'restructuredtext'

__version__ = '1.0.0'
__vdate__ = '1-Feb-2010'
import os,sys,shutil

import pyfits
from pytools import fileutil as fu
from pytools import parseinput

def update(input,refdir,local=None):
    """ 
    Purpose
    =======    
    Updates files given in input (as a single filename, a list or any other
    input recognized by parseinput) to use the new reference files required with
    the new C version of MultiDrizzle. 
    
    Example
    =======
    >>>import update_npol
    >>>update_npol.update('j8bt06010_asn.fits', 'myref$')
    
    :Parameters:

    `input`: string or list
                Name of input file or files
                Acceptable forms: 
                  - single filename with or without directory
                  - @-file
                  - association table
                  - python list of filenames
                  - wildcard specification of filenames
    `refdir`: string
                path to directory containing new reference files, either 
                environment variable or full path
    `local`: boolean
                Specifies whether or not to copy new reference files to local
                directory for use with the input files
    """ 
    # expand (as needed) the list of input files
    files,output = parseinput.parseinput(input)

    # expand reference directory name (if necessary) to 
    # interpret IRAF or environment variable names
    rdir = fu.osfn(refdir)
    ngeofiles,ngout = parseinput.parseinput(rdir+'*npl.fits')
    # Find D2IMFILE in refdir for updating input file header as well
    d2ifiles,d2iout = parseinput.parseinput(rdir+"*d2i.fits")
    
    # Now, build a matched list of input files and DGEOFILE reference files
    # to use for selecting the appropriate new reference file from the 
    # refdir directory. 
    for f in files: 
        print 'Updating: ',f
        fdir = os.path.split(f)[0]
        # Open each file...
        fimg = pyfits.open(f,mode='update')
        phdr = fimg['PRIMARY'].header
        fdet = phdr['detector']
        # get header of DGEOFILE 
        dhdr = pyfits.getheader(fu.osfn(phdr['DGEOFILE']))
        # search all new NPOLFILEs for one that matches current DGEOFILE config
        npol = find_npolfile(ngeofiles,fdet,[phdr['filter1'],phdr['filter2']])
        if npol is None:
            errstr =  "No valid NPOLFILE found in "+rdir+" for detector="+fdet+"\n"
            errstr += " filters = "+phdr['filter1']+","+phdr['filter2']
            raise ValueError,errstr

        npolname = os.path.split(npol)[1]
        if local:
            npolname = os.path.join(fdir,npolname)
            # clobber any previous copies of this reference file
            if os.path.exists(npolname): os.remove(npolname)
            shutil.copy(npol,npolname)
        else:
            npolname = refdir+npolname
        phdr.update('NPOLFILE',npolname,comment="Non-polynomial corrections in Paper IV LUT")

        # Now find correct D2IFILE
        d2i = find_d2ifile(d2ifiles,fdet)
        if d2i is None:
            print '=============\nWARNING:'
            print "    No valid D2IMFILE found in "+rdir+" for detector ="+fdet
            print "    D2IMFILE correction will not be applied."
            d2iname = ""
        else:
            d2iname = os.path.split(d2i)[1]
            if local:
                # Copy D2IMFILE to local data directory alongside input file as well
                d2iname = os.path.join(fdir,d2iname)
                # clobber any previous copies of this reference file
                if os.path.exists(d2iname): os.remove(d2iname)
                shutil.copy(d2i,d2iname)
            else:
                d2iname = refdir+d2iname
            
        phdr.update('D2IMFILE',d2iname,comment="Column correction table")

        # Close this input file header and go on to the next
        fimg.close()
        
        
def find_d2ifile(flist,detector):
    """ Search a list of files for one that matches the detector specified
    """
    d2ifile = None
    for f in flist:
        fimg = pyfits.open(f)
        fdet = fimg[0].header['detector'] 
        fimg.close()
        if fdet == detector:
            d2ifile = f
            break
    return d2ifile
        
def find_npolfile(flist,detector,filters):
    """ Search a list of files for one that matches the configuration 
        of detector and filters used.
    """      
    for f in flist:
        print 'Getting header from NPOLFILE ',f
        phdr = pyfits.getheader(f)
        if phdr['detector'] == detector:
            if phdr['filter1'] == 'ANY' or \
             (phdr['filter1'] == filters[0] and phdr['filter2'] == filters[1]):
                del phdr # (probably unnecessary) clean up
                return f
    return None

if __name__ == "__main__":

    import getopt

    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'hl')
    except getopt.error, e:
        print str(e)
        print __doc__
        print "\t", __version__

    # initialize default values
    help = 0
    local = False
    
    # read options
    for opt, value in optlist:
        if opt == "-h":
            help = 1
        if opt == "-l":
            local = True

    if (help):
        print __doc__
        print "\t", __version__+'('+__vdate__+')'
    else:
        update(args[:-1],args[-1],local=local)

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
