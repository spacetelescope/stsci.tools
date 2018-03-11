"""
A module which provides utilities for reading, writing, creating and updating
association tables and shift files.

:author: Warren Hack, Nadia Dencheva
:version: '0.1 (2008-01-03)'
"""

from __future__ import absolute_import, division, print_function # confidence high

from . import fileutil as fu
from . import wcsutil
import astropy
from astropy.io import fits
import numpy as N
import os.path, time
from distutils.version import LooseVersion

ASTROPY_VER_GE13 = LooseVersion(astropy.__version__) >= LooseVersion('1.3')

__version__ = '0.2(2015-06-23)'


def readASNTable(fname, output=None, prodonly=False):
    """
    Given a fits filename repesenting an association table reads in the table as a
    dictionary which can be used by pydrizzle and multidrizzle.

    An association table is a FITS binary table with 2 required columns: 'MEMNAME',
    'MEMTYPE'. It checks 'MEMPRSNT' column and removes all files for which its value is 'no'.

    Parameters
    ----------
    fname : str
        name of association table
    output : str
        name of output product - if not specified by the user,
        the first PROD-DTH name is used if present,
        if not, the first PROD-RPT name is used if present,
        if not, the rootname of the input association table is used.
    prodonly : bool
        what files should be considered as input
        if True - select only MEMTYPE=PROD* as input
        if False - select only MEMTYPE=EXP as input

    Returns
    -------
    asndict : dict
        A dictionary-like object with all the association information.

    Examples
    --------
    An association table can be read from a file using the following commands::

    >>> from stsci.tools import asnutil
    >>> asntab = asnutil.readASNTable('j8bt06010_shifts_asn.fits', prodonly=False)  # doctest: +SKIP

    The `asntab` object can now be passed to other code to provide relationships
    between input and output images defined by the association table.

    """

    try:
        f = fits.open(fu.osfn(fname))
    except:
        raise IOError("Can't open file %s\n" % fname)

    colnames = f[1].data.names
    try:
        colunits = f[1].data.units
    except AttributeError: pass

    hdr = f[0].header

    if 'MEMNAME' not in colnames or 'MEMTYPE' not in colnames:
        msg = 'Association table incomplete: required column(s) MEMNAME/MEMTYPE NOT found!'
        raise ValueError(msg)

    d = {}
    for n in colnames:
        d[n]=f[1].data.field(n)
    f.close()

    valid_input = d['MEMPRSNT'].copy()
    memtype = d['MEMTYPE'].copy()
    prod_dth = (memtype.find('PROD-DTH')==0).nonzero()[0]
    prod_rpt = (memtype.find('PROD-RPT')==0).nonzero()[0]
    prod_crj = (memtype.find('PROD-CRJ')==0).nonzero()[0]

    # set output name
    if output is None:
        if prod_dth:
            output = d['MEMNAME'][prod_dth[0]]
        elif prod_rpt:
            output = d['MEMNAME'][prod_rpt[0]]
        elif prod_crj:
            output = d['MEMNAME'][prod_crj[0]]
        else:
            output = fname.split('_')[0]

    if prodonly:
        input = d['MEMTYPE'].find('PROD')==0
        if prod_dth:
            input[prod_dth] = False
    else:
        input = (d['MEMTYPE'].find('EXP')==0)
    valid_input *= input

    for k in d:
        d[k] = d[k][valid_input]

    infiles = list(d['MEMNAME'].lower())
    if not infiles:
        print("No valid input specified")
        return None

    if ('XOFFSET' in colnames and d['XOFFSET'].any()) or ('YOFFSET' in colnames and d['YOFFSET'].any()):
        abshift = True
        dshift = False
        try:
            units=colunits[colnames.index('XOFFSET')]
        except: units='pixels'
        xshifts = list(d['XOFFSET'])
        yshifts = list(d['YOFFSET'])
    elif ('XDELTA' in colnames and d['XDELTA'].any()) or  ('YDELTA' in colnames and d['YDELTA'].any()):
        abshift = False
        dshift = True
        try:
            units=colunits[colnames.index('XDELTA')]
        except: units='pixels'
        xshifts = list(d['XDELTA'])
        yshifts = list(d['YDELTA'])
    else:
        abshift = False
        dshift = False
    members = {}

    if not abshift and not dshift:
        asndict = ASNTable(infiles,output=output)
        asndict.create()
        return asndict
    else:
        try:
            refimage = hdr['refimage']
        except KeyError: refimage = None
        try:
            frame = hdr['shframe']
        except KeyError: frame = 'input'
        if 'ROTATION' in colnames:
            rots = list(d['ROTATION'])
        if 'SCALE' in colnames:
            scales = list(d['SCALE'])

        for r in range(len(infiles)):
            row = r
            xshift = xshifts[r]
            yshift = yshifts[r]
            if rots: rot = rots[r]
            if scales: scale = scales[r]
            members[infiles[r]] = ASNMember(row=row, dshift=dshift, abshift=abshift, rot=rot, xshift=xshift,
                                      yshift=yshift, scale=scale, refimage=refimage, shift_frame=frame,
                                      shift_units=units)


        asndict= ASNTable(infiles, output=output)
        asndict.create()
        asndict['members'].update(members)
        return asndict


