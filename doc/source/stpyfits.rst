********
STPyFITS
********
The ``stpyfits`` module serves as a layer on top of `astropy.io.fits` to support the use of single-valued arrays in extensions using the ``NPIX``/``PIXVALUE`` convention developed at STScI. The standard `astropy.io.fits` module implements the strict FITS conventions, and these single-valued arrays are not part of the FITS standard.

.. automodule:: stsci.tools.stpyfits
   :members: ConstantValuePrimaryHDU, ConstantValueImageHDU
   :show-inheritance:
