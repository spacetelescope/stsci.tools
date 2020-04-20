from stsci.tools import parseinput, fileutil, convertwaiveredfits, readgeis
from astropy.io import fits
import os


def checkFiles(filelist,ivmlist = None):
    """
    - Converts waiver fits sciece and data quality files to MEF format
    - Converts GEIS science and data quality files to MEF format
    - Checks for stis association tables and splits them into single imsets
    - Removes files with EXPTIME=0 and the corresponding ivm files
    - Removes files with NGOODPIX == 0 (to exclude saturated images)
    - Removes files with missing PA_V3 keyword

    The list of science files should match the list of ivm files at the end.
    """
    toclose = False
    if isinstance(filelist[0], str):
        toclose = True
    newfilelist, ivmlist = checkFITSFormat(filelist, ivmlist)

    # check for STIS association files. This must be done before
    # the other checks in order to handle correctly stis
    # assoc files
    newfilelist, ivmlist = checkStisFiles(newfilelist, ivmlist)
    if newfilelist == []:
        return [], []
    removed_expt_files = check_exptime(newfilelist)

    newfilelist, ivmlist = update_input(newfilelist, ivmlist, removed_expt_files)
    if newfilelist == []:
        return [], []
    removed_ngood_files = checkNGOODPIX(newfilelist)
    newfilelist, ivmlist = update_input(newfilelist, ivmlist, removed_ngood_files)
    if newfilelist == []:
        return [], []

    removed_pav3_files = checkPA_V3(newfilelist)
    newfilelist, ivmlist = update_input(newfilelist, ivmlist, removed_pav3_files)

    newfilelist, ivmlist = update_input(newfilelist, ivmlist,[])

    if newfilelist == []:
        return [], []

    if toclose:
        newfilelist = [hdul.filename() for hdul in newfilelist]
    return newfilelist, ivmlist

def checkFITSFormat(filelist, ivmlist=None):
    """
    This code will check whether or not files are GEIS or WAIVER FITS and
    convert them to MEF if found. It also keeps the IVMLIST consistent with
    the input filelist, in the case that some inputs get dropped during
    the check/conversion.
    """
    if ivmlist is None:
        ivmlist = [None for l in filelist]

    sci_ivm = list(zip(filelist, ivmlist))

    removed_files, translated_names, newivmlist = convert2fits(sci_ivm)
    newfilelist, ivmlist = update_input(filelist, ivmlist, removed_files)

    if newfilelist == [] and translated_names == []:
        return [], []

    elif translated_names != []:
        newfilelist.extend(translated_names)
        ivmlist.extend(newivmlist)

    return newfilelist, ivmlist


def checkStisFiles(filelist, ivmlist=None):
    newflist = []
    newilist = []
    removed_files = []
    assoc_files = []
    assoc_ilist = []

    if len(filelist) != len(ivmlist):
        errormsg = "Input file list and ivm list have different lenghts\n"
        errormsg += "Quitting ...\n"
        raise ValueError(errormsg)

    toclose = False
    for t in zip(filelist, ivmlist):
        if isinstance(t[0], str):
            t = (fits.open(t[0]), t[1])
            toclose = True
        if t[0][0].header['INSTRUME'] != 'STIS':
            newflist.append(t[0])
            newilist.append(t[1])
            continue
        if isSTISSpectroscopic(t[0]):
            removed_files.append(t[0])
            continue
        sci_count = stisObsCount(t[0])
        stisExt2PrimKw([t[0]])
        if sci_count >1:
            newfilenames = splitStis(t[0], sci_count)

            assoc_files.extend(newfilenames)
            removed_files.append(t[0])
            if (isinstance(t[1], tuple) and t[1][0] is not None) or \
               (not isinstance(t[1], tuple) and t[1] is not None):
                print('Does not handle STIS IVM files and STIS association files\n')
            else:
                asn_ivmlist = list(zip(sci_count * [None], newfilenames))
                assoc_ilist.extend(asn_ivmlist)
        elif sci_count == 1:
            newflist.append(t[0])
            newilist.append(t[1])
        else:
            errormsg = "No valid 'SCI extension in STIS file\n"
            raise ValueError(errormsg)

        if toclose:
            t[0].close()
    newflist.extend(assoc_files)
    newilist.extend(assoc_ilist)
    return newflist, newilist

