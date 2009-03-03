"""
MAKEWCS.PY - Updated the WCS in an image header so that
            it matches the geometric distortion defined in an IDC table
            which is referenced in the image header.

License: http://www.stsci.edu/resources/software_hardware/pyraf/LICENSE

This version tries to implement a full updating of the WCS based on
information about the V2/V3 plane which is obtained from th IDCTAB and,
in the case of WFPC2, the OFFTAB.

The only parameters from the original WCS which are retained are
the CRVALs of the reference chip.

The original WCS are first copied to MCD1_1 etc before being updated.

UPINCD history:
First try, Richard Hook, ST-ECF/STScI, August 2002.
Version 0.0.1 (WJH) - Obtain IDCTAB using PyDrizzle function.
Version 0.1 (WJH) - Added support for processing image lists.  
                    Revised to base CD matrix on ORIENTAT, instead of PA_V3
                    Supports subarrays by shifting coefficients as needed.
Version 0.2 (WJH) - Implemented orientation computation based on PA_V3 using
                    Troll function from Colin to compute new ORIENTAT value.
Version 0.3 (WJH) - Supported filter dependent distortion models in IDCTAB
                    fixed bugs in applying Troll function to WCS.
Version 0.4 (WJH) - Updated to support use of 'defaultModel' for generic 
                    cases: XREF/YREF defaults to image center and idctab
                    name defaults to None.
Version 0.5 (WJH) - Added support for WFPC2 OFFTAB updates, which updates
                    the CRVALs.  However, for WFPC2 data, the creation of
                    the backup values does not currently work.
---------------------------
MAKEWCS V0.0 (RNH) - Created new version to implement more complete
                     WCS creation based on a reference tangent plane.

        V0.1 (RNH) - First working version for tests. May 20th 2004.
        V0.11 (RNH) - changed reference chip for ACS/WFC. May 26th 2004.
        V0.2 (WJH) - Removed all dependencies from IRAF and use new WCSObject
                    class for all WCS operations.
        V0.4 (WJH/CJH) - Corrected logic for looping of extension in FITS image.
        V0.5 (RNH) - Chip to chip CRVAL shifting logic change.
        V0.6 (CJH/WJH) - Added support for non-associated STIS data.
        V0.6.2 (WJH) - Added support for NICMOS data. This required
                        new versions of wcsutil and fileutil in PyDrizzle.
        V0.6.3 (WJH) - Modified to support new version of WCSUtil which correctly
                        sets up and uses archived WCS keywords.
        V0.7.0 (WJH) - Revised algorithm to work properly with subarray images.
                        Also, simplified keyword access using PyFITS object.
        V0.8.0 (CJH) - Modified to work with either numarray or numpy through
                        the use of the numerix interface layer.
        
"""
import numerixenv
numerixenv.check()

#import iraf
from math import *
import string,types, os.path
import pyfits

from pydrizzle import drutil
from pydrizzle.distortion import models,mutil
from pytools import fileutil, wcsutil, parseinput
import numpy as N

yes = True
no = False

# Define parity matrices for supported detectors.
# These provide conversion from XY to V2/V3 coordinate systems.
# Ideally, this information could be included in IDCTAB...
PARITY = {'WFC':[[1.0,0.0],[0.0,-1.0]],'HRC':[[-1.0,0.0],[0.0,1.0]],
          'SBC':[[-1.0,0.0],[0.0,1.0]],'default':[[1.0,0.0],[0.0,1.0]],
          'WFPC2':[[-1.0,0.],[0.,1.0]],'STIS':[[-1.0,0.],[0.,1.0]],
          'NICMOS':[[-1.0,0.],[0.,1.0]], 'UVIS':[[-1.0,0.0],[0.0,1.0]], 
          'IR':[[-1.0,0.0],[0.0,1.0]]  }

NUM_PER_EXTN = {'ACS':3,'WFPC2':1,'STIS':3,'NICMOS':5, 'WFC3':3}

