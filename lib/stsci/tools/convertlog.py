#!/usr/bin/env python
"""
        convertlog: Read ASCII trailer file and convert it to a waivered-FITS file.

        License: http://www.stsci.edu/resources/software_hardware/pyraf/LICENSE

        Usage:

                convertlog.py [OPTIONS] trailer_filename

        :Options:

        -h         print the help (this text)

        -v         print version of task

        -w
        --width    Width (in chars) for trailer file table column

        -o
        --output   Name of output FITS trailer file
                   If none is specified, it will convert input file
                   from "rootname.tra" to "rootname_trl.fits"

        :Example:

        If used in Pythons script, a user can, e. g.::

            >>> from stsci.tools import convertlog
            >>> convertlog.convert(TRLFileName)  # doctest: +SKIP

        The most basic usage from the command line::

            convertlog test1.tra

        This command will convert the input ASCII trailer file test1.tra to
        a waivered-FITS file test1_trl.fits.

"""
# Developed by Science Software Branch, STScI, USA.

from __future__ import division, print_function # confidence high

__version__ = "1.0 (7 Jan, 2016), \xa9 AURA"

import os
import sys
from astropy.io import fits
import numpy as np

import textwrap

def convert(input, width=132, output=None, keep=False):

    """Input ASCII trailer file "input" will be read.

    The contents will then be written out to a FITS file in the same format
    as used by 'stwfits' from IRAF.

    Parameters
    ===========
    input : str
        Filename of input ASCII trailer file

    width : int
        Number of characters wide to use for defining output FITS column
        [Default: 132]

    output : str
        Filename to use for writing out converted FITS trailer file
        If None, input filename will be converted from *.tra -> *_trl.fits
        [Default: None]

    keep : bool
        Specifies whether or not to keep any previously written FITS files
        [Default: False]

    """
    # open input trailer file
    trl = open(input)

    # process all lines
    lines = np.array([i for text in trl.readlines() for i in textwrap.wrap(text,width=width)])

    # close ASCII trailer file now that we have processed all the lines
    trl.close()

    if output is None:
        # create fits file
        rootname,suffix = os.path.splitext(input)
        s = suffix[1:].replace('ra','rl')
        fitsname = "{}_{}{}fits".format(rootname,s,os.path.extsep)
    else:
        fitsname = output
    full_name = os.path.abspath(os.path.join(os.path.curdir,fitsname))

    old_file = os.path.exists(full_name)
    if old_file:
        if keep:
            print("ERROR: Trailer file already written out as: {}".format(full_name))
            raise IOError
        else:
            os.remove(full_name)

    # Build FITS table and write it out
    line_fmt = "{}A".format(width)
    tbhdu = fits.BinTableHDU.from_columns([fits.Column(name='TEXT_FILE',format=line_fmt,array=lines)])
    tbhdu.writeto(fitsname)

    print("Created output FITS filename for trailer:{}    {}".format(os.linesep,full_name))

    os.remove(input)

def usage():
    print(__doc__)

def main():
    import getopt

    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'hvkw:o:')
    except getopt.error as e:
        print(str(e))
        print(__doc__)
        print("\t", __version__)
        sys.exit(2)

    output = None
    width = 132
    keep = False

    for o, a in optlist:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-o", "--output"):
            output = a
        elif o in ("-w", "--width"):
            width = int(a)
        elif o in ("-k", "--keep"):
            keep = True
        else:
            assert False, "unhandled option"


    trl_file = args[0]
    try:
        print("Converting {}...".format(trl_file))
        convert(trl_file, width=width, output=output,keep=keep)
    except:
        print("ERROR: Convertlog failed to convert: {}".format(trl_file))
        sys.exit(2)

#-------------------------------------------------------------------------------
# special initialization when this is the main program

if __name__ == "__main__":
    main()

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
