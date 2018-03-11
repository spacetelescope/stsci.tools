from __future__ import absolute_import, division, print_function # confidence high

import copy, os

from astropy.io import fits
import numpy as N
from math import *

from . import fileutil

# Convenience definitions...
yes = True
no = False

DEGTORAD = fileutil.DEGTORAD
RADTODEG = fileutil.RADTODEG
DIVMOD = fileutil.DIVMOD
DEFAULT_PREFIX = 'O'

#
# History
#
# 30-Mar-2002 WJH: Added separate XYtoSky interface function.
# 19-Apr-2002 WJH: Corrected 'ddtohms' for error in converting neg. dec.
# 20-Sept-2002 WJH: replaced all references to 'keypar' with calls to 'hselect'
#                   This avoids any parameter writes in the pipeline.
# 03-Dec-2002 WJH: Added 'new' parameter to WCSObject to make creating an
#                   object from scratch unambiguous and free from filename
#                   collisions with user files.
# 23-Apr-2003 WJH: Enhanced to search entire file for header with WCS keywords
#                   if no extension was specified with filename.
# 6-Oct-2003 WJH:  Modified to use the 'fileutil.getHeader' function or
#                   accept a PyFITS/readgeis header object.  Removed
#                   any explicit check on whether the image was FITS or
#                   not.
# 5-Feb-2004 WJH:  Added 'recenter' method to rigorously shift the WCS from
#                   an off-center reference pixel position to the frame center
#
# 24-Jan-2005 WJH: Added methods and attributes for working with archived
#                   versions of WCS keywords.  Archived keywords will be
#                   treated as 'read-only' if they already exist, unless
#                   specifically overwritten.
#
# 30-Mar-2005 WJH: 'read_archive' needed to be modified to use existing prefix
#                   found in header, if one exists, for computing archive pscale.
#
# 20-Jun-2005 WJH: Support for constant-value arrays using NPIX/PIXVALUE added to
#                   class.  The output reference WCS now creates a constant-value
#                   array for the extension as well in order to be FITS compliant.
#                   WCS keywords now get written out in a set order to be FITS compliant.
#                   New method, get_orient, added to always allow access to computed
#                   orientation regardless of orientat keyword value.
#
# 29-June-2005 WJH: Multiple WCS extensions are not created when running
#                   'createReferenceWCS'.
#




__version__ = '1.2.3 (11-Feb-2011)'

def help():
    print('wcsutil Version '+str(__version__)+':\n')
    print(WCSObject.__doc__)
#################
#
#
#               Coordinate Transformation Functions
#
#
#################


def ddtohms(xsky,ysky,verbose=no):

    """ Convert sky position(s) from decimal degrees to HMS format."""

    xskyh = xsky /15.
    xskym = (xskyh - N.floor(xskyh)) * 60.
    xskys = (xskym - N.floor(xskym)) * 60.

    yskym = (N.abs(ysky) - N.floor(N.abs(ysky))) * 60.
    yskys = (yskym - N.floor(yskym)) * 60.

    if isinstance(xskyh,N.ndarray):
        rah,dech = [],[]
        for i in range(len(xskyh)):
            rastr = repr(int(xskyh[i]))+':'+repr(int(xskym[i]))+':'+repr(xskys[i])
            decstr = repr(int(ysky[i]))+':'+repr(int(yskym[i]))+':'+repr(yskys[i])
            rah.append(rastr)
            dech.append(decstr)
            if verbose:
                print('RA = ',rastr,', Dec = ',decstr)
    else:
        rastr = repr(int(xskyh))+':'+repr(int(xskym))+':'+repr(xskys)
        decstr = repr(int(ysky))+':'+repr(int(yskym))+':'+repr(yskys)
        rah = rastr
        dech = decstr
        if verbose:
            print('RA = ',rastr,', Dec = ',decstr)

    return rah,dech


def troll(roll, dec, v2, v3):
    """ Computes the roll angle at the target position based on::

            the roll angle at the V1 axis(roll),
            the dec of the target(dec), and
            the V2/V3 position of the aperture (v2,v3) in arcseconds.

        Based on the algorithm provided by Colin Cox that is used in
        Generic Conversion at STScI.
    """
    # Convert all angles to radians
    _roll = DEGTORAD(roll)
    _dec = DEGTORAD(dec)
    _v2 = DEGTORAD(v2 / 3600.)
    _v3 = DEGTORAD(v3 / 3600.)

    # compute components
    sin_rho = sqrt((pow(sin(_v2),2)+pow(sin(_v3),2)) - (pow(sin(_v2),2)*pow(sin(_v3),2)))
    rho = asin(sin_rho)
    beta = asin(sin(_v3)/sin_rho)
    if _v2 < 0: beta = pi - beta
    gamma = asin(sin(_v2)/sin_rho)
    if _v3 < 0: gamma = pi - gamma
    A = pi/2. + _roll - beta
    B = atan2( sin(A)*cos(_dec), (sin(_dec)*sin_rho - cos(_dec)*cos(rho)*cos(A)))

    # compute final value
    troll = RADTODEG(pi - (gamma+B))

    return troll

