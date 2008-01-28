#!/usr/bin/env python

import unittest
import pytools.stpyfits as stpyfits
import pyfits
import numpy as np
import exceptions,os,sys

class TestStpyfitsFunctions(unittest.TestCase):

    tmpfilename = 'tmpfile.out'

    def setUp(self):
        # Perform set up actions (if any)
        pass

    def tearDown(self):
        # Perform clean-up actions (if any)
        pass

    def testInfoConvienceFunction(self):
        """Test the info convience function in both the pyfits and stpyfits 
           namespace."""

        tmpfile = open(self.tmpfilename,'w')
        sys.stdout = tmpfile
        stpyfits.info('o4sp040b0_raw.fits')
        pyfits.info('o4sp040b0_raw.fits')
        stpyfits.info('cdva2.fits')
        pyfits.info('cdva2.fits')
        sys.stdout = sys.__stdout__
        tmpfile.close()
        tmpfile = open(self.tmpfilename,'r')
        output = tmpfile.readlines()
        tmpfile.close()
        os.remove(self.tmpfilename)

        self.assertEqual(output,["Filename: o4sp040b0_raw.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU     215  ()            int16\n",
        "1    SCI         ImageHDU       143  (1062, 1044)  int16\n",
        "2    ERR         ImageHDU        71  (1062, 1044)  int16\n",
        "3    DQ          ImageHDU        71  (1062, 1044)  int16\n",
        "4    SCI         ImageHDU       143  (1062, 1044)  int16\n",
        "5    ERR         ImageHDU        71  (1062, 1044)  int16\n",
        "6    DQ          ImageHDU        71  (1062, 1044)  int16\n",
        "Filename: o4sp040b0_raw.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU     215  ()            int16\n",
        "1    SCI         ImageHDU       143  (1062, 1044)  int16\n",
        "2    ERR         ImageHDU        71  ()            int16\n",
        "3    DQ          ImageHDU        71  ()            int16\n",
        "4    SCI         ImageHDU       143  (1062, 1044)  int16\n",
        "5    ERR         ImageHDU        71  ()            int16\n",
        "6    DQ          ImageHDU        71  ()            int16\n",
        "Filename: cdva2.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU       7  (10, 10)      int32\n",
        "Filename: cdva2.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU       7  ()            int32\n"])

    def testOpenConvienceFunction(self):
        """Test the open convience function in both the pyfits and stpyfits 
           namespace."""

        hdul = stpyfits.open('cdva2.fits')
        hdul1 = pyfits.open('cdva2.fits')

        self.assertEqual(hdul[0].header['NAXIS'],2)
        self.assertEqual(hdul1[0].header['NAXIS'],0)
        self.assertEqual(hdul[0].header['NAXIS1'],10)
        self.assertEqual(hdul[0].header['NAXIS2'],10)

        try:
            val = hdul1[0].header['NAXIS1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NAXIS1 in pyfits namespace")
       
        try:
            val = hdul1[0].header['NAXIS2']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NAXIS2 in pyfits namespace")

        try:
            val = hdul[0].header['NPIX1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NPIX1 in stpyfits namespace")
       
        try:
            val = hdul[0].header['NPIX2']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NPIX2 in stpyfits namespace")

        self.assertEqual(hdul1[0].header['NPIX1'],10)
        self.assertEqual(hdul1[0].header['NPIX2'],10)

        self.assertEqual(hdul[0].data.all(), np.array([[1,1,1,1,1,1,1,1,1,1],
                                                      [1,1,1,1,1,1,1,1,1,1],
                                                      [1,1,1,1,1,1,1,1,1,1],
                                                      [1,1,1,1,1,1,1,1,1,1],
                                                      [1,1,1,1,1,1,1,1,1,1],
                                                      [1,1,1,1,1,1,1,1,1,1],
                                                      [1,1,1,1,1,1,1,1,1,1],
                                                      [1,1,1,1,1,1,1,1,1,1],
                                                      [1,1,1,1,1,1,1,1,1,1],
                                                      [1,1,1,1,1,1,1,1,1,1]],
                                                      dtype=np.int32).all())
        self.assertEqual(hdul1[0].data, None)

        hdul.close()
        hdul1.close()

    def testGetHeaderConvienceFunction(self):
        """Test the getheader convience function in both the pyfits and 
           stpyfits namespace."""

        hd = stpyfits.getheader('cdva2.fits')
        hd1 = pyfits.getheader('cdva2.fits')

        self.assertEqual(hd['NAXIS'],2)
        self.assertEqual(hd1['NAXIS'],0)
        self.assertEqual(hd['NAXIS1'],10)
        self.assertEqual(hd['NAXIS2'],10)

        try:
            val = hd1['NAXIS1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NAXIS1 in pyfits namespace")
       
        try:
            val = hd1['NAXIS2']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NAXIS2 in pyfits namespace")

        try:
            val = hd['NPIX1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NPIX1 in stpyfits namespace")
       
        try:
            val = hd['NPIX2']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NPIX2 in stpyfits namespace")

        self.assertEqual(hd1['NPIX1'],10)
        self.assertEqual(hd1['NPIX2'],10)

        hd = stpyfits.getheader('o4sp040b0_raw.fits',2)
        hd1 = pyfits.getheader('o4sp040b0_raw.fits',2)

        self.assertEqual(hd['NAXIS'],2)
        self.assertEqual(hd1['NAXIS'],0)
        self.assertEqual(hd['NAXIS1'],1062)
        self.assertEqual(hd['NAXIS2'],1044)

        try:
            val = hd1['NAXIS1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NAXIS1 in pyfits namespace")
       
        try:
            val = hd1['NAXIS2']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NAXIS2 in pyfits namespace")

        try:
            val = hd['NPIX1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NPIX1 in stpyfits namespace")
       
        try:
            val = hd['NPIX2']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NPIX2 in stpyfits namespace")

        self.assertEqual(hd1['NPIX1'],1062)
        self.assertEqual(hd1['NPIX2'],1044)

    def testGetDataConvienceFunction(self):
        """Test the getdata convience function in both the pyfits and 
           stpyfits namespace."""

        d = stpyfits.getdata('cdva2.fits')
        self.assertEqual(d.all(), np.array([[1,1,1,1,1,1,1,1,1,1],
                                            [1,1,1,1,1,1,1,1,1,1],
                                            [1,1,1,1,1,1,1,1,1,1],
                                            [1,1,1,1,1,1,1,1,1,1],
                                            [1,1,1,1,1,1,1,1,1,1],
                                            [1,1,1,1,1,1,1,1,1,1],
                                            [1,1,1,1,1,1,1,1,1,1],
                                            [1,1,1,1,1,1,1,1,1,1],
                                            [1,1,1,1,1,1,1,1,1,1],
                                            [1,1,1,1,1,1,1,1,1,1]],
                                            dtype=np.int32).all())

        try:
            d1 = pyfits.getdata('cdva2.fits')
        except IndexError:
            pass
        else:
            self.fail(
             "expected an IndexError exception for getdata in pyfits namespace")

    def testGetValConvienceFunction(self):
        """Test the getval convience function in both the pyfits and 
           stpyfits namespace."""

        val = stpyfits.getval('cdva2.fits','NAXIS',0)
        val1 = pyfits.getval('cdva2.fits','NAXIS',0)
        self.assertEqual(val, 2)
        self.assertEqual(val1,0)

    def testwritetoConvienceFunction(self):
        """Test the writeto convience function in both the pyfits and stpyfits 
           namespace."""

        hdul = stpyfits.open('cdva2.fits')
        hdul1 = pyfits.open('cdva2.fits')

        stpyfits.writeto('new.fits',hdul[0].data,hdul[0].header,clobber=True)
        pyfits.writeto('new1.fits',hdul1[0].data,hdul1[0].header,clobber=True)

        tmpfile = open(self.tmpfilename,'w')
        sys.stdout = tmpfile
        pyfits.info('new.fits')
        stpyfits.info('new.fits')
        pyfits.info('new1.fits')
        stpyfits.info('new1.fits')
        sys.stdout = sys.__stdout__
        tmpfile.close()
        tmpfile = open(self.tmpfilename,'r')
        output = tmpfile.readlines()
        tmpfile.close()
        os.remove(self.tmpfilename)
        hdul.close()
        hdul1.close()
        os.remove('new.fits')
        os.remove('new1.fits')

        self.assertEqual(output,["Filename: new.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU       6  ()            int32\n",
        "Filename: new.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU       6  (10, 10)      int32\n",
        "Filename: new1.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU       6  ()            uint8\n",
        "Filename: new1.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU       6  (10, 10)      uint8\n"])

    def testappendConvienceFunction(self):
        """Test the append convience function in both the pyfits and stpyfits 
           namespace."""

        hdul = stpyfits.open('cdva2.fits')
        hdul1 = pyfits.open('cdva2.fits')

        stpyfits.writeto('new.fits',hdul[0].data,hdul[0].header,clobber=True)
        pyfits.writeto('new1.fits',hdul1[0].data,hdul1[0].header,clobber=True)

        hdu = stpyfits.ImageHDU()
        hdu1 = pyfits.ImageHDU()

        hdu.data = hdul[0].data
        hdu1.data = hdul1[0].data
        hdu.header.update('BITPIX',32)
        hdu1.header.update('BITPIX',32)
        hdu.header.update('NAXIS',2)
        hdu.header.update('NAXIS1',10,'length of constant array axis 1',
                          after='NAXIS')
        hdu.header.update('NAXIS2',10,'length of constant array axis 2',
                          after='NAXIS1')
        hdu.header.update('PIXVALUE',1,'Constant pixel value',after='GCOUNT')
        hdu1.header.update('PIXVALUE',1,'Constant pixel value',after='GCOUNT')
        hdu1.header.update('NPIX1',10,'length of constant array axis 1',
                           after='GCOUNT')
        hdu1.header.update('NPIX2',10,'length of constant array axis 2',
                           after='NPIX1')
        stpyfits.append('new.fits',hdu.data,hdu.header)
        pyfits.append('new1.fits',hdu1.data,hdu1.header)

        tmpfile = open(self.tmpfilename,'w')
        sys.stdout = tmpfile
        stpyfits.info('new.fits')
        stpyfits.info('new1.fits')
        pyfits.info('new.fits')
        pyfits.info('new1.fits')
        sys.stdout = sys.__stdout__
        tmpfile.close()
        tmpfile = open(self.tmpfilename,'r')
        output = tmpfile.readlines()
        tmpfile.close()
        os.remove(self.tmpfilename)

        self.assertEqual(output,["Filename: new.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU       7  (10, 10)      int32\n",
        "1                ImageHDU         8  (10, 10)      int32\n",
        "Filename: new1.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU       7  (10, 10)      uint8\n",
        "1                ImageHDU         8  (10, 10)      uint8\n",
        "Filename: new.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU       7  ()            int32\n",
        "1                ImageHDU         8  ()            int32\n",
        "Filename: new1.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU       7  ()            uint8\n",
        "1                ImageHDU         8  ()            uint8\n"])

        hdul5 = stpyfits.open('new.fits')
        hdul6 = pyfits.open('new1.fits')
        self.assertEqual(hdul5[1].header['NAXIS'],2)
        self.assertEqual(hdul6[1].header['NAXIS'],0)
        self.assertEqual(hdul5[1].header['NAXIS1'],10)
        self.assertEqual(hdul5[1].header['NAXIS2'],10)

        try:
            val = hdul6[1].header['NAXIS1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NAXIS1 in pyfits namespace")
       
        try:
            val = hdul6[1].header['NAXIS2']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NAXIS2 in pyfits namespace")

        try:
            val = hdul5[1].header['NPIX1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NPIX1 in stpyfits namespace")
       
        try:
            val = hdul5[1].header['NPIX2']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NPIX2 in stpyfits namespace")

        self.assertEqual(hdul6[1].header['NPIX1'],10)
        self.assertEqual(hdul6[1].header['NPIX2'],10)

        self.assertEqual(hdul5[1].data.all(), np.array([[1,1,1,1,1,1,1,1,1,1],
                                                        [1,1,1,1,1,1,1,1,1,1],
                                                        [1,1,1,1,1,1,1,1,1,1],
                                                        [1,1,1,1,1,1,1,1,1,1],
                                                        [1,1,1,1,1,1,1,1,1,1],
                                                        [1,1,1,1,1,1,1,1,1,1],
                                                        [1,1,1,1,1,1,1,1,1,1],
                                                        [1,1,1,1,1,1,1,1,1,1],
                                                        [1,1,1,1,1,1,1,1,1,1],
                                                        [1,1,1,1,1,1,1,1,1,1]],
                                                        dtype=np.int32).all())
        self.assertEqual(hdul6[1].data, None)

        hdul5.close()
        hdul6.close()
        hdul.close()
        hdul1.close()
        os.remove('new.fits')
        os.remove('new1.fits')

    def testupdateConvienceFunction(self):
        """Test the update convience function in both the pyfits and stpyfits 
           namespace."""

        hdul = stpyfits.open('cdva2.fits')
        hdul1 = pyfits.open('cdva2.fits')

        stpyfits.writeto('new.fits',hdul[0].data,hdul[0].header,clobber=True)

        hdu = stpyfits.ImageHDU()
        hdu1 = pyfits.ImageHDU()

        hdu.data = hdul[0].data
        hdu1.data = hdul1[0].data
        hdu.header.update('BITPIX',32)
        hdu1.header.update('BITPIX',32)
        hdu.header.update('NAXIS',2)
        hdu.header.update('NAXIS1',10,'length of constant array axis 1',
                          after='NAXIS')
        hdu.header.update('NAXIS2',10,'length of constant array axis 2',
                          after='NAXIS1')
        hdu.header.update('PIXVALUE',1,'Constant pixel value',after='GCOUNT')
        hdu1.header.update('PIXVALUE',1,'Constant pixel value',after='GCOUNT')
        hdu1.header.update('NPIX1',10,'length of constant array axis 1',
                           after='GCOUNT')
        hdu1.header.update('NPIX2',10,'length of constant array axis 2',
                           after='NPIX1')
        stpyfits.append('new.fits',hdu.data,hdu.header)

        d = hdu.data*0

        stpyfits.update('new.fits',d,hdu.header,1)
        tmpfile = open(self.tmpfilename,'w')
        sys.stdout = tmpfile
        pyfits.info('new.fits')
        stpyfits.info('new.fits')
        sys.stdout = sys.__stdout__
        tmpfile.close()
        tmpfile = open(self.tmpfilename,'r')
        output = tmpfile.readlines()
        tmpfile.close()
        os.remove(self.tmpfilename)

        self.assertEqual(output,["Filename: new.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU       7  ()            int32\n",
        "1                ImageHDU         8  ()            int32\n",
        "Filename: new.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU       7  (10, 10)      int32\n",
        "1                ImageHDU         8  (10, 10)      int32\n"])

        hdul7 = stpyfits.open('new.fits')
        self.assertEqual(hdul7[1].header['NAXIS'],2)
        self.assertEqual(hdul7[1].header['NAXIS1'],10)
        self.assertEqual(hdul7[1].header['NAXIS2'],10)
        self.assertEqual(hdul7[1].header['PIXVALUE'],0)
        
        try:
            val = hdul7[1].header['NPIX1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NPIX1 in stpyfits namespace")
       
        try:
            val = hdul7[1].header['NPIX2']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NPIX2 in stpyfits namespace")

        self.assertEqual(hdul7[1].data.all(), np.array([[0,0,0,0,0,0,0,0,0,0],
                                                        [0,0,0,0,0,0,0,0,0,0],
                                                        [0,0,0,0,0,0,0,0,0,0],
                                                        [0,0,0,0,0,0,0,0,0,0],
                                                        [0,0,0,0,0,0,0,0,0,0],
                                                        [0,0,0,0,0,0,0,0,0,0],
                                                        [0,0,0,0,0,0,0,0,0,0],
                                                        [0,0,0,0,0,0,0,0,0,0],
                                                        [0,0,0,0,0,0,0,0,0,0],
                                                        [0,0,0,0,0,0,0,0,0,0]],
                                                        dtype=np.int32).all())

        hdul8 = pyfits.open('new.fits')
        self.assertEqual(hdul8[1].header['NAXIS'],0)
        self.assertEqual(hdul8[1].header['NPIX1'],10)
        self.assertEqual(hdul8[1].header['NPIX2'],10)
        self.assertEqual(hdul8[1].header['PIXVALUE'],0)
        
        try:
            val = hdul8[1].header['NAXIS1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NAXIS1 in pyfits namespace")
       
        try:
            val = hdul8[1].header['NAXIS2']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NAXIS2 in pyfits namespace")
        
        self.assertEqual(hdul8[1].data, None)

        hdul7.close()
        hdul8.close()
        hdul.close()
        hdul1.close()
        os.remove('new.fits')

    def testImageHDUConstructor(self):
        """Test the ImageHDU constructor in both the pyfits and stpyfits 
           namespace."""

        hdu = stpyfits.ImageHDU()
        self.assertEqual(hdu.header._hdutype,stpyfits.st_ImageHDU)
        hdu1 = pyfits.ImageHDU()
        self.assertEqual(hdu1.header._hdutype,pyfits.NP_pyfits.ImageHDU)
        self.assertEqual(type(hdu),stpyfits.st_ImageHDU)
        self.assertEqual(type(hdu1),pyfits.NP_pyfits.ImageHDU)

    def testPrimaryHDUConstructor(self):
        """Test the PrimaryHDU constructor in both the pyfits and stpyfits 
           namespace.  Although stpyfits does not reimplement the 
           constructor, it does add st_ImageBaseHDU to the inheritance
           hierarchy of pyfits.PrimaryHDU when accessed through the stpyfits
           namespace.  This method tests that that inheritance is working"""

        n = np.zeros(10)
        n = n + 1
        
        hdu = stpyfits.PrimaryHDU(n)
        hdu.header.update('PIXVALUE',1.,'Constant pixel value',after='EXTEND')
        stpyfits.writeto('new.fits',hdu.data,hdu.header,clobber=True)
        hdul = stpyfits.open('new.fits')
        hdul1 = pyfits.open('new.fits')

        self.assertEqual(hdul[0].header['NAXIS'],1)
        self.assertEqual(hdul[0].header['NAXIS1'],10)
        self.assertEqual(hdul[0].header['PIXVALUE'],1.0)
        
        try:
            val = hdul[0].header['NPIX1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NPIX1 in stpyfits namespace")
       
        self.assertEqual(hdul[0].data.all(), np.array(
                         [[1.,1.,1.,1.,1.,1.,1.,1.,1.,1.]],
                         dtype=np.float32).all())

        self.assertEqual(hdul1[0].header['NAXIS'],0)
        self.assertEqual(hdul1[0].header['NPIX1'],10)
        self.assertEqual(hdul1[0].header['PIXVALUE'],1.0)
        
        try:
            val = hdul1[0].header['NAXIS1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NAXIS1 in pyfits namespace")
       
        self.assertEqual(hdul1[0].data, None)

        hdul.close()
        hdul1.close()
        os.remove('new.fits')

    def testHDUListWritetoMethod(self):
        """Test the writeto method of HDUList in both the pyfits and stpyfits 
           namespace."""

        hdu = stpyfits.PrimaryHDU()
        hdu1 = stpyfits.ImageHDU()
        hdu.data = np.array([[0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0]], dtype=np.int32)
        hdu1.data = hdu.data+2
        hdu.header.update('BITPIX',32)
        hdu1.header.update('BITPIX',32)
        hdu.header.update('NAXIS',2)
        hdu.header.update('NAXIS1',10,'length of constant array axis 1',
                          after='NAXIS')
        hdu.header.update('NAXIS2',10,'length of constant array axis 2',
                          after='NAXIS1')
        hdu.header.update('PIXVALUE',0,'Constant pixel value',after='NAXIS2')
        hdu1.header.update('PIXVALUE',2,'Constant pixel value',after='GCOUNT')
        hdu1.header.update('NAXIS',2)
        hdu1.header.update('NAXIS1',10,'length of constant array axis 1',
                           after='NAXIS')
        hdu1.header.update('NAXIS2',10,'length of constant array axis 2',
                           after='NAXIS1')
        hdul = stpyfits.HDUList([hdu,hdu1])
        hdul.writeto('new.fits',clobber=True)

        tmpfile = open(self.tmpfilename,'w')
        sys.stdout = tmpfile
        stpyfits.info('new.fits')
        pyfits.info('new.fits')
        sys.stdout = sys.__stdout__
        tmpfile.close()
        tmpfile = open(self.tmpfilename,'r')
        output = tmpfile.readlines()
        tmpfile.close()
        os.remove(self.tmpfilename)

        self.assertEqual(output,["Filename: new.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU       7  (10, 10)      int32\n",
        "1                ImageHDU         8  (10, 10)      int32\n",
        "Filename: new.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU       7  ()            int32\n",
        "1                ImageHDU         8  ()            int32\n"])

        hdul1 = stpyfits.open('new.fits')
        hdul2 = pyfits.open('new.fits')

        self.assertEqual(hdul1[0].header['NAXIS'],2)
        self.assertEqual(hdul1[0].header['NAXIS1'],10)
        self.assertEqual(hdul1[0].header['NAXIS2'],10)
        self.assertEqual(hdul1[0].header['PIXVALUE'],0)
        
        try:
            val = hdul1[0].header['NPIX1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NPIX1 in stpyfits namespace")
       
        try:
            val = hdul1[0].header['NPIX2']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NPIX2 in stpyfits namespace")

        self.assertEqual(hdul1[0].data.all(), np.array([[0,0,0,0,0,0,0,0,0,0],
                                                        [0,0,0,0,0,0,0,0,0,0],
                                                        [0,0,0,0,0,0,0,0,0,0],
                                                        [0,0,0,0,0,0,0,0,0,0],
                                                        [0,0,0,0,0,0,0,0,0,0],
                                                        [0,0,0,0,0,0,0,0,0,0],
                                                        [0,0,0,0,0,0,0,0,0,0],
                                                        [0,0,0,0,0,0,0,0,0,0],
                                                        [0,0,0,0,0,0,0,0,0,0],
                                                        [0,0,0,0,0,0,0,0,0,0]],
                                                        dtype=np.int32).all())

        self.assertEqual(hdul1[1].header['NAXIS'],2)
        self.assertEqual(hdul1[1].header['NAXIS1'],10)
        self.assertEqual(hdul1[1].header['NAXIS2'],10)
        self.assertEqual(hdul1[1].header['PIXVALUE'],2)
        
        try:
            val = hdul1[1].header['NPIX1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NPIX1 in stpyfits namespace")
       
        try:
            val = hdul1[1].header['NPIX2']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NPIX2 in stpyfits namespace")

        self.assertEqual(hdul1[1].data.all(), np.array([[2,2,2,2,2,2,2,2,2,2],
                                                        [2,2,2,2,2,2,2,2,2,2],
                                                        [2,2,2,2,2,2,2,2,2,2],
                                                        [2,2,2,2,2,2,2,2,2,2],
                                                        [2,2,2,2,2,2,2,2,2,2],
                                                        [2,2,2,2,2,2,2,2,2,2],
                                                        [2,2,2,2,2,2,2,2,2,2],
                                                        [2,2,2,2,2,2,2,2,2,2],
                                                        [2,2,2,2,2,2,2,2,2,2],
                                                        [2,2,2,2,2,2,2,2,2,2]],
                                                        dtype=np.int32).all())

        self.assertEqual(hdul2[0].header['NAXIS'],0)
        self.assertEqual(hdul2[0].header['NPIX1'],10)
        self.assertEqual(hdul2[0].header['NPIX2'],10)
        self.assertEqual(hdul2[0].header['PIXVALUE'],0)
        
        try:
            val = hdul2[0].header['NAXIS1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NAXIS1 in pyfits namespace")
       
        try:
            val = hdul2[0].header['NAXIS2']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NAXIS2 in pyfits namespace")

        self.assertEqual(hdul2[0].data, None)

        self.assertEqual(hdul2[1].header['NAXIS'],0)
        self.assertEqual(hdul2[1].header['NPIX1'],10)
        self.assertEqual(hdul2[1].header['NPIX2'],10)
        self.assertEqual(hdul2[1].header['PIXVALUE'],2)
        
        try:
            val = hdul2[1].header['NAXIS1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NAXIS1 in pyfits namespace")
       
        try:
            val = hdul2[1].header['NAXIS2']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NAXIS2 in pyfits namespace")

        hdul1.close()
        hdul2.close()
        os.remove('new.fits')

    def testHDUList__getitem__Method(self):
        """Test the __getitem__ method of st_HDUList in the stpyfits 
           namespace."""

        n = np.zeros(10)
        n = n + 1
  
        hdu = stpyfits.PrimaryHDU(n)
        hdu.header.update('PIXVALUE',1.,'constant pixel value',after='EXTEND')

        hdu.writeto('new.fits',clobber=True)

        hdul = stpyfits.open('new.fits')
        hdul1 = pyfits.open('new.fits')

        hdu = hdul[0]
        hdu1 = hdul1[0]

        self.assertEqual(hdu.header['NAXIS'],1)
        self.assertEqual(hdu.header['NAXIS1'],10)
        self.assertEqual(hdu.header['PIXVALUE'],1.0)
        
        try:
            val = hdu.header['NPIX1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NPIX1 in stpyfits namespace")
       
        self.assertEqual(hdu.data.all(), np.array(
                         [[1.,1.,1.,1.,1.,1.,1.,1.,1.,1.]],
                         dtype=np.float32).all())

        self.assertEqual(hdu1.header['NAXIS'],0)
        self.assertEqual(hdu1.header['NPIX1'],10)
        self.assertEqual(hdu1.header['PIXVALUE'],1.0)
        
        try:
            val = hdu1.header['NAXIS1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NAXIS1 in pyfits namespace")
       
        self.assertEqual(hdu1.data, None)

        hdul.close()
        hdul1.close()
        os.remove('new.fits')

    def testHDUListFlushMethod(self):
        """Test the flush method of HDUList in both the pyfits and stpyfits 
           namespace."""

        hdu = stpyfits.PrimaryHDU()
        hdu1 = stpyfits.ImageHDU()
        hdu.data = np.array([[0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0],
                             [0,0,0,0,0,0,0,0,0,0]], dtype=np.int32)
        hdu1.data = hdu.data+2
        hdu.header.update('BITPIX',32)
        hdu1.header.update('BITPIX',32)
        hdu.header.update('NAXIS',2)
        hdu.header.update('NAXIS1',10,'length of constant array axis 1',
                          after='NAXIS')
        hdu.header.update('NAXIS2',10,'length of constant array axis 2',
                          after='NAXIS1')
        hdu.header.update('PIXVALUE',0,'Constant pixel value',after='NAXIS2')
        hdu1.header.update('PIXVALUE',2,'Constant pixel value',after='GCOUNT')
        hdu1.header.update('NAXIS',2)
        hdu1.header.update('NAXIS1',10,'length of constant array axis 1',
                           after='NAXIS')
        hdu1.header.update('NAXIS2',10,'length of constant array axis 2',
                           after='NAXIS1')
        hdul = stpyfits.HDUList([hdu,hdu1])
        hdul.writeto('new.fits', clobber=True)

        hdul = stpyfits.open('new.fits', 'update')
        d = np.arange(10)
        d = d*0
        d = d+3
        hdul[0].data = d
        hdul.flush()
        hdul.close()

        tmpfile = open(self.tmpfilename,'w')
        sys.stdout = tmpfile
        stpyfits.info('new.fits')
        pyfits.info('new.fits')
        sys.stdout = sys.__stdout__
        tmpfile.close()
        tmpfile = open(self.tmpfilename,'r')
        output = tmpfile.readlines()
        tmpfile.close()
        os.remove(self.tmpfilename)

        self.assertEqual(output,["Filename: new.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU       6  (10,)         int32\n",
        "1                ImageHDU         8  (10, 10)      int32\n",
        "Filename: new.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU       6  ()            int32\n",
        "1                ImageHDU         8  ()            int32\n"])

        hdul1 = stpyfits.open('new.fits')
        hdul2 = pyfits.open('new.fits')

        self.assertEqual(hdul1[0].header['NAXIS'],1)
        self.assertEqual(hdul1[0].header['NAXIS1'],10)
        self.assertEqual(hdul1[0].header['PIXVALUE'],3)
        
        try:
            val = hdul1[0].header['NPIX1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NPIX1 in stpyfits namespace")
       
        self.assertEqual(hdul1[0].data.all(), np.array([[3,3,3,3,3,3,3,3,3,3]],
                                                        dtype=np.int32).all())

        self.assertEqual(hdul2[0].header['NAXIS'],0)
        self.assertEqual(hdul2[0].header['NPIX1'],10)
        self.assertEqual(hdul2[0].header['PIXVALUE'],3)
        
        try:
            val = hdul2[0].header['NAXIS1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NAXIS1 in pyfits namespace")
       
        self.assertEqual(hdul2[0].data, None)

        hdul1.close()
        hdul2.close()
        
        hdul3 = stpyfits.open('new.fits', 'update')
        d = np.arange(15)
        d = d*0
        d = d+4
        hdul3[0].data = d
        hdul3.close()      #Note that close calls flush

        tmpfile = open(self.tmpfilename,'w')
        sys.stdout = tmpfile
        stpyfits.info('new.fits')
        pyfits.info('new.fits')
        sys.stdout = sys.__stdout__
        tmpfile.close()
        tmpfile = open(self.tmpfilename,'r')
        output = tmpfile.readlines()
        tmpfile.close()
        os.remove(self.tmpfilename)

        self.assertEqual(output,["Filename: new.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU       6  (15,)         int32\n",
        "1                ImageHDU         8  (10, 10)      int32\n",
        "Filename: new.fits\n",
        "No.    Name         Type      Cards   Dimensions   Format\n",
        "0    PRIMARY     PrimaryHDU       6  ()            int32\n",
        "1                ImageHDU         8  ()            int32\n"])

        hdul1 = stpyfits.open('new.fits')
        hdul2 = pyfits.open('new.fits')

        self.assertEqual(hdul1[0].header['NAXIS'],1)
        self.assertEqual(hdul1[0].header['NAXIS1'],15)
        self.assertEqual(hdul1[0].header['PIXVALUE'],4)
        
        try:
            val = hdul1[0].header['NPIX1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NPIX1 in stpyfits namespace")
       
        self.assertEqual(hdul1[0].data.all(), np.array(
                         [[4,4,4,4,4,4,4,4,4,4,4,4,4,4,4]],
                         dtype=np.int32).all())

        self.assertEqual(hdul2[0].header['NAXIS'],0)
        self.assertEqual(hdul2[0].header['NPIX1'],15)
        self.assertEqual(hdul2[0].header['PIXVALUE'],4)
        
        try:
            val = hdul2[0].header['NAXIS1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NAXIS1 in pyfits namespace")
       
        self.assertEqual(hdul2[0].data, None)

        hdul1.close()
        hdul2.close()
        os.remove('new.fits')
        
    def testImageBaseHDU__getattr__Method(self):
        """Test the __getattr__ method of ImageBaseHDU in both the pyfits 
           and stpyfits namespace."""

        hdul = stpyfits.open('cdva2.fits')
        hdul1 = pyfits.open('cdva2.fits')

        hdu = hdul[0]
        hdu1 = hdul1[0]

        self.assertEqual(hdu.data.all(), np.array([[1,1,1,1,1,1,1,1,1,1],
                                                   [1,1,1,1,1,1,1,1,1,1],
                                                   [1,1,1,1,1,1,1,1,1,1],
                                                   [1,1,1,1,1,1,1,1,1,1],
                                                   [1,1,1,1,1,1,1,1,1,1],
                                                   [1,1,1,1,1,1,1,1,1,1],
                                                   [1,1,1,1,1,1,1,1,1,1],
                                                   [1,1,1,1,1,1,1,1,1,1],
                                                   [1,1,1,1,1,1,1,1,1,1],
                                                   [1,1,1,1,1,1,1,1,1,1]],
                                                   dtype=np.int32).all())
        self.assertEqual(hdu1.data, None)

        hdul.close()
        hdul1.close()

    def testImageBaseHDUWriteToMethod(self):
        """Test the writeto method of st_ImageBaseHDU in the stpyfits 
           namespace."""

        n = np.zeros(10)
        n = n + 1
  
        hdu = stpyfits.PrimaryHDU(n)
        hdu.header.update('PIXVALUE',1.,'constant pixel value',after='EXTEND')

        hdu.writeto('new.fits',clobber=True)

        hdul = stpyfits.open('new.fits')
        hdul1 = pyfits.open('new.fits')

        self.assertEqual(hdul[0].header['NAXIS'],1)
        self.assertEqual(hdul[0].header['NAXIS1'],10)
        self.assertEqual(hdul[0].header['PIXVALUE'],1.0)
        
        try:
            val = hdul[0].header['NPIX1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NPIX1 in stpyfits namespace")
       
        self.assertEqual(hdul[0].data.all(), np.array(
                         [[1.,1.,1.,1.,1.,1.,1.,1.,1.,1.]],
                         dtype=np.float32).all())

        self.assertEqual(hdul1[0].header['NAXIS'],0)
        self.assertEqual(hdul1[0].header['NPIX1'],10)
        self.assertEqual(hdul1[0].header['PIXVALUE'],1.0)
        
        try:
            val = hdul1[0].header['NAXIS1']
        except KeyError:
            pass
        else:
            self.fail(
             "expected a KeyError exception for NAXIS1 in pyfits namespace")
       
        self.assertEqual(hdul1[0].data, None)

        hdul.close()
        hdul1.close()
        os.remove('new.fits')

if __name__ == '__main__':
    unittest.main()