class ASNTable(dict):
    """
    A dictionary like object which represents an association table.
    An ASNTable object looks like this::

        {'members':
                {'j8bt06nyq': {'abshift': False,
                           'dshift': True,
                           'refimage': 'j8bt06010_shifts_asn.fits[wcs]',
                           'rot': 0.0,
                           'row': 0,
                           'scale': 1.0,
                           'shift_frame': 'input',
                           'shift_units': 'pixels',
                           'xoff': 0.0,
                           'xshift': 0.0,
                           'yoff': 0.0,
                           'yshift': 0.0},
                'j8bt06nzq': {'abshift': False,
                           'dshift': True,
                           'refimage': 'j8bt06010_shifts_asn.fits[wcs]',
                           'rot': 359.99829,
                           'row': 1,
                           'scale': 1.000165,
                           'shift_frame': 'input',
                           'shift_units': 'pixels',
                           'xoff': 0.0,
                           'xshift': 0.4091132,
                           'yoff': 0.0,
                           'yshift': -0.56702018}},
                'order': ['j8bt06nyq', 'j8bt06nzq'],
                'output': 'j8bt06nyq'}

    Examples
    --------
    Creating an ASNTable object from 3 filenames and a shift file would be done using::

    >>> asnt=ASNTable([fname1,fname2,  fname3], shiftfile='shifts.txt')  # doctest: +SKIP

    The ASNTable object would have the 'members' and 'order'
    in the association table populated based on `infiles` and `shiftfile`.

    This creates a blank association table from the ASNTable object::

    >>> asnt.create()  # doctest: +SKIP

    """
    def __init__(self, inlist=None, output=None, shiftfile=None):
        """
        Parameters
        ----------
        inlist : list
            A list of filenames.
        output :  str
            A user specified output name or 'final'.
        shiftfile : str
            A name of a shift file, if given, the association table will be
            updated with the values in the shift file.

        """

        if output is None:
            if len(inlist) == 1:
                self.output = fu.buildNewRootname(inlist[0])
            else:
                self.output = 'final'
        else:
            self.output = fu.buildNewRootname(output)
            # Ensure that output name does not already contain '_drz'
            _indx = self.output.find('_drz')
            if _indx > 0:
                self.output = self.output[:_indx]

        self.order = []
        if inlist is not None:
            for fn in inlist:
                if fu.findFile(fu.buildRootname(fn)):
                    self.order.append(fu.buildNewRootname(fn))
                else:
                    # This may mean corrupted asn table in which a file is listed as present
                    # when it is missing.
                    raise IOError('File %s not found.\n' %fn)
        dict.__init__(self, output=self.output, order=[], members={})
        if inlist is not None:
            self.input = [fu.buildRootname(f) for f in inlist]
        self.shiftfile = shiftfile

    def create(self, shiftfile=None):
        members = {}
        row = 0
        dshift = False
        abshift = False

        # Parse out shift file, if provided
        if shiftfile is not None:
            sdict = ShiftFile(shiftfile)
        elif self.shiftfile is not None:
            sdict = ShiftFile(self.shiftfile)

            shift_frame = sdict['frame']
            shift_units = sdict['units']
            refimage = sdict['refimage']
            if sdict['form']=='delta':
                dshift = True
            else:
                abshift = True

            for f in self.input:
                xshift = sdict[f][0]
                yshift = sdict[f][1]
                rot = sdict[f][2]
                scale = sdict[f][3]
                #This may not be the right thing to do, may want to keep _flt in rootname
                # to distinguish between _c0h.fits, _c0f.fits and '.c0h'
                fname = fu.buildNewRootname(f)
                members[fname] = ASNMember(row=row, dshift=dshift, abshift=abshift, rot=rot, xshift=xshift,
                                  yshift=yshift, scale=scale, refimage=refimage, shift_frame=shift_frame,
                                  shift_units=shift_units)
                row+=1
        else:
            for f in self.input:
                # also here

                fname = fu.buildNewRootname(f)
                members[fname] = ASNMember(row=row)
                row+=1

        self['members'].update(members)
        self['order']=self.order


    def update(self, members=None, shiftfile=None, replace=False):
        __help_update="""
        Update an existing association table.

        Parameters
        ----------
        members : dict
            A dictionary representing asndict['members'].
        shiftfile : str
            The name of a shift file
            If given, shiftfile will replace shifts in an asndict.
        replace : bool False(default)
            A flag which indicates whether the 'members' item
            of an association table should be updated or replaced.
            default: False
            If True, it's up to the user to replace also asndict['order']
        """
        if members and isinstance(members, dict):
            if not replace:
                self['members'].update(members=members)
            else:
                self['members'] = members
        elif shiftfile:
            members = {}
            abshift = False
            dshift = False
            row = 0
            sdict = ShiftFile(shiftfile)
            shift_frame = sdict['frame']
            shift_units = sdict['units']
            refimage = sdict['refimage']
            if sdict['form']=='delta':
                dshift = True
            else:
                abshift = True

            for f in self.order:
                fullname = fu.buildRootname(f)
                xshift = sdict[fullname][0]
                yshift = sdict[fullname][1]
                rot = sdict[fullname][2]
                scale = sdict[fullname][3]
                members[f] = ASNMember(row=row, dshift=dshift, abshift=abshift, rot=rot, xshift=xshift,
                                  yshift=yshift, scale=scale, refimage=refimage, shift_frame=shift_frame,
                                  shift_units=shift_units)
                row+=1
            self['members'].update(members)
        else:
            #print __help_update
            pass

    def write(self, output=None):
        """
        Write association table to a file.

        """
        if not output:
            outfile = self['output']+'_asn.fits'
            output = self['output']
        else:
            outfile = output

        # Delete the file if it exists.
        if os.path.exists(outfile):
            warningmsg =  "\n#########################################\n"
            warningmsg += "#                                       #\n"
            warningmsg += "# WARNING:                              #\n"
            warningmsg += "#  The existing association table,      #\n"
            warningmsg += "           " + str(outfile) + '\n'
            warningmsg += "#  is being replaced.                   #\n"
            warningmsg += "#                                       #\n"
            warningmsg += "#########################################\n\n"
        fasn = fits.HDUList()

        # Compute maximum length of MEMNAME for table column definition
        _maxlen = 0
        for _fname in self['order']:
            if len(_fname) > _maxlen: _maxlen = len(_fname)
        # Enforce a mimimum size of 24
        if _maxlen < 24: _maxlen = 24
        namelen_str = str(_maxlen+2)+'A'
        self.buildPrimary(fasn, output=output)

        mname = self['order'][:]
        mname.append(output)
        mtype = ['EXP-DTH' for l in self['order']]
        mtype.append('PROD-DTH')
        mprsn = [True for l in self['order']]
        mprsn.append(False)
        xoff = [self['members'][l]['xoff'] for l in self['order']]
        xoff.append(0.0)
        yoff = [self['members'][l]['yoff'] for l in self['order']]
        yoff.append(0.0)
        xsh = [self['members'][l]['xshift'] for l in self['order']]
        xsh.append(0.0)
        ysh = [self['members'][l]['yshift'] for l in self['order']]
        ysh.append(0.0)
        rot = [self['members'][l]['rot'] for l in self['order']]
        rot.append(0.0)
        scl = [self['members'][l]['scale'] for l in self['order']]
        scl.append(1.0)

        memname = fits.Column(name='MEMNAME',format=namelen_str,array=N.char.array(mname))
        memtype = fits.Column(name='MEMTYPE',format='14A',array=N.char.array(mtype))
        memprsn = fits.Column(name='MEMPRSNT', format='L', array=N.array(mprsn).astype(N.uint8))
        xoffset = fits.Column(name='XOFFSET', format='E', array=N.array(xoff))
        yoffset = fits.Column(name='YOFFSET', format='E', array=N.array(yoff))
        xdelta = fits.Column(name='XDELTA', format='E', array=N.array(xsh))
        ydelta = fits.Column(name='YDELTA', format='E', array=N.array(ysh))
        rotation = fits.Column(name='ROTATION', format='E', array=N.array(rot))
        scale = fits.Column(name='SCALE', format='E', array=N.array(scl))
        cols = fits.ColDefs([memname,memtype,memprsn,xoffset,yoffset,xdelta,ydelta,rotation,scale])
        hdu = fits.BinTableHDU.from_columns(cols)
        fasn.append(hdu)
        if ASTROPY_VER_GE13:
            fasn.writeto(outfile, overwrite=True)
        else:
            fasn.writeto(outfile, clobber=True)
        fasn.close()
        mem0 = self['order'][0]
        refimg = self['members'][mem0]['refimage']
        if refimg is not None:
            whdu = wcsutil.WCSObject(refimg)
            whdu.createReferenceWCS(outfile,overwrite=False)
            ftab = fits.open(outfile)
            ftab['primary'].header['refimage'] = outfile+"[wcs]"
            ftab.close()
        del whdu



    def buildPrimary(self, fasn, output=None):
        _prihdr = fits.Header([fits.Card('SIMPLE', True, 'Fits standard'),
                    fits.Card('BITPIX  ',                    16 ,' Bits per pixel'),
                    fits.Card('NAXIS   ',                     0 ,' Number of axes'),
                    fits.Card('ORIGIN  ',  'NOAO-IRAF FITS Image Kernel July 1999' ,'FITS file originator'),
                    fits.Card('IRAF-TLM',  '18:26:13 (27/03/2000)' ,' Time of last modification'),
                    fits.Card('EXTEND  ', True ,' File may contain standard extensions'),
                    fits.Card('NEXTEND ',                     1 ,' Number of standard extensions'),
                    fits.Card('DATE    ',  '2001-02-14T20:07:57',' date this file was written (yyyy-mm-dd)'),
                    fits.Card('FILENAME',  'hr_box_asn.fits'            ,' name of file'),
                    fits.Card('FILETYPE',  'ASN_TABLE'          ,' type of data found in data file'),
                    fits.Card('TELESCOP',  'HST'                ,' telescope used to acquire data'),
                    fits.Card('INSTRUME',  'ACS   '             ,' identifier for instrument used to acquire data'),
                    fits.Card('EQUINOX ',                2000.0 ,' equinox of celestial coord. system'),
                    fits.Card('ROOTNAME',  'hr_box  '              ,' rootname of the observation set'),
                    fits.Card('PRIMESI ',  'ACS   '             ,' instrument designated as prime'),
                    fits.Card('TARGNAME',  'SIM-DITHER'                     ,'proposer\'s target name'),
                    fits.Card('RA_TARG ',                    0. ,' right ascension of the target (deg) (J2000)'),
                    fits.Card('DEC_TARG',                    0. ,' declination of the target (deg) (J2000)'),
                    fits.Card('DETECTOR',  'HRC     '           ,' detector in use: WFC, HRC, or SBC'),
                    fits.Card('ASN_ID  ',  'hr_box  '           ,' unique identifier assigned to association'),
                    fits.Card('ASN_TAB ',  'hr_box_asn.fits'         ,' name of the association table')])

        # Format time values for keywords IRAF-TLM, and DATE
        _ltime = time.localtime(time.time())
        tlm_str = time.strftime('%H:%M:%S (%d/%m/%Y)',_ltime)
        date_str = time.strftime('%Y-%m-%dT%H:%M:%S',_ltime)
        origin_str = 'FITS Version '+ astropy.__version__
        # Build PRIMARY HDU
        _hdu = fits.PrimaryHDU(header=_prihdr)
        fasn.append(_hdu)

        newhdr = fasn['PRIMARY'].header
        mem0name = self['order'][0]
        refimg = self['members'][mem0name]['refimage']
        shframe = self['members'][mem0name]['shift_frame']
        fullname = fu.buildRootname(mem0name,ext=['_flt.fits', '_c0h.fits', '_c0f.fits'])
        try:
            # Open img1 to obtain keyword values for updating template
            fimg1 = fits.open(fullname)
        except:
            print('File %s does not exist' % fullname)


        kws = ['INSTRUME', 'PRIMESI', 'TARGNAME', 'DETECTOR', 'RA_TARG', 'DEC_TARG']
        mem0hdr = fimg1['PRIMARY'].header
        default = 'UNKNOWN'
        for kw in kws:
            try:
                newhdr[kw] = mem0hdr[kw]
            except:
                newhdr[kw] = default
        fimg1.close()

        if not output:
            output = self['output']

        outfilename = fu.buildNewRootname(output, extn='_asn.fits')
        newhdr['IRAF-TLM']=tlm_str
        newhdr['DATE'] = date_str
        newhdr['ORIGIN'] = origin_str
        newhdr['ROOTNAME'] = output

        newhdr['FILENAME'] = outfilename
        newhdr['ASN_ID'] = output
        newhdr['ASN_TAB'] = outfilename
        newhdr['SHFRAME'] = (shframe, "Frame which shifts are measured")
        newhdr['REFIMAGE'] = (refimg, "Image shifts were measured from")