__version__ = '1.1.2 (4 Mar 2009)'
def run(input,quiet=yes,restore=no,prepend='O', tddcorr=True):

    print "+ MAKEWCS Version %s" % __version__
    
    _prepend = prepend

    files = parseinput.parseinput(input)[0]
    newfiles = []
    if files == []:
        print "No valid input files found.\n"
        raise IOError
    
    for image in files:
        #find out what the input is
        imgfits,imgtype = fileutil.isFits(image)
        
        # Check for existence of waiver FITS input, and quit if found.
        if imgfits and imgtype == 'waiver':
            """
            errormsg = '\n\nPyDrizzle does not support waiver fits format.\n'
            errormsg += 'Convert the input files to GEIS or multiextension FITS.\n\n'
            raise ValueError, errormsg
            """
            newfilename = fileutil.buildNewRootname(image, extn='_c0h.fits')
            # Convert GEIS image to MEF file
            newimage = fileutil.openImage(image,writefits=True,fitsname=newfilename,clobber=True)
            del newimage
            # Work with new file
            image = newfilename
            newfiles.append(image)
        # If a GEIS image is provided as input, create a new MEF file with 
        # a name generated using 'buildFITSName()' and update that new MEF file.
        if not imgfits:
            # Create standardized name for MEF file
            newfilename = fileutil.buildFITSName(image)
            # Convert GEIS image to MEF file
            newimage = fileutil.openImage(image,writefits=True,fitsname=newfilename,clobber=True)
            del newimage
            # Work with new file
            image = newfilename
            newfiles.append(image)
            
        if not quiet:
            print "Input files: ",files

        # First get the name of the IDC table
        #idctab = drutil.getIDCFile(_files[0][0],keyword='idctab')[0]
        idctab = drutil.getIDCFile(image,keyword='idctab')[0]
        _found = fileutil.findFile(idctab)
        if idctab == None or idctab == '':
            print '#\n No IDCTAB specified.  No correction can be done for file %s.Quitting makewcs\n' %image
            #raise ValueError
            continue
        elif not _found:
            print '#\n IDCTAB: ',idctab,' could not be found. \n'
            print 'WCS keywords for file %s will not be updated.\n' %image
            #raise IOError 
            continue

        _phdu = image + '[0]'
        _instrument = fileutil.getKeyword(_phdu,keyword='INSTRUME')
        if _instrument == 'WFPC2':
            Nrefchip, Nrefext = getNrefchip(image)
        else:
            Nrefchip = None
            Nrefext = None
        if not NUM_PER_EXTN.has_key(_instrument):

            raise "Instrument %s not supported yet. Exiting..."%_instrument
        
        _detector = fileutil.getKeyword(_phdu, keyword='DETECTOR')                          
        _nimsets = get_numsci(image)
        
        for i in xrange(_nimsets):
            if image.find('.fits') > 0:
                _img = image+'[sci,'+repr(i+1)+']'
            else:
                _img = image+'['+repr(i+1)+']'
            if not restore:
                if not quiet: 
                    print 'Updating image: ', _img
                  
                _update(_img,idctab, _nimsets, apply_tdd=False,
                        quiet=quiet,instrument=_instrument,prepend=_prepend, 
                        nrchip=Nrefchip, nrext = Nrefext)
                if _instrument == 'ACS' and _detector == 'WFC':
                    tddswitch = fileutil.getKeyword(_phdu,keyword='TDDCORR')
                    # This logic requires that TDDCORR be in the primary header 
                    # and set to PERFORM in order to turn this on at all. It can
                    # be turned off by setting either tddcorr=False or setting
                    # the keyword to anything but PERFORM or by deleting the 
                    # keyword altogether. PyDrizzle will rely simply on the 
                    # values of alpha and beta as computed here to apply the 
                    # correction to the coefficients.
                    if (tddcorr and tddswitch != 'OMIT'):
                        print 'Applying time-dependent distortion corrections...'
                        _update(_img,idctab, _nimsets, apply_tdd=True, \
                        quiet=quiet,instrument=_instrument,prepend=_prepend, nrchip=Nrefchip, nrext = Nrefext)
            else:                    
                if not quiet:
                    print 'Restoring original WCS values for',_img  
                restoreCD(_img,_prepend)
        
        #fimg = fileutil.openImage(image,mode='update')
        #if fimg[0].header.has_key('TDDCORR') and fimg[0].header['TDDCORR'] == 'PERFORM':
        #    fimg[0].header['TDDCORR'] = 'COMPLETE'
        #fimg.close()
        
    if newfiles == []:
        return files
    else:
        return newfiles
    
