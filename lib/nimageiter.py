from __future__ import generators

import types
import numarray as N


BUFSIZE = 1024*1000   # 1Mb cache size

__version__ = '0.4'


def ImageIter(imglist,bufsize=None,overlap=0,copy=0,updateSection = None):
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
    if bufsize == None: bufsize = BUFSIZE

    if type(imglist) != types.ListType:
        imgarr = imglist.data
        _imglen = 1
        single = 1
    else:
        imgarr = imglist[0].data
        _imglen = len(imglist)
        single = 0
        _outlist = []

    if len(imgarr.shape) == 1:
        if copy:
            if single:
                yield imgarr.copy(),None
            else:
                for img in imglist: _outlist.append(img.copy())
        else:
            yield imglist,None

    else:
        nrows = int(bufsize / (imgarr.itemsize() * imgarr.shape[1]))
        niter = int(imgarr.shape[0] / nrows) * nrows

        if copy:
            # Create a cache that will contain a copy of the input
                    # not just a view...
            if single:
                _cache = N.zeros((nrows,imgarr.shape[1]),type=imgarr.typecode())
            else:
                for img in imglist: _outlist.append(N.zeros((nrows,imgarr.shape[1]),type=imgarr.typecode()))

        for pix in range(0,niter+1,nrows):
            # overlap needs to be computed here
            # This allows the user to avoid edge effects when
            # convolving the returned image sections, and insures
            # that the last segment will always be returned with
            # overlap+1 rows.  
            if pix > 0: pix -= overlap
            _prange = pix+nrows
            if _prange > imgarr.shape[0]: _prange = imgarr.shape[0]
            if copy:
                if single:
                    _cache = imgarr[pix:_prange].copy()
                    yield _cache,(pix,_prange)
                    N.multiply(_cache,0.,_cache)
                else:
                    for img in xrange(len(imglist)): _outlist[img] = imglist[img][pix:_prange].copy()
                    yield _outlist,(pix,_prange)
                    for img in xrange(len(imglist)): N.multiply(_outlist[img],0.,_outlist[img])
            else:
                if single:
                    yield imgarr.section[pix:_prange,:],(pix,_prange)
                    #yield imgarr[pix:pix+nrows]
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