class ASNMember(dict):
    """
    A dictionary like object representing a member of an association table. It looks like this::

        'j8bt06nzq': {'abshift': False,
                  'dshift': True,
                  'refimage': 'j8bt06010_shifts_asn.fits[wcs]',
                  'rot': 359.99829,
                  'row': 1,
                  'scale': 1.000165,
                  'shift_frame': 'input',
                  'shift_units': 'pixels',
                  'xoff': 0.0,
                  'xshift': 0.4091132,
                  'yoff': 0.0,
                  'yshift': -0.56702018}

    If `abshift` is True, shifts, rotation and scale refer to absolute shifts.
    If `dshift`  is True, they are delta shifts.

    """

    def __init__(self, xoff=0.0, yoff=0.0, rot=0.0, xshift=0.0,
                 yshift=0.0, scale=1.0, dshift=False, abshift=False, refimage="", shift_frame="",
                 shift_units='pixels', row=0):

        dict.__init__(self, xoff=xoff, yoff=yoff, xshift=xshift, yshift=yshift, rot=rot, scale=scale,
                      dshift=dshift, abshift=abshift, refimage=refimage, shift_frame=shift_frame,
                      shift_units=shift_units, row=row)

class ShiftFile(dict):
    """
    A shift file has the following format (name, Xsh, Ysh, Rot, Scale)::

        # frame: output
        # refimage: tweak_wcs.fits[wcs]
        # form: delta
        # units: pixels
        j8bt06nyq_flt.fits    0.0  0.0    0.0    1.0
        j8bt06nzq_flt.fits    0.4091132  -0.5670202    359.9983    1.000165

    This object creates a `dict` like object representing a shift file used by Pydrizzle and Mirashift.
    """

    def __init__(self,filename="", form='delta', frame=None, units='pixels',
                 order=None, refimage=None, **kw):
        """
        :Purpose: Create a dict like ShiftFile object from a shift file on disk or from
                  variables in memory. If a file name is provided all other parameters are ignored.

        Examples
        ---------
        These examples demonstrate a couple of the most common usages.

        Read a shift file on disk using::

        >>> sdict = ShiftFile('shifts.txt')  # doctest: +SKIP

        Pass values for the fields of the shift file and a dictionary with all files::

        >>> d={'j8bt06nyq_flt.fits': [0.0, 0.0, 0.0, 1.0],
        ...    'j8bt06nzq_flt.fits': [0.4091132, -0.5670202, 359.9983, 1.000165]}

        >>> sdict = ShiftFile(
        ...     form='absolute', frame='output', units='pixels',
        ...     order=['j8bt06nyq_flt.fits', 'j8bt06nzq_flt.fits'],
        ...     refimage='tweak_wcs.fits[wcs]', **d)  # doctest: +SKIP

        The return value can then be used to provide the shift information to code in memory.

        Parameters
        ----------
        filename : str
            Name of shift file on disk, see above the expected format
        form : str
            Form of shifts (absolute|delta)
        frame : str
            Frame in which the shifts should be applied (input|output)
        units : str
            Units in which the shifts are measured.
        order : list
            Keeps track of the order of the files.
        refimage : str
                    name of reference image
         **d :  dict
                    keys: file names
                    values: a list:  [Xsh, Ysh, Rot, Scale]
                    The keys must match the files in the order parameter.

        Raises
        ------
        ValueError
            If reference file can't be found

        """
        ## History: This is refactored code which was initially in fileutil.py and
        ## pydrizzle: buildasn.py and updateasn.py

        dict.__init__(self, form=form, frame=frame, units=units,order=order, refimage=refimage)

        if filename == "":
            self.update(kw)
        else:
            self.readShiftFile(filename)

        if not self.verifyShiftFile():
            msg = "\nReference image not found.\n "
            msg += "The keyword in the shift file has changed from 'reference' to 'refimage'.\n"
            msg += "Make sure this keyword is specified as 'refimage' in %s." %filename

            raise ValueError(msg)

    def readShiftFile(self, filename):
        """
        Reads a shift file from disk and populates a dictionary.
        """
        order = []
        fshift = open(filename,'r')
        flines = fshift.readlines()
        fshift.close()

        common = [f.strip('#').strip() for f in flines if f.startswith('#')]
        c=[line.split(': ') for line in common]

        # Remove any line comments in the shift file - lines starting with '#'
        # but not part of the common block.
        for l in c:
            if l[0] not in ['frame', 'refimage', 'form', 'units']:
                c.remove(l)

        for line in c: line[1]=line[1].strip()
        self.update(c)

        files = [f.strip().split(' ',1) for f in flines if not (f.startswith('#') or f.strip() == '')]
        for f in files:
            order.append(f[0])

        self['order'] = order

        for f in files:
            # Check to see if filename provided is a full filename that corresponds
            # to a file on the path.  If not, try to convert given rootname into
            # a valid filename based on available files.  This may or may not
            # define the correct filename, which is why it prints out what it is
            # doing, so that the user can verify and edit the shiftfile if needed.
            #NOTE:
            # Supporting the specification of only rootnames in the shiftfile with this
            # filename expansion is NOT to be documented, but provided solely as
            # an undocumented, dangerous and not fully supported helper function for
            # some backwards compatibility.
            if not os.path.exists(f[0]):
                f[0] = fu.buildRootname(f[0])
                print('Defining filename in shiftfile as: ', f[0])

            f[1] = f[1].split()
            try:
                f[1] = [float(s) for s in f[1]]
            except:
                msg = 'Cannot read in ', s, ' from shiftfile ', filename, ' as a float number'
                raise ValueError(msg)
            msg = "At least 2 and at most 4 shift values should be provided in a shiftfile"
            if len(f[1]) < 2:
                raise ValueError(msg)
            elif len(f[1]) == 3:
                f[1].append(1.0)
            elif len(f[1]) == 2:
                f[1].extend([0.0, 1.0])
            elif len(f[1]) > 4:
                raise ValueError(msg)

        fdict = dict(files)
        self.update(fdict)


    def verifyShiftFile(self):
        """
        Verifies that reference file exists.
        """
        if self['refimage'] and fu.findFile(self['refimage']):
            return True
        else: return False

    def writeShiftFile(self, filename="shifts.txt"):
        """
        Writes a shift file object to a file on disk using the convention for shift file format.
        """
        lines = ['# frame: ', self['frame'], '\n',
                 '# refimage: ', self['refimage'], '\n',
                 '# form: ', self['form'], '\n',
                 '# units: ', self['units'], '\n']

        for o in self['order']:
            ss = " "
            for shift in self[o]:
                ss += str(shift) + " "
            line = str(o) + ss + "\n"
            lines.append(line)

        fshifts= open(filename, 'w')
        fshifts.writelines(lines)
        fshifts.close()