def check_exptime(filelist):
    """
    Removes files with EXPTIME==0 from filelist.
    """
    toclose = False
    removed_files = []
    for f in filelist:
        if isinstance(f, str):
            f = fits.open(f)
            toclose = True

        try:
            exptime = f[0].header['EXPTIME']
        except KeyError:
            removed_files.append(f)
            print("Warning:  There are files without keyword EXPTIME")
            continue
        if exptime <= 0:
            removed_files.append(f)
            print("Warning:  There are files with zero exposure time: keyword EXPTIME = 0.0")

    if removed_files != []:
        print("Warning:  Removing the following files from input list")
        for f in removed_files:
            print('\t',f.filename() or "")
    return removed_files

def checkNGOODPIX(filelist):
    """
    Only for ACS, WFC3 and STIS, check NGOODPIX
    If all pixels are 'bad' on all chips, exclude this image
    from further processing.
    Similar checks requiring comparing 'driz_sep_bits' against
    WFPC2 c1f.fits arrays and NICMOS DQ arrays will need to be
    done separately (and later).
    """
    toclose = False
    removed_files = []
    supported_instruments = ['ACS','STIS','WFC3']
    for inputfile in filelist:
        if isinstance(inputfile, str):
            if fileutil.getKeyword(inputfile,'instrume') in supported_instruments:
                inputfile = fits.open(inputfile)
                toclose = True
        elif inputfile[0].header['instrume'] not in supported_instruments:
            continue

        ngood = 0
        for extn in inputfile:
            if 'EXTNAME' in extn.header and extn.header['EXTNAME'] == 'SCI':
                ngood += extn.header['NGOODPIX']
        if (ngood == 0):
            removed_files.append(inputfile)
        if toclose:
            inputfile.close()

    if removed_files != []:
        print("Warning:  Files without valid pixels detected: keyword NGOODPIX = 0.0")
        print("Warning:  Removing the following files from input list")
        for f in removed_files:
            print('\t',f.filename() or "")

    return removed_files

def update_input(filelist, ivmlist=None, removed_files=None):
    """
    Removes files flagged to be removed from the input filelist.
    Removes the corresponding ivm files if present.
    """
    newfilelist = []

    if removed_files == []:
        return filelist, ivmlist
    else:
        sci_ivm = list(zip(filelist, ivmlist))
        for f in removed_files:
            result = [sci_ivm.remove(t) for t in sci_ivm if t[0] == f ]
        ivmlist = [el[1] for el in sci_ivm]
        newfilelist = [el[0] for el in sci_ivm]
        return newfilelist, ivmlist


def stisObsCount(input):
    """
    Input: A stis multiextension file
    Output: Number of stis science extensions in input
    """
    count = 0
    toclose = False
    if isinstance(input, str):
        input = fits.open(input)
        toclose = True
    for ext in input:
        if 'extname' in ext.header:
            if (ext.header['extname'].upper() == 'SCI'):
                count += 1
    if toclose:
        input.close()
    return count

def splitStis(stisfile, sci_count):
    """
    Split a STIS association file into multiple imset MEF files.

    Split the corresponding spt file if present into single spt files.
    If an spt file can't be split or is missing a Warning is printed.

    Returns
    -------
    names: list
        a list with the names of the new flt files.

    """
    newfiles = []

    toclose = False
    if isinstance(stisfile, str):
        f = fits.open(stisfile)
        toclose = True
    else:
        f = stisfile
    hdu0 = f[0].copy()
    stisfilename = stisfile.filename()

    for count in range(1,sci_count+1):
        fitsobj = fits.HDUList()
        fitsobj.append(hdu0)
        hdu = f[('sci',count)].copy()
        fitsobj.append(hdu)
        rootname = hdu.header['EXPNAME']
        newfilename = fileutil.buildNewRootname(rootname, extn='_flt.fits')
        try:
            # Verify error array exists
            if f[('err', count)].data is None:
                raise ValueError
            # Verify dq array exists
            if f[('dq', count)].data is None:
                raise ValueError
            # Copy the err extension
            hdu = f[('err',count)].copy()
            fitsobj.append(hdu)
            # Copy the dq extension
            hdu = f[('dq',count)].copy()
            fitsobj.append(hdu)
            fitsobj[1].header['EXTVER'] = 1
            fitsobj[2].header['EXTVER'] = 1
            fitsobj[3].header['EXTVER'] = 1

        except ValueError:
            print('\nWarning:')
            print('Extension version %d of the input file %s does not' %(count, stisfile))
            print('contain all required image extensions. Each must contain')
            print('populates SCI, ERR and DQ arrays.')

            continue


        # Determine if the file you wish to create already exists on the disk.
        # If the file does exist, replace it.
        if (os.path.exists(newfilename)):
            os.remove(newfilename)
            print("       Replacing "+newfilename+"...")

            # Write out the new file
        fitsobj.writeto(newfilename)
        # Insure returned HDUList is associated with a file
        fitsobj.close()
        fitsobj = fits.open(newfilename, mode='update')
        newfiles.append(fitsobj) # Return HDUList, not filename

    f.close()

    sptfilename = fileutil.buildNewRootname(stisfilename, extn='_spt.fits')
    try:
        sptfile = fits.open(sptfilename)
    except IOError:
        print('SPT file not found %s \n' % sptfilename)
        return newfiles

    if sptfile:
        hdu0 = sptfile[0].copy()
        try:
            for count in range(1,sci_count+1):
                fitsobj = fits.HDUList()
                fitsobj.append(hdu0)
                hdu = sptfile[count].copy()
                fitsobj.append(hdu)
                rootname = hdu.header['EXPNAME']
                newfilename = fileutil.buildNewRootname(rootname, extn='_spt.fits')
                fitsobj[1].header['EXTVER'] = 1
                if (os.path.exists(newfilename)):
                    os.remove(newfilename)
                    print("       Replacing "+newfilename+"...")

                # Write out the new file
                fitsobj.writeto(newfilename)
        except:
            print("Warning: Unable to split spt file %s " % sptfilename)
        if toclose:
            sptfile.close()

    return newfiles