#################
#
#
#               Coordinate System Class
#
#
#################

class WCSObject:
    """ This class should contain the WCS information from the
        input exposure's header and provide conversion functionality
        from pixels to RA/Dec and back.

        The basic syntax for using this object is::

            >>> wcs = wcsutil.WCSObject(
            ...     rootname, header=None, shape=None,
            ...     pa_key='PA_V3', new=no, prefix=None)  # doctest: +SKIP

        This will create a WCSObject which provides basic WCS functions.

        Parameters
        ==========
        rootname: string
            filename in a format supported by IRAF, specifically::

                filename.hhh[group] -or-
                filename.fits[ext] -or-
                filename.fits[extname,extver]

        header: object
            PyFITS header object from which WCS keywords can be read
        shape:    tuple
            tuple giving (nx,ny,pscale)
        pa_key: string
            name of keyword to read in telescopy orientation
        new: boolean
            specify a new object rather than creating one by
            reading in keywords from an existing image
        prefix: string
            string to use as prefix for creating archived versions
            of WCS keywords, if such keywords do not already exist

        Notes
        ======
        Setting 'new=yes' will create a WCSObject from scratch
        regardless of any input rootname.  This avoids unexpected
        filename collisions.

        Methods
        =======
        print_archive(format=True)
            print out archive keyword values
        get_archivekw(keyword)
            return archived value for WCS keyword
        set_pscale()
            set pscale attribute for object
        compute_pscale(cd11,cd21)
            compute pscale value
        get_orient()
            return orient computed from CD matrix
        updateWCS(pixel_scale=None,orient=None,refpos=None,refval=None,size=None)
            reset entire WCS based on given values
        xy2rd(pos)
            compute RA/Dec position for given (x,y) tuple
        rd2xy(skypos,hour=no)
            compute X,Y position for given (RA,Dec)
        rotateCD(orient)
            rotate CD matrix to new orientation given by 'orient'
        recenter()
            Reset reference position to X,Y center of frame
        write(fitsname=None,archive=True,overwrite=False,quiet=True)
            write out values of WCS to specified file
        restore()
            reset WCS keyword values to those from archived values
        read_archive(header,prepend=None)
            read any archive WCS keywords from PyFITS header
        archive(prepend=None,overwrite=no,quiet=yes)
            create archived copies of WCS keywords.
        write_archive(fitsname=None,overwrite=no,quiet=yes)
            write out the archived WCS values to the file
        restoreWCS(prepend=None)
            resets WCS values in file to original values
        createReferenceWCS(refname,overwrite=yes)
            write out values of WCS keywords to NEW FITS
            file without any image data
        copy(deep=True)
            create a copy of the WCSObject.
        help()
            prints out this help message

    """
    def __init__(self, rootname,header=None,shape=None,pa_key='PA_V3',new=no,prefix=None):
        # Initialize wcs dictionaries:
        #   wcsdef - default values for new images
        #   wcstrans - translation table from header keyword to attribute
        #   wcskeys  - keywords in the order they should appear in the header
        self.wcsdef = {'crpix1':0.0,'crpix2':0.0,'crval1':0.0,'crval2':0.0,'cd11':1.0,
                'cd12':1.0,'cd21':1.0,'cd22':1.0,'orient':1.0,'naxis1':0,'naxis2':0,'pscale':1.0,
                'postarg1':0.0,'postarg2':0.0,'pa_obs':0.0,
                'ctype1':'RA---TAN','ctype2':'DEC--TAN'}
        self.wcstrans = {'CRPIX1':'crpix1','CRPIX2':'crpix2','CRVAL1':'crval1','CRVAL2':'crval2',
            'CD1_1':'cd11','CD1_2':'cd12','CD2_1':'cd21','CD2_2':'cd22',
            'ORIENTAT':'orient', 'NAXIS1':'naxis1','NAXIS2':'naxis2',
            'pixel scale':'pscale','CTYPE1':'ctype1','CTYPE2':'ctype2'}
        self.wcskeys = ['NAXIS1','NAXIS2','CRPIX1','CRPIX2',
                        'CRVAL1','CRVAL2','CTYPE1','CTYPE2',
                        'CD1_1','CD1_2','CD2_1','CD2_2',
                        'ORIENTAT']
        # Now, read in the CRPIX1/2, CRVAL1/2, CD1/2_1/2 keywords.
        # Simplistic, but easy to understand what you are asking for.

        _exists = yes
        if rootname is not None:
            self.rootname = rootname
        else:
            self.rootname = 'New'
            new = yes
            _exists = no

        # Initialize attribute for GEIS image name, just in case...
        self.geisname = None

        # Look for extension specification in rootname
        _indx = _section = self.rootname.find('[')
        # If none are found, use entire rootname
        if _indx < 0:
            _indx = len(self.rootname)

        # Determine whether we are working with a new image or not.
        _dir,_rootname = os.path.split(fileutil.osfn(self.rootname[:_indx]))
        if _dir:
            _filename = _dir+os.sep+_rootname
        else:
            _filename = _rootname
        self.filename = _filename

        if not new:
            _exists = fileutil.checkFileExists(_rootname,directory=_dir)

        else:
            _exists = no

        # If no header has been provided, get the PRIMARY and the
        # specified extension header... This call uses the fully
        # expanded version of the filename, plus any sections listed by
        # by the user in the original rootname.
        if not header and _exists:
            _hdr_file = _filename+self.rootname[_indx:]
            _header = fileutil.getHeader(_hdr_file)
        else:
            # Otherwise, simply use the header already read into memory
            # for this exposure/chip.
            _header = header

        if _exists or header:
            # Initialize WCS object with keyword values...
            try:
                _dkey = 'orientat'
                if 'orientat' in _header:
                    self.orient = _header['orientat']
                else:
                    self.orient = None

                if _header['naxis'] == 0 and 'pixvalue' in _header:

                # Check for existence of NPIX/PIXVALUE keywords
                # which represent a constant array extension
                    _dkey = 'npix1'
                    self.naxis1 = _header['npix1']
                    _dkey = 'npix2'
                    self.naxis2 = _header['npix2']
                    _dkey = 'pixvalue'
                    self.pixvalue = _header['pixvalue']
                else:
                    _dkey = 'naxis1'
                    self.naxis1 = _header['naxis1']
                    _dkey = 'naxis2'
                    self.naxis2 = _header['naxis2']
                    self.pixvalue = None

                self.npix1 = self.naxis1
                self.npix2 = self.naxis2

                for key in self.wcstrans.keys():
                    _dkey = self.wcstrans[key]
                    if _dkey not in ['pscale','orient','naxis1','naxis2']:
                        self.__dict__[_dkey] = _header[key]

                self.new = no
            except:
                print('Could not find WCS keyword: ',_dkey)
                raise IOError('Image %s does not contain all required WCS keywords!' % self.rootname)

            # Now, try to read in POSTARG keyword values, if they exist...
            try:
                self.postarg1 = _header['postarg1']
                self.postarg2 = _header['postarg2']
            except:
                # If these keywords, don't exist set defaults...
                self.postarg1 = 0.0
                self.postarg2 = 0.0
            try:
                self.pa_obs = _header[pa_key]
            except:
                # If no such keyword exists, use orientat value later
                self.pa_obs = None

        else:
            # or set default values...
            self.new = yes
            for key in self.wcsdef.keys():
                self.__dict__[key] = self.wcsdef[key]

            if shape is not None:
                # ... and update with user values.
                self.naxis1 = int(shape[0])
                self.naxis2 = int(shape[1])
                self.pscale = float(shape[2])

        # Make sure reported 'orient' is consistent with CD matrix
        # while preserving the original 'ORIENTAT' keyword value
        self.orientat = self.orient

        self.orient = RADTODEG(N.arctan2(self.cd12,self.cd22))

        # If no keyword provided pa_obs value (PA_V3), then default to
        # image orientation from CD matrix.
        if self.pa_obs is None:
            self.pa_obs = self.orient

        if shape is None:
            self.set_pscale()
            #self.pscale = N.sqrt(N.power(self.cd11,2)+N.power(self.cd21,2)) * 3600.
            # Use Jacobian determination of pixel scale instead of X or Y separately...
            #self.pscale = N.sqrt(abs(self.cd11*self.cd22 - self.cd12*self.cd21))*3600.

        # Establish an attribute for the linearized orient
        # defined as the orientation of the CD after applying the default
        # distortion correction.
        self._orient_lin = 0.

        # attribute to define format for printing WCS
        self.__format__=yes

        # Keep track of the keyword names used as the backup keywords
        # for the original WCS values
        #    backup - dict relating active keywords with backup keywords
        #    prepend - string prepended to active keywords to create backup keywords
        #    orig_wcs - dict containing orig keywords and values
        self.backup = {}
        self.revert = {}
        self.prepend = None
        self.orig_wcs = {}
        # Read in any archived WCS keyword values, if they exist
        self.read_archive(_header,prepend=prefix)

    # You never know when you want to print out the WCS keywords...
    def __str__(self):
        block = 'WCS Keywords for ' + self.rootname + ': \n'
        if not self.__format__:
            for key in self.wcstrans.keys():
                _dkey = self.wcstrans[key]
                strn = key.upper() + " = " + repr(self.__dict__[_dkey]) + '\n'
                block += strn
            block += 'PA_V3: '+repr(self.pa_obs)+'\n'

        else:
            block += 'CD_11  CD_12: '+repr(self.cd11)+'  '+repr(self.cd12) +'\n'
            block += 'CD_21  CD_22: '+repr(self.cd21)+'  '+repr(self.cd22) +'\n'
            block += 'CRVAL       : '+repr(self.crval1)+'  '+repr(self.crval2) + '\n'
            block += 'CRPIX       : '+repr(self.crpix1)+'  '+repr(self.crpix2) + '\n'
            block += 'NAXIS       : '+repr(int(self.naxis1))+'  '+repr(int(self.naxis2)) + '\n'
            block += 'Plate Scale : '+repr(self.pscale)+'\n'
            block += 'ORIENTAT    : '+repr(self.orient)+'\n'
            block += 'CTYPE       : '+repr(self.ctype1)+'  '+repr(self.ctype2)+'\n'
            block += 'PA Telescope: '+repr(self.pa_obs)+'\n'

        return block

    def __repr__(self):
        return repr(self.__dict__)

    def print_archive(self,format=True):
        """ Prints out archived WCS keywords."""
        if len(list(self.orig_wcs.keys())) > 0:
            block  = 'Original WCS keywords for ' + self.rootname+ '\n'
            block += '    backed up on '+repr(self.orig_wcs['WCSCDATE'])+'\n'
            if not format:
                for key in self.wcstrans.keys():
                    block += key.upper() + " = " + repr(self.get_archivekw(key)) + '\n'
                block = 'PA_V3: '+repr(self.pa_obs)+'\n'

            else:
                block += 'CD_11  CD_12: '+repr(self.get_archivekw('CD1_1'))+'  '+repr(self.get_archivekw('CD1_2')) +'\n'
                block += 'CD_21  CD_22: '+repr(self.get_archivekw('CD2_1'))+'  '+repr(self.get_archivekw('CD2_2')) +'\n'
                block += 'CRVAL       : '+repr(self.get_archivekw('CRVAL1'))+'  '+repr(self.get_archivekw('CRVAL2')) + '\n'
                block += 'CRPIX       : '+repr(self.get_archivekw('CRPIX1'))+'  '+repr(self.get_archivekw('CRPIX2')) + '\n'
                block += 'NAXIS       : '+repr(int(self.get_archivekw('NAXIS1')))+'  '+repr(int(self.get_archivekw('NAXIS2'))) + '\n'
                block += 'Plate Scale : '+repr(self.get_archivekw('pixel scale'))+'\n'
                block += 'ORIENTAT    : '+repr(self.get_archivekw('ORIENTAT'))+'\n'

            print(block)

    def get_archivekw(self,keyword):
        """ Return an archived/backup value for the keyword. """
        return self.orig_wcs[self.backup[keyword]]

    def set_pscale(self):
        """ Compute the pixel scale based on active WCS values. """
        if self.new:
            self.pscale = 1.0
        else:
            self.pscale = self.compute_pscale(self.cd11,self.cd21)

    def compute_pscale(self,cd11,cd21):
        """ Compute the pixel scale based on active WCS values. """
        return N.sqrt(N.power(cd11,2)+N.power(cd21,2)) * 3600.

    def get_orient(self):
        """ Return the computed orientation based on CD matrix. """
        return RADTODEG(N.arctan2(self.cd12,self.cd22))

    def set_orient(self):
        """ Return the computed orientation based on CD matrix. """
        self.orient = RADTODEG(N.arctan2(self.cd12,self.cd22))

    def update(self):
        """ Update computed values of WCS based on current CD matrix."""
        self.set_pscale()
        self.set_orient()

    def updateWCS(self, pixel_scale=None, orient=None,refpos=None,refval=None,size=None):
        """
        Create a new CD Matrix from the absolute pixel scale
        and reference image orientation.
        """
        # Set up parameters necessary for updating WCS
        # Check to see if new value is provided,
        # If not, fall back on old value as the default

        _updateCD = no
        if orient is not None and orient != self.orient:
            pa = DEGTORAD(orient)
            self.orient = orient
            self._orient_lin = orient
            _updateCD = yes
        else:
            # In case only pixel_scale was specified
            pa = DEGTORAD(self.orient)

        if pixel_scale is not None and pixel_scale != self.pscale:
            _ratio = pixel_scale / self.pscale
            self.pscale = pixel_scale
            _updateCD = yes
        else:
            # In case, only orient was specified
            pixel_scale = self.pscale
            _ratio = None

        # If a new plate scale was given,
        # the default size should be revised accordingly
        # along with the default reference pixel position.
        # Added 31 Mar 03, WJH.
        if _ratio is not None:
            self.naxis1 /= _ratio
            self.naxis2 /= _ratio
            self.crpix1 = self.naxis1/2.
            self.crpix2 = self.naxis2/2.

        # However, if the user provides a given size,
        # set it to use that no matter what.
        if size is not None:
            self.naxis1 = size[0]
            self.naxis2 = size[1]

        # Insure that naxis1,2 always return as integer values.
        self.naxis1 = int(self.naxis1)
        self.naxis2 = int(self.naxis2)

        if refpos is not None:
            self.crpix1 = refpos[0]
            self.crpix2 = refpos[1]
        if self.crpix1 is None:
            self.crpix1 = self.naxis1/2.
            self.crpix2 = self.naxis2/2.

        if refval is not None:
            self.crval1 = refval[0]
            self.crval2 = refval[1]

        # Reset WCS info now...
        if _updateCD:
            # Only update this should the pscale or orientation change...
            pscale = pixel_scale / 3600.

            self.cd11 = -pscale * N.cos(pa)
            self.cd12 = pscale * N.sin(pa)
            self.cd21 = self.cd12
            self.cd22 = -self.cd11

        # Now make sure that all derived values are really up-to-date based
        # on these changes
        self.update()

    def scale_WCS(self,pixel_scale,retain=True):
        ''' Scale the WCS to a new pixel_scale. The 'retain' parameter
        [default value: True] controls whether or not to retain the original
        distortion solution in the CD matrix.
        '''
        _ratio = pixel_scale / self.pscale

        # Correct the size of the image and CRPIX values for scaled WCS
        self.naxis1 /= _ratio
        self.naxis2 /= _ratio
        self.crpix1 = self.naxis1/2.
        self.crpix2 = self.naxis2/2.

        if retain:
            # Correct the WCS while retaining original distortion information
            self.cd11 *= _ratio
            self.cd12 *= _ratio
            self.cd21 *= _ratio
            self.cd22 *= _ratio
        else:
            pscale = pixel_scale / 3600.
            self.cd11 = -pscale * N.cos(pa)
            self.cd12 = pscale * N.sin(pa)
            self.cd21 = self.cd12
            self.cd22 = -self.cd11

        # Now make sure that all derived values are really up-to-date based
        # on these changes
        self.update()

    def xy2rd(self,pos):
        """
        This method would apply the WCS keywords to a position to
        generate a new sky position.

        The algorithm comes directly from 'imgtools.xy2rd'

        translate (x,y) to (ra, dec)
        """
        if self.ctype1.find('TAN') < 0 or self.ctype2.find('TAN') < 0:
            print('XY2RD only supported for TAN projections.')
            raise TypeError

        if isinstance(pos,N.ndarray):
            # If we are working with an array of positions,
            # point to just X and Y values
            posx = pos[:,0]
            posy = pos[:,1]
        else:
            # Otherwise, we are working with a single X,Y tuple
            posx = pos[0]
            posy = pos[1]

        xi = self.cd11 * (posx - self.crpix1) + self.cd12 * (posy - self.crpix2)
        eta = self.cd21 * (posx - self.crpix1) + self.cd22 * (posy - self.crpix2)

        xi = DEGTORAD(xi)
        eta = DEGTORAD(eta)
        ra0 = DEGTORAD(self.crval1)
        dec0 = DEGTORAD(self.crval2)

        ra = N.arctan((xi / (N.cos(dec0)-eta*N.sin(dec0)))) + ra0
        dec = N.arctan( ((eta*N.cos(dec0)+N.sin(dec0)) /
                (N.sqrt((N.cos(dec0)-eta*N.sin(dec0))**2 + xi**2))) )

        ra = RADTODEG(ra)
        dec = RADTODEG(dec)
        ra = DIVMOD(ra, 360.)

        # Otherwise, just return the RA,Dec tuple.
        return ra,dec


    def rd2xy(self,skypos,hour=no):
        """
        This method would use the WCS keywords to compute the XY position
        from a given RA/Dec tuple (in deg).

        NOTE: Investigate how to let this function accept arrays as well
        as single positions. WJH 27Mar03

        """
        if self.ctype1.find('TAN') < 0 or self.ctype2.find('TAN') < 0:
            print('RD2XY only supported for TAN projections.')
            raise TypeError

        det = self.cd11*self.cd22 - self.cd12*self.cd21

        if det == 0.0:
            raise ArithmeticError("singular CD matrix!")

        cdinv11 = self.cd22 / det
        cdinv12 = -self.cd12 / det
        cdinv21 = -self.cd21 / det
        cdinv22 = self.cd11 / det

        # translate (ra, dec) to (x, y)

        ra0 = DEGTORAD(self.crval1)
        dec0 = DEGTORAD(self.crval2)
        if hour:
            skypos[0] = skypos[0] * 15.
        ra = DEGTORAD(skypos[0])
        dec = DEGTORAD(skypos[1])

        bottom = float(N.sin(dec)*N.sin(dec0) + N.cos(dec)*N.cos(dec0)*N.cos(ra-ra0))
        if bottom == 0.0:
            raise ArithmeticError("Unreasonable RA/Dec range!")

        xi = RADTODEG((N.cos(dec) * N.sin(ra-ra0) / bottom))
        eta = RADTODEG((N.sin(dec)*N.cos(dec0) - N.cos(dec)*N.sin(dec0)*N.cos(ra-ra0)) / bottom)

        x = cdinv11 * xi + cdinv12 * eta + self.crpix1
        y = cdinv21 * xi + cdinv22 * eta + self.crpix2

        return x,y

    def rotateCD(self,orient):
        """ Rotates WCS CD matrix to new orientation given by 'orient'
        """
        # Determine where member CRVAL position falls in ref frame
        # Find out whether this needs to be rotated to align with
        # reference frame.

        _delta = self.get_orient() - orient
        if _delta == 0.:
            return

        # Start by building the rotation matrix...
        _rot = fileutil.buildRotMatrix(_delta)
        # ...then, rotate the CD matrix and update the values...
        _cd = N.array([[self.cd11,self.cd12],[self.cd21,self.cd22]],dtype=N.float64)
        _cdrot = N.dot(_cd,_rot)
        self.cd11 = _cdrot[0][0]
        self.cd12 = _cdrot[0][1]
        self.cd21 = _cdrot[1][0]
        self.cd22 = _cdrot[1][1]
        self.orient = orient

    def recenter(self):
        """
        Reset the reference position values to correspond to the center
        of the reference frame.
        Algorithm used here developed by Colin Cox - 27-Jan-2004.
        """
        if self.ctype1.find('TAN') < 0 or self.ctype2.find('TAN') < 0:
            print('WCS.recenter() only supported for TAN projections.')
            raise TypeError

        # Check to see if WCS is already centered...
        if self.crpix1 == self.naxis1/2. and self.crpix2 == self.naxis2/2.:
            # No recentering necessary... return without changing WCS.
            return

        # This offset aligns the WCS to the center of the pixel, in accordance
        # with the 'align=center' option used by 'drizzle'.
        #_drz_off = -0.5
        _drz_off = 0.
        _cen = (self.naxis1/2.+ _drz_off,self.naxis2/2. + _drz_off)

        # Compute the RA and Dec for center pixel
        _cenrd = self.xy2rd(_cen)
        _cd = N.array([[self.cd11,self.cd12],[self.cd21,self.cd22]],dtype=N.float64)
        _ra0 = DEGTORAD(self.crval1)
        _dec0 = DEGTORAD(self.crval2)
        _ra = DEGTORAD(_cenrd[0])
        _dec = DEGTORAD(_cenrd[1])

        # Set up some terms for use in the final result
        _dx = self.naxis1/2. - self.crpix1
        _dy = self.naxis2/2. - self.crpix2

        _dE,_dN = DEGTORAD(N.dot(_cd,(_dx,_dy)))
        _dE_dN = 1 + N.power(_dE,2) + N.power(_dN,2)
        _cosdec = N.cos(_dec)
        _sindec = N.sin(_dec)
        _cosdec0 = N.cos(_dec0)
        _sindec0 = N.sin(_dec0)

        _n1 = N.power(_cosdec,2) + _dE*_dE + _dN*_dN*N.power(_sindec,2)
        _dra_dE = (_cosdec0 - _dN*_sindec0)/_n1
        _dra_dN = _dE*_sindec0 /_n1

        _ddec_dE = -_dE*N.tan(_dec) / _dE_dN
        _ddec_dN = (1/_cosdec) * ((_cosdec0 / N.sqrt(_dE_dN)) - (_dN*N.sin(_dec) / _dE_dN))

        # Compute new CD matrix values now...
        _cd11n = _cosdec * (self.cd11*_dra_dE + self.cd21 * _dra_dN)
        _cd12n = _cosdec * (self.cd12*_dra_dE + self.cd22 * _dra_dN)
        _cd21n = self.cd11 * _ddec_dE + self.cd21 * _ddec_dN
        _cd22n = self.cd12 * _ddec_dE + self.cd22 * _ddec_dN

        _new_orient = RADTODEG(N.arctan2(_cd12n,_cd22n))
        #_new_pscale = N.sqrt(N.power(_cd11n,2)+N.power(_cd21n,2)) * 3600.

        # Update the values now...
        self.crpix1 = _cen[0]
        self.crpix2 = _cen[1]
        self.crval1 = RADTODEG(_ra)
        self.crval2 = RADTODEG(_dec)

        # Keep the same plate scale, only change the orientation
        self.rotateCD(_new_orient)

        # These would update the CD matrix with the new rotation
        # ALONG with the new plate scale which we do not want.
        self.cd11 = _cd11n
        self.cd12 = _cd12n
        self.cd21 = _cd21n
        self.cd22 = _cd22n
        #self.pscale = _new_pscale

        self.update()

    def write(self,fitsname=None,wcs=None,archive=True,overwrite=False,quiet=True):
        """
        Write out the values of the WCS keywords to the
        specified image.

        If it is a GEIS image and 'fitsname' has been provided,
        it will automatically make a multi-extension
        FITS copy of the GEIS and update that file. Otherwise, it
        throw an Exception if the user attempts to directly update
        a GEIS image header.

        If archive=True, also write out archived WCS keyword values to file.
        If overwrite=True, replace archived WCS values in file with new values.

        If a WCSObject is passed through the 'wcs' keyword, then the WCS keywords
        of this object are copied to the header of the image to be updated. A use case
        fo rthis is updating the WCS of a WFPC2 data quality (_c1h.fits) file
        in order to be in sync with the science (_c0h.fits) file.

        """
        ## Start by making sure all derived values are in sync with CD matrix
        self.update()

        image = self.rootname
        _fitsname = fitsname

        if image.find('.fits') < 0 and _fitsname is not None:
            # A non-FITS image was provided, and openImage made a copy
            # Update attributes to point to new copy instead
            self.geisname = image
            image = self.rootname = _fitsname

        # Open image as writable FITS object
        fimg = fileutil.openImage(image, mode='update', fitsname=_fitsname)

        _root,_iextn = fileutil.parseFilename(image)
        _extn = fileutil.getExtn(fimg,_iextn)

        # Write out values to header...
        if wcs:
            _wcsobj = wcs
        else:
            _wcsobj = self

        for key in _wcsobj.wcstrans.keys():
            _dkey = _wcsobj.wcstrans[key]
            if _dkey != 'pscale':
                _extn.header[key] = _wcsobj.__dict__[_dkey]

        # Close the file
        fimg.close()
        del fimg
        if archive:
            self.write_archive(fitsname=fitsname,overwrite=overwrite,quiet=quiet)

    def restore(self):
        """ Reset the active WCS keywords to values stored in the
            backup keywords.
        """
        # If there are no backup keys, do nothing...
        if len(list(self.backup.keys())) == 0:
            return
        for key in self.backup.keys():
            if key != 'WCSCDATE':
                self.__dict__[self.wcstrans[key]] = self.orig_wcs[self.backup[key]]

        self.update()

    def archive(self,prepend=None,overwrite=no,quiet=yes):
        """ Create backup copies of the WCS keywords with the given prepended
            string.
            If backup keywords are already present, only update them if
            'overwrite' is set to 'yes', otherwise, do warn the user and do nothing.
            Set the WCSDATE at this time as well.
        """
        # Verify that existing backup values are not overwritten accidentally.
        if len(list(self.backup.keys())) > 0 and overwrite == no:
            if not quiet:
                print('WARNING: Backup WCS keywords already exist! No backup made.')
                print('         The values can only be overridden if overwrite=yes.')
            return

        # Establish what prepend string to use...
        if prepend is None:
            if self.prepend is not None:
                _prefix = self.prepend
            else:
                _prefix = DEFAULT_PREFIX
        else:
            _prefix = prepend

        # Update backup and orig_wcs dictionaries
        # We have archive keywords and a defined prefix
        # Go through and append them to self.backup
        self.prepend = _prefix
        for key in self.wcstrans.keys():
            if key != 'pixel scale':
                _archive_key = self._buildNewKeyname(key,_prefix)
            else:
                _archive_key = self.prepend.lower()+'pscale'