def restoreCD(image,prepend):
    
    _prepend = prepend
    try:
        _wcs = wcsutil.WCSObject(image)
        _wcs.restoreWCS(prepend=_prepend)
        del _wcs
    except: 
        print 'ERROR: Could not restore WCS keywords for %s.'%image

def _update(image,idctab,nimsets,apply_tdd=False,
            quiet=None,instrument=None,prepend=None,nrchip=None, nrext=None):
    
    tdd_xyref = {1: [2048, 3072], 2:[2048, 1024]}
    _prepend = prepend
    _dqname = None        
    # Make a copy of the header for keyword access
    # This copy includes both Primary header and 
    # extension header
    hdr = fileutil.getHeader(image)

    # Try to get the instrument if we don't have it already
    instrument = readKeyword(hdr,'INSTRUME')

    binned = 1
    # Read in any specified OFFTAB, if present (WFPC2)
    offtab = readKeyword(hdr,'OFFTAB')
    dateobs = readKeyword(hdr,'DATE-OBS')
    if not quiet:
        print "OFFTAB, DATE-OBS: ",offtab,dateobs
    
    print "-Updating image ",image

    if not quiet:
        print "-Reading IDCTAB file ",idctab

    # Get telescope orientation from image header
    # If PA_V# is not present of header, try to get it from the spt file
    pvt = readKeyword(hdr,'PA_V3')
    if pvt == None:
        sptfile = fileutil.buildNewRootname(image, extn='_spt.fits')
        if os.path.exists(sptfile):
            spthdr = fileutil.getHeader(sptfile)
            pvt = readKeyword(spthdr,'PA_V3')
    if pvt != None:
        pvt = float(pvt)
    else:
        print 'PA_V3 keyword not found, WCS cannot be updated. Quitting ...'
        raise ValueError
    
    # Find out about instrument, detector & filters
    detector = readKeyword(hdr,'DETECTOR')

    Nrefchip=1
    if instrument == 'WFPC2':
        filter1 = readKeyword(hdr,'FILTNAM1')
        filter2 = readKeyword(hdr,'FILTNAM2')
        mode = readKeyword(hdr,'MODE')
        if os.path.exists(fileutil.buildNewRootname(image, extn='_c1h.fits')):
            _dqname = fileutil.buildNewRootname(image, extn='_c1h.fits')
            dqhdr = pyfits.getheader(_dqname,1)
            dqext = readKeyword(dqhdr, 'EXTNAME')
        if mode == 'AREA':
            binned = 2
        Nrefchip=nrchip
    elif instrument == 'NICMOS':
        filter1 = readKeyword(hdr,'FILTER')
        filter2 = None
    elif instrument == 'WFC3':
        filter1 = readKeyword(hdr,'FILTER')
        filter2 = None
        #filter2 = readKeyword(hdr,'FILTER2')
    else:
        filter1 = readKeyword(hdr,'FILTER1')
        filter2 = readKeyword(hdr,'FILTER2')
    
    if filter1 == None or filter1.strip() == '': filter1 = 'CLEAR'
    else: filter1 = filter1.strip()
    if filter2 == None or filter2.strip() == '': filter2 = 'CLEAR'
    else: filter2 = filter2.strip()
    
    if filter1.find('CLEAR') == 0: filter1 = 'CLEAR'
    if filter2.find('CLEAR') == 0: filter2 = 'CLEAR'
    
    # Set up parity matrix for chip
    if instrument == 'WFPC2' or instrument =='STIS' or instrument == 'NICMOS':
        parity = PARITY[instrument]
    elif PARITY.has_key(detector):
       parity = PARITY[detector]
    else:
        raise 'Detector ',detector,' Not supported at this time. Exiting...'

    # If ACS get the VAFACTOR, otherwise set to 1.0
    # we also need the reference pointing position of the target
    # as this is where
    VA_fac=1.0
    if instrument == 'ACS':
       _va_key = readKeyword(hdr,'VAFACTOR')
       if _va_key != None: 
          VA_fac = float(_va_key)
       
       if not quiet:
          print 'VA factor: ',VA_fac
       
    #ra_targ = float(readKeyword(hdr,'RA_TARG'))
    #dec_targ = float(readKeyword(hdr,'DEC_TARG'))

    # Get the chip number
    _c = readKeyword(hdr,'CAMERA')
    _s = readKeyword(hdr,'CCDCHIP')
    _d = readKeyword(hdr,'DETECTOR')
    if _c != None and str(_c).isdigit():
        chip = int(_c)
    elif _s == None and _d == None:
        chip = 1
    else:
        if _s:
            chip = int(_s)
        elif str(_d).isdigit():
            chip = int(_d)
        else:
            chip = 1
    # For the ACS/WFC case the chip number doesn't match the image
    # extension
    nr = 1
    if instrument == 'ACS' and detector == 'WFC':
        if nimsets > 1:
          Nrefchip = 2
        else:
          Nrefchip = chip
    elif instrument == 'NICMOS':
        Nrefchip = readKeyword(hdr,'CAMERA')
    elif instrument == 'WFPC2':
        nr = nrext
    else:
       if nimsets > 1:
          nr = Nrefchip

    if not quiet:
        print "-PA_V3 : ",pvt," CHIP #",chip

    # Determine whether to perform time-dependent correction
    # Construct matrices neded to correct the zero points for TDD
    if apply_tdd:
        alpha,beta = mutil.compute_wfc_tdd_coeffs(dateobs)
        tdd = N.array([[beta, alpha], [alpha, -beta]])
        mrotp = fileutil.buildRotMatrix(2.234529)/2048.
        
    else:
        alpha = 0.0
        beta = 0.0
        
    # Extract the appropriate information from the IDCTAB
    #fx,fy,refpix,order=fileutil.readIDCtab(idctab,chip=chip,direction='forward',
    #            filter1=filter1,filter2=filter2,offtab=offtab,date=dateobs)
    idcmodel = models.IDCModel(idctab,
                    chip=chip, direction='forward', date=dateobs,
                    filter1=filter1, filter2=filter2, offtab=offtab, binned=binned,
                    tddcorr=apply_tdd)
    fx = idcmodel.cx
    fy = idcmodel.cy
    refpix = idcmodel.refpix
    order = idcmodel.norder

    # Get the original image WCS
    Old=wcsutil.WCSObject(image,prefix=_prepend)
    
    # Reset the WCS keywords to original archived values.
    Old.restore()
 
    #
    # Look for any subarray offset
    #
    ltv1,ltv2 = drutil.getLTVOffsets(image)
    #
    # If reference point is not centered on distortion model
    # shift coefficients to be applied relative to observation
    # reference position
    #
    offsetx = Old.crpix1 - ltv1 - refpix['XREF']
    offsety = Old.crpix2 - ltv2 - refpix['YREF']
    shiftx = refpix['XREF'] + ltv1
    shifty = refpix['YREF'] + ltv2
    if ltv1 != 0. or ltv2 != 0.:
        ltvoffx = ltv1 + offsetx
        ltvoffy = ltv2 + offsety
        offshiftx = offsetx + shiftx
        offshifty = offsety + shifty
    else:
        ltvoffx = 0.
        ltvoffy = 0.
        offshiftx = 0.
        offshifty = 0.

    if ltv1 != 0. or ltv2 != 0.:
       fx,fy = idcmodel.shift(idcmodel.cx,idcmodel.cy,offsetx,offsety)

    # Extract the appropriate information for reference chip
    rfx,rfy,rrefpix,rorder=mutil.readIDCtab(idctab,chip=Nrefchip,
        direction='forward', filter1=filter1,filter2=filter2,offtab=offtab, 
        date=dateobs,tddcorr=apply_tdd)

    # Create the reference image name
    rimage = image.split('[')[0]+"[sci,%d]" % nr
    if not quiet:
       print "Reference image: ",rimage       
 
    # Create the tangent plane WCS on which the images are defined
    # This is close to that of the reference chip
    R=wcsutil.WCSObject(rimage)
    R.write_archive(rimage)
    R.restore()

    # Reacd in declination of target (for computing orientation at aperture)
    # Note that this is from the reference image
    #dec = float(fileutil.getKeyword(rimage,'CRVAL2'))
    #crval1 = float(fileutil.getKeyword(rimage,'CRVAL1'))
    #crval1 = float(R.crval1)
    #crval2 = dec
    dec = float(R.crval2)
    
    # Get an approximate reference position on the sky
    rref = (rrefpix['XREF']+ltvoffx, rrefpix['YREF']+ltvoffy)
    
    crval1,crval2=R.xy2rd(rref)
    
    if apply_tdd:
        # Correct zero points for TDD
        tddscale = (R.pscale/fx[1][1])
        rxy0 = N.array([[tdd_xyref[Nrefchip][0]-2048.],[ tdd_xyref[Nrefchip][1]-2048.]])
        xy0 = N.array([[tdd_xyref[chip][0]-2048.], [tdd_xyref[chip][1]-2048.]])
        rv23_corr = N.dot(mrotp,N.dot(tdd,rxy0))*tddscale
        v23_corr = N.dot(mrotp,N.dot(tdd,xy0))*tddscale
    else:
        rv23_corr = N.array([[0],[0]])
        v23_corr = N.array([[0],[0]])
        
    # Convert the PA_V3 orientation to the orientation at the aperture
    # This is for the reference chip only - we use this for the
    # reference tangent plane definition
    # It has the same orientation as the reference chip
    v2ref = rrefpix['V2REF'] +  rv23_corr[0][0]*0.05
    v3ref = rrefpix['V3REF'] - rv23_corr[1][0]*0.05
    v2 = refpix['V2REF'] + v23_corr[0][0]*0.05
    v3 = refpix['V3REF'] - v23_corr[1][0] *0.05    

    pv = wcsutil.troll(pvt,dec,v2ref,v3ref)

    # Add the chip rotation angle
    if rrefpix['THETA']:
        pv += rrefpix['THETA']
       

    # Set values for the rest of the reference WCS
    R.crval1=crval1
    R.crval2=crval2
    R.crpix1=0.0 + offshiftx
    R.crpix2=0.0 + offshifty
    
    R_scale=rrefpix['PSCALE']/3600.0
    R.cd11=parity[0][0] *  cos(pv*pi/180.0)*R_scale
    R.cd12=parity[0][0] * -sin(pv*pi/180.0)*R_scale
    R.cd21=parity[1][1] *  sin(pv*pi/180.0)*R_scale
    R.cd22=parity[1][1] *  cos(pv*pi/180.0)*R_scale
        
    ##print R
    R_cdmat = N.array([[R.cd11,R.cd12],[R.cd21,R.cd22]])
    
    if not quiet:
        print "  Reference Chip Scale (arcsec/pix): ",rrefpix['PSCALE']

    # Offset and angle in V2/V3 from reference chip to
    # new chip(s) - converted to reference image pixels
    
    off = sqrt((v2-v2ref)**2 + (v3-v3ref)**2)/(R_scale*3600.0)

    # Here we must include the PARITY
    if v3 == v3ref:
       theta=0.0
    else:
       theta = atan2(parity[0][0]*(v2-v2ref),parity[1][1]*(v3-v3ref))

    if rrefpix['THETA']: theta += rrefpix['THETA']*pi/180.0

    dX=(off*sin(theta)) + offshiftx
    dY=(off*cos(theta)) + offshifty
    
    # Check to see whether we are working with GEIS or FITS input
    _fname,_iextn = fileutil.parseFilename(image)

    if _fname.find('.fits') < 0:
        # Input image is NOT a FITS file, so 
        #     build a FITS name for it's copy.
        _fitsname = fileutil.buildFITSName(_fname)
    else:
        _fitsname = None
    # Create a new instance of a WCS
    if _fitsname == None:
        _new_name = image
    else:
        _new_name = _fitsname+'['+str(_iextn)+']'

    #New=wcsutil.WCSObject(_new_name,new=yes)
    New = Old.copy()
    
    # Calculate new CRVALs and CRPIXs
    New.crval1,New.crval2=R.xy2rd((dX,dY))
    New.crpix1=refpix['XREF'] + ltvoffx
    New.crpix2=refpix['YREF'] + ltvoffy
    
    # Account for subarray offset
    # Angle of chip relative to chip
    if refpix['THETA']:
       dtheta = refpix['THETA'] - rrefpix['THETA']
    else:
       dtheta = 0.0

    # Create a small vector, in reference image pixel scale
    # There is no parity effect here ???
    delXX=fx[1,1]/R_scale/3600.
    delYX=fy[1,1]/R_scale/3600.
    delXY=fx[1,0]/R_scale/3600.
    delYY=fy[1,0]/R_scale/3600.

    # Convert to radians
    rr=dtheta*pi/180.0

    # Rotate the vectors
    dXX= cos(rr)*delXX - sin(rr)*delYX
    dYX= sin(rr)*delXX + cos(rr)*delYX

    dXY= cos(rr)*delXY - sin(rr)*delYY
    dYY= sin(rr)*delXY + cos(rr)*delYY

    # Transform to sky coordinates
    a,b=R.xy2rd((dX+dXX,dY+dYX))
    c,d=R.xy2rd((dX+dXY,dY+dYY))

    # Calculate the new CDs and convert to degrees
    New.cd11=diff_angles(a,New.crval1)*cos(New.crval2*pi/180.0)
    New.cd12=diff_angles(c,New.crval1)*cos(New.crval2*pi/180.0)
    New.cd21=diff_angles(b,New.crval2)
    New.cd22=diff_angles(d,New.crval2)
    
    # Apply the velocity aberration effect if applicable
    if VA_fac != 1.0:

       # First shift the CRVALs apart
