
#  Program: parseinput.py
#  Author:  Christopher Hanley
#
#  License: http://www.stsci.edu/resources/software_hardware/pyraf/LICENSE
#
#  History:
#   Version 0.1,  11/02/2004: Initial Creation -- CJH
#   Version 0.1.2 01/10/2005: Removed the appending of "_drz.fits" to extracted
#       file names.  -- CJH
#   Version 0.1.3 01/18/2005: Added the NICMOS '_asc.fits' to the list of
#       valid association file names.
#   Version 0.1.4 01/25/2005: Removed reliance on ASN dict keys for ordering
#                   the output filelist. WJH/CJH
#   Version 0.1.5 10/11/2005: Corrected typo in errorstr variable name discovered
#                   by external user j.e.geach@durham.ac.uk.

from __future__ import division # confidence high

__version__ = '0.1.5 (10/11/2005)'
__author__  = 'Christopher Hanley'

# irafglob provides the ability to recursively parse user input that
# is in the form of wildcards and '@' files.
from . import irafglob
from .irafglob import irafglob

from . import fileutil
from stsci.tools.asnutil import readASNTable

def parseinput(inputlist,outputname=None, atfile=None):
    """
    Recursively parse user input based upon the irafglob
    program and construct a list of files that need to be processed.
    This program addresses the following deficiencies of the irafglob program::

       parseinput can extract filenames from association tables

    Returns
    -------
    This program will return a list of input files that will need to
    be processed in addition to the name of any outfiles specified in
    an association table.

    Parameters
    ----------
    inputlist - string
        specification of input files using either wild-cards, @-file or
        comma-separated list of filenames

    outputname - string
        desired name for output product to be created from the input files

    atfile - object
        function to use in interpreting the @-file columns that gets passed to irafglob

    Returns
    -------
    files - list of strings
        names of output files to be processed
    newoutputname - string
        name of output file to be created.

    See Also
    --------
    stsci.tools.irafglob

    """

    # Initalize some variables
    files = [] # list used to store names of input files
    newoutputname = outputname # Outputname returned to calling program.
                               # The value of outputname is only changed
                               # if it had a value of 'None' on input.


    # We can use irafglob to parse the input.  If the input wasn't
    # an association table, it needs to be either a wildcard, '@' file,
    # or comma seperated list.
    files = irafglob(inputlist, atfile=atfile)

    # Now that we have expanded the inputlist into a python list
    # containing the list of input files, it is necessary to examine
    # each of the files to make sure none of them are association tables.
    #
    # If an association table is found, the entries should be read
    # Determine if the input is an association table
    for file in files:
        if (checkASN(file) == True):
            # Create a list to store the files extracted from the
            # association tiable
            assoclist = []

            # The input is an association table
            try:
                # Open the association table
                assocdict = readASNTable(file, None, prodonly=False)
            except:
                errorstr  = "###################################\n"
                errorstr += "#                                 #\n"
                errorstr += "# UNABLE TO READ ASSOCIATION FILE,#\n"
                errorstr +=  str(file)+'\n'
                errorstr += "# DURING FILE PARSING.            #\n"
                errorstr += "#                                 #\n"
                errorstr += "# Please determine if the file is #\n"
                errorstr += "# in the current directory and    #\n"
                errorstr += "# that it has been properly       #\n"
                errorstr += "# formatted.                      #\n"
                errorstr += "#                                 #\n"
                errorstr += "# This error message is being     #\n"
                errorstr += "# generated from within the       #\n"
                errorstr += "# parseinput.py module.           #\n"
                errorstr += "#                                 #\n"
                errorstr += "###################################\n"
                raise ValueError(errorstr)

            # Extract the output name from the association table if None
            # was provided on input.
            if outputname is None:
                newoutputname = assocdict['output']

            # Loop over the association dictionary to extract the input
            # file names.
            for f in assocdict['order']:
                assoclist.append(fileutil.buildRootname(f))

            # Remove the name of the association table from the list of files
            files.remove(file)
            # Append the list of filenames generated from the association table
            # to the master list of input files.
            files.extend(assoclist)

    # Return the list of the input files and the output name if provided in an association.
    return files, newoutputname


def checkASN(filename):
    """
    Determine if the filename provided to the function belongs to
    an association.

    Parameters
    ----------
    filename: string

    Returns
    -------
    validASN  : boolean value

    """
    # Extract the file extn type:
    extnType = filename[filename.rfind('_')+1:filename.rfind('.')]

    # Determine if this extn name is valid for an assocation file
    if isValidAssocExtn(extnType):
        return True
    else:
        return False


def isValidAssocExtn(extname):
    """
    Determine if the extension name given as input could
    represent a valid association file.

    Parameters
    ----------
    extname : string

    Returns
    -------
    isValid  : boolean value

    """
    # Define a list of valid extension types to define an association table.
    validExtnNames = ['asn','asc']

    # Loop over the list of valid extension types and compare with the input
    # extension name.  If there is ever a match return True.
    for validName in validExtnNames:
        if (extname == validName):
            return True
    return False

def countinputs(inputlist):
    """
    Determine the number of inputfiles provided by the user and the
    number of those files that are association tables

    Parameters
    ----------
    inputlist   : string
        the user input

    Returns
    -------
    numInputs: int
        number of inputs provided by the user
    numASNfiles: int
        number of association files provided as input
    """

    # Initialize return values
    numInputs = 0
    numASNfiles = 0

    # User irafglob to count the number of inputfiles
    files = irafglob(inputlist, atfile=None)

    # Use the "len" ufunc to count the number of entries in the list
    numInputs = len(files)

    # Loop over the list and see if any of the entries are association files
    for file in files:
        if (checkASN(file) == True):
            numASNfiles += 1

    return numInputs,numASNfiles

