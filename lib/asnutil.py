"""
A module which provides utilities for reading, writing, creating and updating 
association tables and shift files.

:author: Warren Hack, Nadia Dencheva
:version: '0.1 (2008-01-03)'
"""
__docformat__ = 'restructuredtext'

import fileutil as fu
import wcsutil
import pyfits
import numpy as N
import os.path, time

__version__ = '0.1 (2008-01-03)'

def readASNTable(fname, output=None, prodonly=True):
    """
    Purpose
    =======
    Given a fits filename repesenting an association table reads in the table as a 
    dictionary which can be used by pydrizzle and multidrizzle.
    
    Algorithm
    =========
    An association table is a FITS binary table with 2 required columns: 'MEMNAME', 
    'MEMTYPE'. It checks 'MEMPRSNT' column and removes all files for which its value is 'no'.
    
    Example
    =======
    >>>from pytools import asnutil
    >>>asnutil.readASNTable('j8bt06010_shifts_asn.fits', prodonly=False)
    
    :Parameters:

    `fname`: string
             name of association table
    `output`: string
              name of output product - if not specified by the user,
              the first PROD-DTH name is used if present,
              if not, the first PROD-RPT name is used if present,
              if not, the rootname of the input association table is used.
    `prodonly`: bool
                what files should be considered as input
                if True - select only MEMTYPE=PROD* as input
                if False - select only MEMTYPE=EXP as input 
    
              
    """

    try:
        f = pyfits.open(fu.osfn(fname))
    except IOError:
        print "Can't open file %s\n" % fname
        return
    
    colnames = f[1].data.names
    try:
        colunits = f[1].data.units
    except AttributeError: pass
    
    hdr = f[0].header
    
    if 'MEMNAME' not in colnames or 'MEMTYPE' not in colnames:
        msg = 'Association table incomplete: required column(s) MEMNAME/MEMTYPE NOT found!'
        raise ValueError, msg

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
    if output == None:
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
    
    for k in d.keys():
        d[k] = d[k][valid_input]
    
    infiles = list(d['MEMNAME'].lower())
    if not infiles:
        print "No valid input specified"
        return
    
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
    Purpose
    =======
    A dictionary like object which represents an association table.
    An ASNTable object looks like this:

    {'members': {'j8bt06nyq': {'abshift': False,
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
    
    Example
    =======
    asnt=ASNTable([fname1,fname2,  fname3], shiftfile='shifts.txt')
    This creates a blank association table.
    asnt.create()
    This populates 'members' and 'order' in the association table based on infiles 
    and shiftfile.
    """
    def __init__(self, inlist=None, output=None, shiftfile=None):
        """
        :Parameters:
        `inlist`: a list
                  a python list of filenames
        `output`  a string
                  a user specified output name or 'final'
        `shiftfile`: a string
                  a name of a shift file, if given, the association table will be 
                  updated with the values in the shift file
        """

        if output == None:
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
        if inlist != None:
            for fn in inlist:
                self.order.append(fu.buildNewRootname(fn))

        dict.__init__(self, output=self.output, order=[], members={})
        if inlist != None:
            self.input = [fu.buildRootname(f) for f in inlist]
        self.shiftfile = shiftfile
    def create(self, shiftfile=None): 
        members = {}
        row = 0
        dshift = False
        abshift = False

        # Parse out shift file, if provided
        if shiftfile != None:
            sdict = ShiftFile(shiftfile)
        elif self.shiftfile != None:
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
        Purpose
        =======

        Update an existing association table
        
        :Parameters:
        
        `members`: dictionary
                   a dictionary representing asndict['members'] 
        `shiftfile`: string
                   the name of a shift file
                   If given, shiftfile will replace shifts in an asndict.
        `replace`: bool False(default)
                   a flag which indicates whether the 'members' item
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
        Purpose
        =======
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
            warningmsg += "#  The exisiting assocation table,      #\n"
            warningmsg += "           " + str(outfile) + '\n'
            warningmsg += "#  is being replaced.                   #\n"
            warningmsg += "#                                       #\n"
            warningmsg += "#########################################\n\n"
        fasn = pyfits.HDUList()
        
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
        
        memname = pyfits.Column(name='MEMNAME',format=namelen_str,array=N.char.array(mname))
        memtype = pyfits.Column(name='MEMTYPE',format='14A',array=N.char.array(mtype))
        memprsn = pyfits.Column(name='MEMPRSNT', format='L', array=N.array(mprsn).astype(N.uint8))
        xoffset = pyfits.Column(name='XOFFSET', format='E', array=N.array(xoff))
        yoffset = pyfits.Column(name='YOFFSET', format='E', array=N.array(yoff))
        xdelta = pyfits.Column(name='XDELTA', format='E', array=N.array(xsh))
        ydelta = pyfits.Column(name='YDELTA', format='E', array=N.array(ysh))
        rotation = pyfits.Column(name='ROTATION', format='E', array=N.array(rot))
        scale = pyfits.Column(name='SCALE', format='E', array=N.array(scl))
        
        hdu = pyfits.new_table([memname,memtype,memprsn,xoffset,yoffset,xdelta,ydelta,rotation,scale],nrows=len(mname))
        fasn.append(hdu)
        fasn.writeto(outfile, clobber=True)
        fasn.close()
        mem0 = self['order'][0]
        refimg = self['members'][mem0]['refimage']
        if refimg != None:
            whdu = wcsutil.WCSObject(refimg)
            whdu.createReferenceWCS(outfile,overwrite=False)
            ftab = pyfits.open(outfile)
            ftab['primary'].header.update('refimage', outfile+"[wcs]")
            ftab.close()
        del whdu
        
        
    
    def buildPrimary(self, fasn, output=None):
        _prihdr = pyfits.Header([pyfits.Card('SIMPLE', pyfits.TRUE,'Fits standard'),
                    pyfits.Card('BITPIX  ',                    16 ,' Bits per pixel'),
                    pyfits.Card('NAXIS   ',                     0 ,' Number of axes'),
                    pyfits.Card('ORIGIN  ',  'NOAO-IRAF FITS Image Kernel July 1999' ,'FITS file originator'),
                    pyfits.Card('IRAF-TLM',  '18:26:13 (27/03/2000)' ,' Time of last modification'),
                    pyfits.Card('EXTEND  ',pyfits.TRUE ,' File may contain standard extensions'),
                    pyfits.Card('NEXTEND ',                     1 ,' Number of standard extensions'),
                    pyfits.Card('DATE    ',  '2001-02-14T20:07:57',' date this file was written (yyyy-mm-dd)'),
                    pyfits.Card('FILENAME',  'hr_box_asn.fits'            ,' name of file'),
                    pyfits.Card('FILETYPE',  'ASN_TABLE'          ,' type of data found in data file'),
                    pyfits.Card('TELESCOP',  'HST'                ,' telescope used to acquire data'),
                    pyfits.Card('INSTRUME',  'ACS   '             ,' identifier for instrument used to acquire data'),
                    pyfits.Card('EQUINOX ',                2000.0 ,' equinox of celestial coord. system'),
                    pyfits.Card('ROOTNAME',  'hr_box  '              ,' rootname of the observation set'),
                    pyfits.Card('PRIMESI ',  'ACS   '             ,' instrument designated as prime'),
                    pyfits.Card('TARGNAME',  'SIM-DITHER'                     ,'proposer\'s target name'),
                    pyfits.Card('RA_TARG ',                    0. ,' right ascension of the target (deg) (J2000)'),
                    pyfits.Card('DEC_TARG',                    0. ,' declination of the target (deg) (J2000)'),
                    pyfits.Card('DETECTOR',  'HRC     '           ,' detector in use: WFC, HRC, or SBC'),
                    pyfits.Card('ASN_ID  ',  'hr_box  '           ,' unique identifier assigned to association'),
                    pyfits.Card('ASN_TAB ',  'hr_box_asn.fits'         ,' name of the association table')])
    
        # Format time values for keywords IRAF-TLM, and DATE
        _ltime = time.localtime(time.time())
        tlm_str = time.strftime('%H:%M:%S (%d/%m/%Y)',_ltime)
        date_str = time.strftime('%Y-%m-%dT%H:%M:%S',_ltime)
        origin_str = 'PyFITS Version '+pyfits.__version__
        # Build PRIMARY HDU
        _hdu = pyfits.PrimaryHDU(header=_prihdr)
        fasn.append(_hdu)

        newhdr = fasn['PRIMARY'].header
        mem0name = self['order'][0]
        refimg = self['members'][mem0name]['refimage']
        shframe = self['members'][mem0name]['shift_frame']
        fullname = fu.buildRootname(mem0name,ext=['_flt.fits', '_c0h.fits', '_c0f.fits'])
        try:
            # Open img1 to obtain keyword values for updating template
            fimg1 = pyfits.open(fullname)
        except:
            print 'File %s does not exist' % fullname


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
        newhdr.update('SHFRAME', shframe, comment="Frame which shifts are measured")
        newhdr.update('REFIMAGE', refimg, comment="Image shifts were measured from")

    
    
class ASNMember(dict):
    """
    Purpose
    =======
    A dictionary like object representing a member of an association table. It looks like this:
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
    If 'abshift' is True, shifts, roattion and scale reffer to absolute shifts. 
    If 'dshift'  is True, they are delta shifts. 

    """

    def __init__(self, xoff=0.0, yoff=0.0, rot=0.0, xshift=0.0, 
                 yshift=0.0, scale=1.0, dshift=False, abshift=False, refimage="", shift_frame="",
                 shift_units='pixels', row=0):
        
        dict.__init__(self, xoff=xoff, yoff=yoff, xshift=xshift, yshift=yshift, rot=rot, scale=scale, 
                      dshift=dshift, abshift=abshift, refimage=refimage, shift_frame=shift_frame, 
                      shift_units=shift_units, row=row)
        
class ShiftFile(dict):
    """
    A dict like object representing a shift file used by Pydrizzle and Mirashift.

    A shift file has the following format (name, Xsh, Ysh, Rot, Scale):
    
    # frame: output
    # refimage: tweak_wcs.fits[wcs]
    # form: delta 
    # units: pixels 
    j8bt06nyq_flt.fits    0.0  0.0    0.0    1.0
    j8bt06nzq_flt.fits    0.4091132  -0.5670202    359.9983    1.000165

    """
    
    def __init__(self,filename="", form='absolute', frame=None, units='pixels', 
                 order=None, refimage=None, **kw):
        """
        Purpose
        =======
        Create a dict like ShiftFile object from a shift file on disk or from 
        variables in memory. If a file name is provided all other parameters are ignored.
        
        Example
        =======
        
        1. Read a shift file on disk.
    
        sdict = ShiftFile('shifts.txt')
        
        2. Pass values for the fields of the shift file and a dictionary with all
        files:
    
        d={'j8bt06nyq_flt.fits': [0.0, 0.0, 0.0, 1.0], 
           'j8bt06nzq_flt.fits': [0.4091132, -0.5670202, 359.9983, 1.000165]}
    
        sdict = ShiftFile(form='absolute', frame='output', units='pixels', order=['j8bt06nyq_flt.fits',
        'j8bt06nzq_flt.fits'], refimage='tweak_wcs.fits[wcs]', **d)
        
        :Parameters:

        `filename`: string
                    name of shift file on disk, see above the expected format
        `form`:     string
                    form of shifts (absolute|delta)
        `frame`:    string
                    frame in which the shifts should be applied (input|output)
        `units`:    string
                    in which the shofts are measured (pixels?)
        `order`:    list
                    Keeps track of the order of the files
        `refimage`: string
                    name of reference image
        `**d`:      dictionary
                    keys: file names
                    values: a list:  [Xsh, Ysh, Rot, Scale]
                    The keys must match the files in the oder parameter.
                    
        :raise ValueError: If reference file can't be found
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
            
            raise ValueError, msg
            
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
        self.update(c)
        
        files = [f.strip().split(' ',1) for f in flines if not (f.startswith('#') or f.strip() == '')]
        for f in files:
            order.append(f[0])
            
        self['order'] = order

        for f in files:
            f[1] = f[1].split()
            try:
                f[1] = [float(s) for s in f[1]]
            except:
                msg = 'Cannot read in ', s, ' from shiftfile ', filename, ' as a float number'  
                raise ValueError, msg
            msg = "At least 2 and at most 4 shift values should be provided in a shiftfile"
            if len(f[1]) < 2:
                raise ValueError, msg
            elif len(f[1]) == 3:
                f[1].append(1.0)
            elif len(f[1]) == 2:
                f[1].extend([0.0, 1.0])
            elif len(f[1]) > 4:
                raise ValueError, msg
            
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
        