#       New.crval1 = ra_targ + VA_fac*(New.crval1 - ra_targ) 
#       New.crval2 = dec_targ + VA_fac*(New.crval2 - dec_targ) 
       # First shift the CRVALs apart
       # This is now relative to the reference chip, not the
       # target position.
       New.crval1 = R.crval1 + VA_fac*diff_angles(New.crval1, R.crval1)
       New.crval2 = R.crval2 + VA_fac*diff_angles(New.crval2, R.crval2)

       # and scale the CDs
       New.cd11 = New.cd11*VA_fac
       New.cd12 = New.cd12*VA_fac
       New.cd21 = New.cd21*VA_fac
       New.cd22 = New.cd22*VA_fac        
        
    New_cdmat = N.array([[New.cd11,New.cd12],[New.cd21,New.cd22]])

    # Store new one
    # archive=yes specifies to also write out archived WCS keywords
    # overwrite=no specifies do not overwrite any pre-existing archived keywords
        
    New.write(fitsname=_new_name,overwrite=no,quiet=quiet,archive=yes)
    if _dqname:
        _dq_iextn = _iextn.replace('sci', dqext.lower())
        _new_dqname = _dqname +'['+_dq_iextn+']'
        dqwcs = wcsutil.WCSObject(_new_dqname)
        dqwcs.write(fitsname=_new_dqname, wcs=New,overwrite=no,quiet=quiet, archive=yes)
    
    """ Convert distortion coefficients into SIP style
        values and write out to image (assumed to be FITS). 
    """  
    #First the CD matrix:
    f = refpix['PSCALE']/3600.0
    a = fx[1,1]/3600.0
    b = fx[1,0]/3600.0
    c = fy[1,1]/3600.0
    d = fy[1,0]/3600.0
    det = (a*d - b*c)*refpix['PSCALE']
    
    # Write to header
    fimg = fileutil.openImage(_new_name,mode='update')
    _new_root,_nextn = fileutil.parseFilename(_new_name)
    _new_extn = fileutil.getExtn(fimg,_nextn)
    
    
    # Transform the higher-order coefficients
    for n in range(order+1):
      for m in range(order+1):
        if n >= m and n>=2:

          # Form SIP-style keyword names
          Akey="A_%d_%d" % (m,n-m)
          Bkey="B_%d_%d" % (m,n-m)

          # Assign them values
          #Aval=string.upper("%13.9e" % (f*(d*fx[n,m]-b*fy[n,m])/det))
          #Bval=string.upper("%13.9e" % (f*(a*fy[n,m]-c*fx[n,m])/det))
          Aval= f*(d*fx[n,m]-b*fy[n,m])/det
          Bval= f*(a*fy[n,m]-c*fx[n,m])/det

          _new_extn.header.update(Akey,Aval)
          _new_extn.header.update(Bkey,Bval)

    # Update the SIP flag keywords as well
    #iraf.hedit(image,"CTYPE1","RA---TAN-SIP",verify=no,show=no)
    #iraf.hedit(image,"CTYPE2","DEC--TAN-SIP",verify=no,show=no)
    _new_extn.header.update("CTYPE1","RA---TAN-SIP")
    _new_extn.header.update("CTYPE2","DEC--TAN-SIP")

    # Finally we also need the order
    #iraf.hedit(image,"A_ORDER","%d" % order,add=yes,verify=no,show=no)
    #iraf.hedit(image,"B_ORDER","%d" % order,add=yes,verify=no,show=no)
    _new_extn.header.update("A_ORDER",order)
    _new_extn.header.update("B_ORDER",order)

    # Update header with additional keywords required for proper
    # interpretation of SIP coefficients by PyDrizzle.

    _new_extn.header.update("IDCSCALE",refpix['PSCALE'])
    _new_extn.header.update("IDCV2REF",refpix['V2REF'])
    _new_extn.header.update("IDCV3REF",refpix['V3REF'])
    _new_extn.header.update("IDCTHETA",refpix['THETA'])
    _new_extn.header.update("OCX10",fx[1][0])
    _new_extn.header.update("OCX11",fx[1][1])
    _new_extn.header.update("OCY10",fy[1][0])
    _new_extn.header.update("OCY11",fy[1][1])
    #_new_extn.header.update("TDDXOFF",rv23_corr[0][0] - v23_corr[0][0])
    #_new_extn.header.update("TDDYOFF",-(rv23_corr[1][0] - v23_corr[1][0]))
        
    # Report time-dependent coeffs, if computed
    if instrument == 'ACS' and detector == 'WFC':
        _new_extn.header.update("TDDALPHA",alpha)
        _new_extn.header.update("TDDBETA",beta)

    
    # Close image now
    fimg.close()
    del fimg
    
    
def diff_angles(a,b):
    """ Perform angle subtraction a-b taking into account
        small-angle differences across 360degree line. """
        
    diff = a - b

    if diff > 180.0:
       diff -= 360.0

    if diff < -180.0:
       diff += 360.0
    
    return diff
    
def readKeyword(hdr,keyword):

    try:
        value =  hdr[keyword]
    except KeyError:
        value = None

    # NOTE:  Need to clean up the keyword.. Occasionally the keyword value
    # goes right up to the "/" FITS delimiter, and iraf.keypar is incapable
    # of realizing this, so it incorporates "/" along with the keyword value.
    # For example, after running "pydrizzle" on the image "j8e601bkq_flt.fits",
    # the CD keywords look like this:
    #
    #   CD1_1   = 9.221627430999639E-06/ partial of first axis coordinate w.r.t. x
    #   CD1_2   = -1.0346992614799E-05 / partial of first axis coordinate w.r.t. y
    #
    # so for CD1_1, iraf.keypar returns:
    #       "9.221627430999639E-06/"
    #
    # So, the following piece of code CHECKS for this and FIXES the string,
    # very simply by removing the last character if it is a "/".
    # This fix courtesy of Anton Koekemoer, 2002.
    if type(value) is types.StringType:
        if value[-1:] == '/':
            value = value[:-1]

    return value

