from pytools import parseinput, fileutil, readgeis, asnutil,irafglob
import pyfits
import os 

def checkFiles(filelist,ivmlist = None):
    """
    1. Converts waiver fits sciece and data quality files to MEF format
    2. Converts all GEIS science and data quality files to MEF format
    3. Checks for stis association tables 
    4. Checks if kw idctab exists, if not tries to populate it 
        based on the spt file
    5. Removes files with EXPTIME=0 and the corresponding ivm files
    6. Removes files with NGOODPIX == 0 (to exclude saturated images)
    """
    removed_files = []
    translated_names = []
    newivmlist = []
    
    if ivmlist == None:
        ivmlist = [None for l in filelist]

    sci_ivm = zip(filelist, ivmlist)
    
    for file in sci_ivm:
        #find out what the input is
        # if science file is not found on disk, add it to removed_files for removal
        try:
            imgfits,imgtype = fileutil.isFits(file[0])
        except IOError:
            print "Warning:  File %s could not be found\n" %file[0]
            print "Removing file %s from input list" %file[0]
            removed_files.append(file)
            continue
        if file[1] != None:
            #If an ivm file is not found on disk
            # Remove the corresponding science file
            try:
                ivmfits,ivmtype = fileutil.isFits(file[1])
            except IOError:
                print "Warning:  File %s could not be found\n" %file[1]
                print "Removing file %s from input list" %file[0]
                removed_files.append(file)
        # Check for existence of waiver FITS input, and quit if found.
        # Or should we print a warning and continue but not use that file
        if imgfits and imgtype == 'waiver':
            newfilename = waiver2mef(file[0], convert_dq=True)
            if newfilename == None:
                print "Removing file %s from input list - could not convert waiver to mef" %file[0]
                removed_files.append(file[0])
            else:
                translated_names.append(newfilename)

        # If a GEIS image is provided as input, create a new MEF file with 
        # a name generated using 'buildFITSName()'
        # Convert the corresponding data quality file if present    
        if not imgfits:
            newfilename = geis2mef(file[0], convert_dq=True)
            if newfilename == None:
                print "Removing file %s from input list - could not convert geis to mef" %file[0]
                removed_files.append(file[0])
            else:
                translated_names.append(newfilename)
        if file[1] != None:
            if ivmfits and ivmtype == 'waiver':
                print "Warning: PyDrizzle does not support waiver fits format.\n"
                print "Convert the input files to GEIS or multiextension FITS.\n"
                print "File %s appears to be in waiver fits format \n" %file[1]
                print "Removing file %s from input list" %file[0] 
                removed_files.append(file[0])
  
            if not ivmfits:
                newfilename = geis2mef(file[1], convert_dq=False)
                if newfilename == None:
                    print "Removing file %s from input list" %file[0]
                    removed_files.append(file[0])
                else:
                    newivmlist.append(newfilename)

    newfilelist, ivmlist = update_input(filelist, ivmlist, removed_files)

    if newfilelist == []:
        return [], []
    
    if translated_names != []:
        # Since we don't allow input from different instruments
        # we can abandon the original input list and provide as 
        # input only the translated names
        removed_expt_files = check_exptime(translated_names)
        newfilelist, ivmlist = update_input(translated_names, newivmlist, removed_expt_files)
    else:
        # check for STIS association files. This must be done before 
        # the check for EXPTIME in order to handle correctly stis 
        # assoc files
        if pyfits.getval(newfilelist[0], 'INSTRUME') == 'STIS':
            newfilelist, ivmlist = checkStisFiles(newfilelist, ivmlist)
            #removed_files = check_exptime(newflist)
        
        removed_expt_files = check_exptime(newfilelist)
        newfilelist, ivmlist = update_input(newfilelist, ivmlist, removed_expt_files)
    if removed_expt_files:
        errorstr =  "#############################################\n"
        errorstr += "#                                           #\n"
        errorstr += "# ERROR:                                    #\n"
        errorstr += "#                                           #\n"
        errorstr += "#  The following files were excluded from   #\n"
        errorstr += "#  Multidrizzle processing because their    #\n"
        errorstr += "#  header keyword EXPTIME values were 0.0:  #\n"
        for name in removed_expt_files:
            errorstr += "         "+ str(name) + "\n" 
        errorstr += "#                                           #\n"
        errorstr += "#############################################\n\n"
        print errorstr
        
    removed_ngood_files = checkNGOODPIX(newfilelist)
    newfilelist, ivmlist = update_input(newfilelist, ivmlist, removed_ngood_files)
    if removed_ngood_files:
        msgstr =  "####################################\n"
        msgstr += "#                                  #\n"
        msgstr += "# WARNING:                         #\n"
        msgstr += "#  NGOODPIX keyword value of 0 in  #\n"
        for name in removed_ngood_files:
            msgstr += "         "+ str(name) + "\n" 
        msgstr += "#  has been detected.  Images with #\n"
        msgstr += "#  no valid pixels will not be     #\n"
        msgstr += "#  used during processing.  If you #\n"
        msgstr += "#  wish this file to be used in    #\n"
        msgstr += "#  processing, please check its DQ #\n"
        msgstr += "#  array and reset driz_sep_bits   #\n"
        msgstr += "#  and final_bits parameters       #\n"
        msgstr += "#  to accept flagged pixels.       #\n"
        msgstr += "#                                  #\n"
        msgstr += "####################################\n"
        print msgstr   
                
    return newfilelist, ivmlist
    
