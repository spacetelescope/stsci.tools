"""

License: http://www.stsci.edu/resources/software_hardware/pyraf/LICENSE

"""
from __future__ import absolute_import, division, generators # confidence medium

from . import numerixenv
numerixenv.check()

import numpy as N

BUFSIZE = 1024*1000   # 1Mb cache size

__version__ = '0.2'


def ImageIter(imgarr,bufsize=None,overlap=0,copy=0):

    imgarr = N.asarray(imgarr)
    
    if bufsize == None: bufsize = BUFSIZE

    if len(imgarr.shape) == 1:
        if copy:
            yield imgarr.copy()
        else:
            yield imgarr
    else:
        nrows = int(bufsize / (imgarr.itemsize * imgarr.shape[1]))    
        niter = int(imgarr.shape[0] / nrows) * nrows
    
        if copy:
                # Create a cache that will contain a copy of the input
                    # not just a view...
                    _cache = N.zeros((nrows,imgarr.shape[1]),dtype=imgarr.dtype.char)

        for pix in range(0,niter+1,nrows):
                    if copy:
                            _cache = imgarr[pix:pix+nrows].copy()
                            yield _cache
                    else:
                            yield imgarr[pix:pix+nrows]
                    if copy:
                            _cache *= 0

                    pix -= overlap  
             