def get_numsci(image):
    """ Find the number of SCI extensions in the image.
        Input:
            image - name of single input image 
    """ 
    handle = fileutil.openImage(image)
    num_sci = 0    
    for extn in handle:
        if extn.header.has_key('extname'):
            if extn.header['extname'].lower() == 'sci':
                num_sci += 1
    handle.close()
    return num_sci

def shift_coeffs(cx,cy,xs,ys,norder):
    """
    Shift reference position of coefficients to new center 
    where (xs,ys) = old-reference-position - subarray/image center.
    This will support creating coeffs files for drizzle which will 
    be applied relative to the center of the image, rather than relative
    to the reference position of the chip.
    
    Derived directly from PyDrizzle V3.3d.
    """

    _cxs = N.zeros(shape=cx.shape,dtype=cx.dtype.name)
    _cys = N.zeros(shape=cy.shape,dtype=cy.dtype.name)
    _k = norder + 1

    # loop over each input coefficient
    for m in xrange(_k):
        for n in xrange(_k):
            if m >= n:
                # For this coefficient, shift by xs/ys.
                _ilist = N.array(range(_k - m)) + m
                # sum from m to k
                for i in _ilist:
                    _jlist = N.array(range( i - (m-n) - n + 1)) + n
                    # sum from n to i-(m-n)
                    for j in _jlist:
                        _cxs[m,n] = _cxs[m,n] + cx[i,j]*pydrizzle._combin(j,n)*pydrizzle._combin((i-j),(m-n))*pow(xs,(j-n))*pow(ys,((i-j)-(m-n)))
                        _cys[m,n] = _cys[m,n] + cy[i,j]*pydrizzle._combin(j,n)*pydrizzle._combin((i-j),(m-n))*pow(xs,(j-n))*pow(ys,((i-j)-(m-n)))
    _cxs[0,0] = _cxs[0,0] - xs
    _cys[0,0] = _cys[0,0] - ys
    #_cxs[0,0] = 0.
    #_cys[0,0] = 0.

    return _cxs,_cys