def waiver2mef(sciname, newname=None, convert_dq=True):
    """
    Converts a GEIS science file and its corresponding 
    data quality file (if present) to MEF format
    Writes out both files to disk.
    Returns the new name of the science image.
    """
    
    def convert(file):
        newfilename = fileutil.buildNewRootname(file, extn='_c0h.fits')
        try:
            newimage = fileutil.openImage(file,writefits=True,
                                          fitsname=newfilename,clobber=True)
            del newimage
            return newfilename
        except IOError:
            print 'Warning: File %s could not be found' % file     
            return None
        
    newsciname = convert(sciname)
    if convert_dq:
        dq_name = convert(fileutil.buildNewRootname(sciname, extn='_c1h.fits'))
        
    return newsciname   



def geis2mef(sciname, convert_dq=True):
    """
    Converts a GEIS science file and its corresponding 
    data quality file (if present) to MEF format
    Writes out both files to disk.
    Returns the new name of the science image.
    """
        
    def convert(file):
        newfilename = fileutil.buildFITSName(file)
        try:
            newimage = fileutil.openImage(file,writefits=True,
                fitsname=newfilename, clobber=True)            
            del newimage
            return newfilename
        except IOError:
            print 'Warning: File %s could not be found' % file     
            return None

    newsciname = convert(sciname)
    if convert_dq:
        dq_name = convert(sciname.split('.')[0] + '.c1h')
        
    return newsciname


def checkStisFiles(filelist, ivmlist=None):
    newflist = []
    newilist = []
    
    if len(filelist) != len(ivmlist):
        errormsg = "Input file list and ivm list have different lenghts\n"
        errormsg += "Quitting ...\n"
        raise ValueError, errormsg
        
    for t in zip(filelist, ivmlist):
        sci_count = stisObsCount(t[0])
        if sci_count >1:
            newfilenames = splitStis(t[0], sci_count)
            newflist.extend(newfilenames)
            if t[1] != None:
                newivmnames = splitStis(t[1], sci_count)
                newilist.extend(newivmnames)
            else:
                newilist.append(None)
        elif sci_count == 1:
            newflist.append(t[0])
            newilist.append(t[1])
        else:
            errormesg = "No valid 'SCI extension in STIS file\n"
            raise ValueError, errormsg
    
    if newflist != []:
        stisExt2PrimKw(newflist)
        
    return newflist, newilist




def check_exptime(filelist):
    """
    Removes files with EXPTIME==0 from filelist.
    """
    removed_files = []
    
    for f in filelist:
        if fileutil.getKeyword(f, 'EXPTIME') <= 0: 
            removed_files.append(f)
            
    return removed_files