def stisExt2PrimKw(stisfiles):
    """
        Several kw which are usually in the primary header
        are in the extension header for STIS. They are copied to
        the primary header for convenience.
        List if kw:
        'DATE-OBS', 'EXPEND', 'EXPSTART', 'EXPTIME'
    """

    kw_list = ['DATE-OBS', 'EXPEND', 'EXPSTART', 'EXPTIME']

    for sfile in stisfiles:
        toclose = False

        if isinstance(sfile, str):
            sfile = fits.open(sfile, mode='update')
            toclose = True

        #d = {}
        for k in kw_list:
            sfile[0].header[k] = sfile[1].header[k]
            sfile[0].header.comments[k] = "Copied from extension header"
        if toclose:
            sfile.close()


def isSTISSpectroscopic(fname):

    if (isinstance(fname, fits.HDUList) and fname[0].header['OBSTYPE'] == 'SPECTROSCOPIC'
        or isinstance(fname, str) and fits.getval(fname, 'OBSTYPE') == 'SPECTROSCOPIC'):
        print("Warning:  STIS spectroscopic files detected")
        print("Warning:  Removing %s from input list" % fname)
        return True
    else:
        return False

def checkPA_V3(fnames):
    removed_files = []
    for f in fnames:
        toclose = False
        if isinstance(f, str):
            f = fits.open(f)
            toclose = True
        try:
            pav3 = f[0].header['PA_V3']
        except KeyError:
            rootname = f[0].header['ROOTNAME']
            sptfile = rootname+'_spt.fits'
            if fileutil.findFile(sptfile):
                try:
                    pav3 = fits.getval(sptfile, 'PA_V3')
                except KeyError:
                    print("Warning:  Files without keyword PA_V3 detected")
                    removed_files.append(f.filename() or "")
                f[0].header['PA_V3'] = pav3
            else:
                print("Warning:  Files without keyword PA_V3 detected")
                removed_files.append(f.filename() or "")
        if toclose:
            f.close()
    if removed_files != []:
        print("Warning:  Removing the following files from input list")
        for f in removed_files:
            print('\t',f)
    return removed_files

def convert2fits(sci_ivm):
    """
    Checks if a file is in WAIVER of GEIS format and converts it to MEF
    """
    removed_files = []
    translated_names = []
    newivmlist = []

    for file in sci_ivm:
        #find out what the input is
        # if science file is not found on disk, add it to removed_files for removal
        try:
            imgfits,imgtype = fileutil.isFits(file[0])
        except IOError:
            print("Warning:  File %s could not be found" %file[0])
            print("Warning:  Removing file %s from input list" %file[0])
            removed_files.append(file[0])
            continue

        # Check for existence of waiver FITS input, and quit if found.
        # Or should we print a warning and continue but not use that file
        if imgfits and imgtype == 'waiver':
            newfilename = waiver2mef(file[0], convert_dq=True)
            if newfilename is None:
                print("Removing file %s from input list - could not convert WAIVER format to MEF\n" %file[0])
                removed_files.append(file[0])
            else:
                removed_files.append(file[0])
                translated_names.append(newfilename)
                newivmlist.append(file[1])

        # If a GEIS image is provided as input, create a new MEF file with
        # a name generated using 'buildFITSName()'
        # Convert the corresponding data quality file if present
        if not imgfits:
            newfilename = geis2mef(file[0], convert_dq=True)
            if newfilename is None:
                print("Removing file %s from input list - could not convert GEIS format to MEF\n" %file[0])
                removed_files.append(file[0])
            else:
                removed_files.append(file[0])
                translated_names.append(newfilename)
                newivmlist.append(file[1])

    return removed_files, translated_names, newivmlist