def getNrefchip(image,instrument='WFPC2'):
    """
    This handles the fact that WFPC2 subarray observations
    may not include chip 3 which is the default reference chip for
    full observations. Also for subarrays chip 3  may not be the third
    extension in a MEF file. It is a kludge but this whole module is
    one big kludge. ND
    """
    hdu = fileutil.openImage(image)
    if instrument == 'WFPC2':
        detectors = [img.header['DETECTOR'] for img in hdu[1:]]

    if 3 not in detectors:
        Nrefchip=detectors[0]
        Nrefext = 1
    else:
        Nrefchip = 3
        Nrefext = detectors.index(3) + 1

    hdu.close()
    return Nrefchip, Nrefext

        
def help():
    _help_str = """ makewcs - a task for updating an image header WCS to make
          it consistent with the distortion model and velocity aberration.  
    
    This task will read in a distortion model from the IDCTAB and generate 
    a new WCS matrix based on the value of ORIENTAT.  It will support subarrays
    by shifting the distortion coefficients to image reference position before
    applying them to create the new WCS, including velocity aberration. 
    Original WCS values will be moved to an O* keywords (OCD1_1,...).
    Currently, this task will only support ACS and WFPC2 observations.
    
    Syntax:
        makewcs.run(image,quiet=no)
    where 
        image   - either a single image with extension specified,
                  or a substring common to all desired image names,
                  or a wildcarded filename
                  or '@file' where file is a file containing a list of images
        quiet   - turns off ALL reporting messages: 'yes' or 'no'(default)
        restore - restore WCS for all input images to defaults if possible:
                    'yes' or 'no'(default) 
        apply_tdd - applies the time-dependent skew terms to the SIP coefficients
                    written out to the header: 'yes' or True or, 'no' or False (default).
    Usage:
        --> import makewcs
        --> makewcs.run('raw') # This will update all _raw files in directory
        --> makewcs.run('j8gl03igq_raw.fits[sci,1]')
    """
    print _help_str