def checkNGOODPIX(filelist):
    """
    Only for ACS, and STIS, check NGOODPIX
    If all pixels are 'bad' on all chips, exclude this image
    from further processing. 
    Similar checks requiring comparing 'driz_sep_bits' against
    WFPC2 c1f.fits arrays and NICMOS DQ arrays will need to be
    done separately (and later).
    """
    removed_files = []
    for inputfile in filelist:
        if (fileutil.getKeyword(inputfile,'instrume') == 'ACS') \
           or fileutil.getKeyword(inputfile,'instrume') == 'STIS': 
            _file = fileutil.openImage(inputfile)
            _ngood = 0
            for extn in _file:
                if extn.header.has_key('EXTNAME') and extn.header['EXTNAME'] == 'SCI':
                    _ngood += extn.header['NGOODPIX']
            _file.close()
            
            if (_ngood == 0):
                removed_files.append(inputfile)
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
        sci_ivm = zip(filelist, ivmlist)
        for f in removed_files:
            result=[sci_ivm.remove(t) for t in sci_ivm if t[0] == f ]
        ivmlist = [el[1] for el in sci_ivm] 
        newfilelist = [el[0] for el in sci_ivm] 
        return newfilelist, ivmlist 
  

def stisObsCount(input):
    """
    Input: A stis multiextension file
    Output: Number of stis science extensions in input
    """
    count = 0
    f = pyfits.open(input)
    for ext in f:
        if ext.header.has_key('extname'):
            if (ext.header['extname'].upper() == 'SCI'):
                count += 1
    f.close()
    return count

def splitStis(stisfile, sci_count):
    """
    Purpose
    =======
    
    Split a STIS association file into multiple imset MEF files.
    Split the corresponding spt file if present into single spt files.
    If an spt file can't be split or is missing a Warning is printed.
    
    Output: a list with the names of the new flt files.
    """
    newfiles = []
    
    f = pyfits.open(stisfile)
    hdu0 = f[0].copy()


    for count in range(1,sci_count+1):
        fitsobj = pyfits.HDUList()            
        fitsobj.append(hdu0)
        hdu = f[('sci',count)].copy()
        fitsobj.append(hdu)
        rootname = hdu.header['EXPNAME']
        newfilename = fileutil.buildNewRootname(rootname, extn='_flt.fits')
        try:
            # Verify error array exists
            if f[('err',count)].data == None:
                raise ValueError
            # Verify dq array exists
            if f[('dq',count)].data == None:
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
            print '\nWarning:'
            print 'Extension version %d of the input file %s does not' %(count, stisfile)
            print 'contain all required image extensions. Each must contain'
            print 'populates SCI, ERR and DQ arrays.'
            
            continue
            
        
        # Determine if the file you wish to create already exists on the disk.
        # If the file does exist, replace it.
        if (os.path.exists(newfilename)):
            os.remove(newfilename)
            print "       Replacing "+newfilename+"..."
            
            # Write out the new file
        fitsobj.writeto(newfilename)
        newfiles.append(newfilename)
    f.close()

    sptfilename = fileutil.buildNewRootname(stisfile, extn='_spt.fits')
    try:
        sptfile = pyfits.open(sptfilename)
    except IOError:
        print 'SPT file not found %s \n' % sptfilename
        return newfiles
    
    if sptfile:
        hdu0 = sptfile[0].copy()
        try:
            for count in range(1,sci_count+1):
                fitsobj = pyfits.HDUList()            
                fitsobj.append(hdu0)
                hdu = sptfile[count].copy()
                fitsobj.append(hdu)
                rootname = hdu.header['EXPNAME']
                newfilename = fileutil.buildNewRootname(rootname, extn='_spt.fits')
                fitsobj[1].header['EXTVER'] = 1
                if (os.path.exists(newfilename)):
                    os.remove(newfilename)
                    print "       Replacing "+newfilename+"..."
            
                # Write out the new file
                fitsobj.writeto(newfilename)
        except:
            print "Warning: Unable to split spt file %s " % sptfilename
        sptfile.close()
    
    return newfiles 

def stisExt2PrimKw(stisfiles):
    """
        Several kw which are usuall yin the primary header 
        are in the extension header for STIS. They are copied to
        the primary header for convenience.
        List if kw:
        'DATE-OBS', 'EXPEND', 'EXPSTART', 'EXPTIME'
    """

    kw_list = ['DATE-OBS', 'EXPEND', 'EXPSTART', 'EXPTIME']
    
    for sfile in stisfiles:
        d = {}
        for k in kw_list:
            d[k] = pyfits.getval(sfile, k, ext=1)
        
        for item in d.items():
            pyfits.setval(sfile, key=item[0], value=item[1], comment='Copied from extension header')
        
        