def waiver2mef(sciname, newname=None, convert_dq=True, writefits=True):
    """
    Converts a GEIS science file and its corresponding
    data quality file (if present) to MEF format
    Writes out both files to disk.
    Returns the new name of the science image.
    """

    if isinstance(sciname, fits.HDUList):
        filename = sciname.filename()
    else:
        filename = sciname

    try:
        clobber = True
        fimg = convertwaiveredfits.convertwaiveredfits(filename)

        #check for the existence of a data quality file
        _dqname = fileutil.buildNewRootname(filename, extn='_c1f.fits')
        dqexists = os.path.exists(_dqname)
        if convert_dq and dqexists:
            try:
                dqfile = convertwaiveredfits.convertwaiveredfits(_dqname)
                dqfitsname = fileutil.buildNewRootname(_dqname, extn='_c1h.fits')
            except Exception:
                print("Could not read data quality file %s" % _dqname)
        if writefits:
            # User wants to make a FITS copy and update it
            # using the filename they have provided
            rname = fileutil.buildNewRootname(filename)
            fitsname = fileutil.buildNewRootname(rname, extn='_c0h.fits')

            # Write out GEIS image as multi-extension FITS.
            fexists = os.path.exists(fitsname)
            if (fexists and clobber) or not fexists:
                print('Writing out WAIVERED as MEF to ', fitsname)
                fimg.writeto(fitsname, overwrite=clobber)
                if dqexists:
                    print('Writing out WAIVERED as MEF to ', dqfitsname)
                    dqfile.writeto(dqfitsname, overwrite=clobber)

        # Now close input GEIS image, and open writable
        # handle to output FITS image instead...
        fimg.close()
        del fimg

        fimg = fits.open(fitsname, mode='update', memmap=False)

        return fimg
    except IOError:
        print('Warning: File %s could not be found' % sciname)
        return None


def geis2mef(sciname, convert_dq=True):
    """
    Converts a GEIS science file and its corresponding
    data quality file (if present) to MEF format
    Writes out both files to disk.
    Returns the new name of the science image.
    """
    clobber = True
    mode = 'update'
    memmap = True
    # Input was specified as a GEIS image, but no FITS copy
    # exists.  Read it in with 'readgeis' and make a copy
    # then open the FITS copy...
    try:
        # Open as a GEIS image for reading only
        fimg = readgeis.readgeis(sciname)
    except Exception:
        raise IOError("Could not open GEIS input: %s" % sciname)

    #check for the existence of a data quality file
    _dqname = fileutil.buildNewRootname(sciname, extn='.c1h')
    dqexists = os.path.exists(_dqname)
    if dqexists:
        try:
            dqfile = readgeis.readgeis(_dqname)
            dqfitsname = fileutil.buildFITSName(_dqname)
        except Exception:
            print("Could not read data quality file %s" % _dqname)

    # Check to see if user wanted to update GEIS header.
    # or write out a multi-extension FITS file and return a handle to it
    # User wants to make a FITS copy and update it
    # using the filename they have provided
    fitsname = fileutil.buildFITSName(sciname)

    # Write out GEIS image as multi-extension FITS.
    fexists = os.path.exists(fitsname)
    if (fexists and clobber) or not fexists:
            print('Writing out GEIS as MEF to ', fitsname)
            fimg.writeto(fitsname, overwrite=clobber)
            if dqexists:
                print('Writing out GEIS as MEF to ', dqfitsname)
                dqfile.writeto(dqfitsname, overwrite=clobber)

    # Now close input GEIS image, and open writable
    # handle to output FITS image instead...
    fimg.close()
    del fimg
    fimg = fits.open(fitsname, mode=mode, memmap=memmap)

    return fimg


def countInput(input):
    files = parseinput.parseinput(input)
    count = len(files[0])
    for f in files[0]:
        if fileutil.isFits(f)[0]:
            try:
                ins = fits.getval(f, 'INSTRUME')
            except Exception:  # allow odd fits files; do not stop the count
                ins = None
            if ins == 'STIS':
                count += (stisObsCount(f)-1)
    return count
