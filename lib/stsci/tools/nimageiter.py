"""

License: http://www.stsci.edu/resources/software_hardware/pyraf/LICENSE

"""
from __future__ import division # confidence medium
from __future__ import generators

import types
import numpy as N


BUFSIZE = 1024*1000   # 1Mb cache size

__version__ = '0.7'
__vdate__ = '25-July-2012'


def ImageIter(imglist,bufsize=BUFSIZE,overlap=0,copy=0,updateSection = None):
    """ Return image section for each image listed on input.
        The inputs can either be a single image or a list of them,
        with the return value matching the input type.
        All images in a list MUST have the same shape, though,
        in order for the iterator to scroll through them properly.

        The size of section gets defined by 'bufsize', while
        'copy' specifies whether to return an explicit copy
        of each input section or simply return views.
        The 'overlap' parameter provides a way of scrolling
        through the image with this many rows of overlap, with
        the default being no overlap at all.
    """
    if type(imglist) != list:
        imgarr = imglist.data
        imgarr = N.asarray(imgarr)
        _imglen = 1
        single = 1
    else:
        imgarr = imglist[0].data
        imgarr = N.asarray(imgarr)
        _imglen = len(imglist)
        single = 0
        _outlist = []
    _numrows = imgarr.shape[0]

    if len(imgarr.shape) == 1:
        if copy:
            if single:
                yield imgarr.copy(),None
            else:
                for img in imglist: _outlist.append(img.copy())
        else:
            yield imglist,None

    else:
        nrows = computeBuffRows(imgarr,bufsize=bufsize)
#       niter = int(imgarr.shape[0] / nrows) * nrows
        nbuff,nrows = computeNumberBuff(imgarr.shape[0],nrows,overlap)
        niter = nbuff*nrows

        if copy:
            # Create a cache that will contain a copy of the input
                    # not just a view...
            if single:
                _cache = N.zeros((nrows,imgarr.shape[1]),dtype=imgarr.dtype)
            else:
                for img in imglist: _outlist.append(N.zeros((nrows,imgarr.shape[1]),dtype=imgarr.dtype))

        for pix in range(0,niter+1,nrows):
            # overlap needs to be computed here
            # This allows the user to avoid edge effects when
            # convolving the returned image sections, and insures
            # that the last segment will always be returned with
            # overlap+1 rows.

            _prange = pix+nrows+overlap
            if _prange > _numrows: _prange = _numrows
            if pix == _prange: break

            if copy:
                if single:
                    _cache = imgarr[pix:_prange].copy()
                    yield _cache,(pix,_prange)
                    N.multiply(_cache,0.,_cache)
                else:
                    for img in range(len(imglist)): _outlist[img] = imglist[img][pix:_prange].copy()
                    yield _outlist,(pix,_prange)
                    for img in range(len(imglist)): N.multiply(_outlist[img],0.,_outlist[img])
            else:
                if single:
                    #yield imgarr.section[pix:_prange,:],(pix,_prange)
                    yield imgarr[pix:_prange],(pix,_prange)
                else:
                    for hdu in imglist:
                        #_outlist.append(imglist[img][pix:pix+nrows])
                        _outlist.append(hdu.section[pix:_prange,:])
                    yield _outlist,(pix,_prange)
                    # This code is inserted to copy any values changed
                    # in the image sections back into the original image.
                    if (updateSection != None):
                        #for _index in xrange(len(_outlist)):
                        imglist[updateSection][pix:_prange] = _outlist[updateSection]
                    del _outlist
                    _outlist = []

def computeBuffRows(imgarr,bufsize=BUFSIZE):
    """ Function to compute the number of rows from the
        input array that fits in the allocated memory given
        by the bufsize.
    """
    imgarr = N.asarray(imgarr)
    buffrows = int(bufsize / (imgarr.itemsize * imgarr.shape[1]))
    return buffrows

def computeNumberBuff(numrows, buffrows, overlap):
    """ Function to compute the number of buffer sections
        that will be used to read the input image given the
        specified overlap.
    """
    nbuff = _computeNbuff(numrows, buffrows, overlap)
    niter = 1 + int(nbuff)
    totalrows = niter * buffrows
    # We need to account for the case where the number of
    # iterations ends up being greater than needed due to the
    # overlap.
    #if totalrows > numrows: niter -= 1
    lastbuff = numrows - (niter*(buffrows-overlap))

    if lastbuff < overlap+1 and nbuff > 1:
        good = False
        while not good:
            if buffrows > overlap+1:
                buffrows -= 1

                nbuff = _computeNbuff(numrows, buffrows, overlap)
                niter = 1 + int(nbuff)
                totalrows = niter * (buffrows - overlap)
                lastbuff = numrows - (niter*(buffrows-overlap))
                if lastbuff > overlap + 1:
                    good = True
            else:
                good = True
    return niter,buffrows

def _computeNbuff(numrows,buffrows,overlap):

    if buffrows > numrows:
        nbuff = 1
    else:
        overlaprows = buffrows - overlap
        rowratio = (numrows - overlaprows)/(1.0*buffrows)
        nbuff = (numrows - overlaprows+1)/(1.0*overlaprows)
    return nbuff

def FileIter(filelist,bufsize=BUFSIZE,overlap=0):
    """ Return image section for each image listed on input, with
        the object performing the file I/O upon each call to the
        iterator.

        The inputs can either be a single image or a list of them,
        with the return value matching the input type.
        All images in a list MUST have the same shape, though,
        in order for the iterator to scroll through them properly.

        The size of section gets defined by 'bufsize'.
        The 'overlap' parameter provides a way of scrolling
        through the image with this many rows of overlap, with
        the default being no overlap at all.
    """
    if type(filelist) != list:
        imgarr = filelist.data
        imgarr = N.asarray(imgarr)
        _imglen = 1
        single = 1
    else:
        imgarr = filelist[0].data
        imgarr = N.asarray(imgarr)
        _imglen = len(filelist)
        single = 0
        _outlist = []
    _numrows = imgarr.shape[0]

    if len(imgarr.shape) == 1:
        # This needs to be generalized to return pixel ranges
        # based on bufsize, just like with 2-D arrays (images).
        yield filelist,None

    else:
        nrows = computeBuffRows(imgarr,bufsize=bufsize)
#       niter = int(imgarr.shape[0] / nrows) * nrows
        nbuff,nrows = computeNumberBuff(imgarr.shape[0],nrows,overlap)
        niter = nbuff * nrows

        for pix in range(0,niter+1,nrows-overlap):
            # overlap needs to be computed here
            # This allows the user to avoid edge effects when
            # convolving the returned image sections, and insures
            # that the last segment will always be returned with
            # overlap+1 rows.
            _prange = pix+nrows
            if _prange > _numrows: _prange = _numrows
            if pix >= _prange: break
            if single:
                yield imgarr[pix:_prange],(pix,_prange)
            else:
                for hdu in filelist:
                    _outlist.append(hdu[pix:_prange])
                yield _outlist,(pix,_prange)
                del _outlist
                _outlist = []