#            if key != 'pixel scale':
            self.orig_wcs[_archive_key] = self.__dict__[self.wcstrans[key]]
            self.backup[key] = _archive_key
            self.revert[_archive_key] = key

        # Setup keyword to record when these keywords were backed up.
        self.orig_wcs['WCSCDATE']= fileutil.getLTime()
        self.backup['WCSCDATE'] = 'WCSCDATE'
        self.revert['WCSCDATE'] = 'WCSCDATE'

    def read_archive(self,header,prepend=None):
        """ Extract a copy of WCS keywords from an open file header,
            if they have already been created and remember the prefix
            used for those keywords. Otherwise, setup the current WCS
            keywords as the archive values.
        """
        # Start by looking for the any backup WCS keywords to
        # determine whether archived values are present and to set
        # the prefix used.
        _prefix = None
        _archive = False
        if header is not None:
            for kw in header.items():
                if kw[0][1:] in self.wcstrans.keys():
                    _prefix = kw[0][0]
                    _archive = True
                    break

        if not _archive:
            self.archive(prepend=prepend)
            return

        # We have archive keywords and a defined prefix
        # Go through and append them to self.backup
        if _prefix is not None:
            self.prepend = _prefix
        else:
            self.prepend = DEFAULT_PREFIX

        for key in self.wcstrans.keys():
            _archive_key = self._buildNewKeyname(key,_prefix)
            if key!= 'pixel scale':
                if _archive_key in header:
                    self.orig_wcs[_archive_key] = header[_archive_key]
                else:
                    self.orig_wcs[_archive_key] = header[key]
                self.backup[key] = _archive_key
                self.revert[_archive_key] = key

        # Establish plate scale value
        _cd11str = self.prepend+'CD1_1'
        _cd21str = self.prepend+'CD2_1'
        pscale = self.compute_pscale(self.orig_wcs[_cd11str],self.orig_wcs[_cd21str])
        _archive_key = self.prepend.lower()+'pscale'
        self.orig_wcs[_archive_key] = pscale
        self.backup['pixel scale'] = _archive_key
        self.revert[_archive_key] = 'pixel scale'

        # Setup keyword to record when these keywords were backed up.
        if 'WCSCDATE' in header:
            self.orig_wcs['WCSCDATE'] = header['WCSCDATE']
        else:
            self.orig_wcs['WCSCDATE'] = fileutil.getLTime()
        self.backup['WCSCDATE'] = 'WCSCDATE'
        self.revert['WCSCDATE'] = 'WCSCDATE'

    def write_archive(self,fitsname=None,overwrite=no,quiet=yes):
        """ Saves a copy of the WCS keywords from the image header
            as new keywords with the user-supplied 'prepend'
            character(s) prepended to the old keyword names.

            If the file is a GEIS image and 'fitsname' is not None, create
            a FITS copy and update that version; otherwise, raise
            an Exception and do not update anything.

        """
        _fitsname = fitsname

        # Open image in update mode
        #    Copying of GEIS images handled by 'openImage'.
        fimg = fileutil.openImage(self.rootname,mode='update',fitsname=_fitsname)
        if self.rootname.find('.fits') < 0 and _fitsname is not None:
            # A non-FITS image was provided, and openImage made a copy
            # Update attributes to point to new copy instead
            self.geisname = self.rootname
            self.rootname = _fitsname

        # extract the extension ID being updated
        _root,_iextn = fileutil.parseFilename(self.rootname)
        _extn = fileutil.getExtn(fimg,_iextn)
        if not quiet:
            print('Updating archive WCS keywords for ',_fitsname)

        # Write out values to header...
        for key in self.orig_wcs.keys():
            _comment = None
            _dkey = self.revert[key]

            # Verify that archive keywords will not be overwritten,
            # unless overwrite=yes.
            _old_key = key in _extn.header
            if  _old_key == True and overwrite == no:
                if not quiet:
                    print('WCS keyword',key,' already exists! Not overwriting.')
                continue

            # No archive keywords exist yet in file, or overwrite=yes...
            # Extract the value for the original keyword
            if _dkey in _extn.header:

                # Extract any comment string for the keyword as well
                _indx_key = _extn.header.index(_dkey)
                _full_key = _extn.header.cards[_indx_key]
                if not quiet:
                    print('updating ',key,' with value of: ',self.orig_wcs[key])
                _extn.header[key] = (self.orig_wcs[key], _full_key.comment)

        key = 'WCSCDATE'
        if key not in _extn.header:
            # Print out history keywords to record when these keywords
            # were backed up.
            _extn.header[key] = (self.orig_wcs[key], "Time WCS keywords were copied.")

        # Close the now updated image
        fimg.close()
        del fimg

    def restoreWCS(self,prepend=None):
        """ Resets the WCS values to the original values stored in
            the backup keywords recorded in self.backup.
        """
        # Open header for image
        image = self.rootname

        if prepend: _prepend = prepend
        elif self.prepend: _prepend = self.prepend
        else: _prepend = None

        # Open image as writable FITS object
        fimg = fileutil.openImage(image, mode='update')
        # extract the extension ID being updated
        _root,_iextn = fileutil.parseFilename(self.rootname)
        _extn = fileutil.getExtn(fimg,_iextn)

        if len(self.backup) > 0:
            # If it knows about the backup keywords already,
            # use this to restore the original values to the original keywords
            for newkey in self.revert.keys():
                if newkey != 'opscale':
                    _orig_key = self.revert[newkey]
                    _extn.header[_orig_key] = _extn.header[newkey]
        elif _prepend:
            for key in self.wcstrans.keys():
                # Get new keyword name based on old keyname
                #    and prepend string
                if key != 'pixel scale':
                    _okey = self._buildNewKeyname(key,_prepend)

                    if _okey in _extn.header:
                        _extn.header[key] = _extn.header[_okey]
                    else:
                        print('No original WCS values found. Exiting...')
                        break
        else:
            print('No original WCS values found. Exiting...')

        fimg.close()
        del fimg

    def createReferenceWCS(self,refname,overwrite=yes):
        """ Write out the values of the WCS keywords to the NEW
            specified image 'fitsname'.

        """
        hdu = self.createWcsHDU()
        # If refname already exists, delete it to make way for new file
        if os.path.exists(refname):
            if overwrite==yes:
                # Remove previous version and re-create with new header
                os.remove(refname)
                hdu.writeto(refname)
            else:
                # Append header to existing file
                wcs_append = True
                oldhdu = fits.open(refname, mode='append')
                for e in oldhdu:
                    if 'extname' in e.header and e.header['extname'] == 'WCS':
                        wcs_append = False
                if wcs_append == True:
                    oldhdu.append(hdu)
                oldhdu.close()
                del oldhdu
        else:
            # No previous file, so generate new one from scratch
            hdu.writeto(refname)

        # Clean up
        del hdu

    def createWcsHDU(self):
        """ Generate a WCS header object that can be used to
            populate a reference WCS HDU.
        """
        hdu = fits.ImageHDU()
        hdu.header['EXTNAME'] = 'WCS'
        hdu.header['EXTVER'] = 1
        # Now, update original image size information
        hdu.header['WCSAXES'] = (2, "number of World Coordinate System axes")
        hdu.header['NPIX1'] = (self.naxis1, "Length of array axis 1")
        hdu.header['NPIX2'] = (self.naxis2, "Length of array axis 2")
        hdu.header['PIXVALUE'] = (0.0, "values of pixels in array")

        # Write out values to header...
        excluded_keys = ['naxis1','naxis2']
        for key in self.wcskeys:
            _dkey = self.wcstrans[key]
            if _dkey not in excluded_keys:
                hdu.header[key] = self.__dict__[_dkey]


        return hdu

    def _buildNewKeyname(self,key,prepend):
        """ Builds a new keyword based on original keyword name and
            a prepend string.
        """

        if len(prepend+key) <= 8: _new_key = prepend+key
        else: _new_key = str(prepend+key)[:8]

        return _new_key


    def copy(self,deep=yes):
        """ Makes a (deep)copy of this object for use by other objects.
        """
        if deep:
            return copy.deepcopy(self)
        else:
            return copy.copy(self)

    def help(self):
        """ Prints out help message."""
        print('wcsutil Version '+str(__version__)+':\n')
        print(self.__doc__)
