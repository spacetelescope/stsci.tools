#   PROGRAM: numcombine.py
#   AUTOHOR: Christopher Hanley
#   DATE:    December 12, 2003
#   PURPOSE: --- We want to reproduce limited imcombine functionality ---
#
#   License: http://www.stsci.edu/resources/software_hardware/pyraf/LICENSE
#
#   HISTORY:
#      Version 0.0.0: Initial Development -- CJH -- 12/30/03
#      Version 0.1.0: Added the ability to apply an upper and lower threshold
#                     to the values of pixels used in the computation of the
#                     median image.  -- CJH -- 12/31/03
#      Version 0.2.0: Added error checking to ensure that for min/max clipping,
#                     more values are not being eliminated than are avilable in
#                     the image stack. Also, a list of masks can now be accepted
#                     as input and applied to the imput image list in addition to
#                     any internal clipping that occurs.-- CJH -- 01/12/04
#      Version 0.2.1: Added the nkeep parameter.  This parameter defines the minimum
#                     number of pixels to be kept in the calculation after clipping
#                     the high and low pixels.
#      Version 0.2.2: Added support for creating a "sum" array.  -- CJH -- 05/17/04
#      Version 0.2.3: Fixed syntax error in _createMaskList method.  -- CJH -- 06/01/04
#      Version 0.2.4: Removed diagnostic print statements.  -- CJH -- 06/28/04
#      Version 0.3.0: Added support for a computing a clipped minimum array. This is based upon
#                     the minimum function in numarray.images.combine that Todd Miller has
#                     implemented for numarray 1.3. -- CJH -- 03/30/05
#      Version 0.4.0: Modified numcombine to use the numerix interface.  This allows for the use
#                     of either the numarray or numpy array packages. -- CJH -- 08/18/06
#

# Import necessary modules
import numerixenv
numerixenv.check()

import numpy as n
import image

# Version number
__version__ = '0.4.0'

class numCombine:
    """ A lite version of the imcombine IRAF task"""

    def __init__(self,
        numarrayObjectList,         # Specifies a sequence of inputs arrays, which are nominally a stack of identically shaped images.
        numarrayMaskList = None,    #
        combinationType = "median", # What time of numarray object should be created?
        nlow = 0,                   # Number of low pixels to throw out of the median calculation
        nhigh = 0,                  # Number of high pixels to throw out of the median calculation
        nkeep = 1,                  # Minimun number of pixels to keep for a valid computation
        upper = None,               # Throw out values >= to upper in a median calculation
        lower = None                # Throw out values < lower in a median calculation
        ):

        # Convert the input arrays to the type of array used by the numerix layer
        for i in range(len(numarrayObjectList)):
            numarrayObjectList[i] = n.asarray(numarrayObjectList[i])
        
        if numarrayMaskList is not None:
            for i in range(len(numarrayMaskList)):
                numarrayMaskList[i] = n.asarray(numarrayMaskList[i])
                
        # define variables
        self.__numarrayObjectList = numarrayObjectList
        self.__numarrayMaskList = numarrayMaskList
        self.__combinationType = combinationType
        self.__nlow = nlow
        self.__nhigh = nhigh
        self.__nkeep = nkeep
        self.__upper = upper
        self.__lower = lower
        self.__masks = []

        # Get the number of objects to be combined
        self.__numObjs = len( self.__numarrayObjectList )

        # Simple sanity check to make sure that the min/max clipping doesn't throw out all of the pixels.
        if ( (self.__numObjs - (self.__nlow + self.__nhigh)) < self.__nkeep ):
            raise ValueError, "Rejecting more pixels than specified by the nkeep parameter!"

        # Create output numarray object
        self.combArrObj = n.zeros(self.__numarrayObjectList[0].shape,dtype=self.__numarrayObjectList[0].dtype )

        # Generate masks if necessary and combine them with the input masks (if any).
        self._createMaskList()

        # Combine the input images.
        if ( self.__combinationType.lower() == "median"):
            self._median()
        elif ( self.__combinationType.lower() == "mean" ):
            self._average()
        elif ( self.__combinationType.lower() == "sum" ):
            self._sum()
        elif ( self.__combinationType.lower() == "minimum"):
            self._minimum()
        else:
            print "Combination type not supported!!!"

    def _createMaskList(self):
        # Create the threshold masks
        if ( (self.__lower != None) or (self.__upper != None) ):
            __tmpMaskList =[]
            for imgobj in self.__numarrayObjectList:
                __tmpMask = image.threshhold(imgobj,low=self.__lower,high=self.__upper)
                __tmpMaskList.append(__tmpMask)
        else:
            __tmpMaskList = None

        # Combine the threshold masks with the input masks
        if ( (self.__numarrayMaskList == None) and (__tmpMaskList == None) ):
            self.__masks = None
        elif ( (self.__numarrayMaskList == None) and (__tmpMaskList != None) ):
            self.__masks = __tmpMaskList
        elif ( (self.__numarrayMaskList != None) and (__tmpMaskList == None) ):
            self.__masks = self.__numarrayMaskList
        else:
            for mask in xrange(len(self.__numarrayMaskList)):
                self.__masks.append(n.logical_or(__tmpMaskList[mask],self.__numarrayMaskList[mask]))
        del (__tmpMaskList)
        return None

    def _median(self):
        # Create a median image.
        #print "*  Creating a median array..."
        image.median(self.__numarrayObjectList,self.combArrObj,nlow=self.__nlow,nhigh=self.__nhigh,badmasks=self.__masks)
        return None

    def _average(self):
        # Create an average image.
        #print "*  Creating a mean array..."
        image.average(self.__numarrayObjectList,self.combArrObj,nlow=self.__nlow,nhigh=self.__nhigh,badmasks=self.__masks)
        return None

    def _sum(self):
        # Sum the images in the input list
        #print "* Creating a sum array..."
        for imgobj in self.__numarrayObjectList:
            n.add(self.combArrObj,imgobj,self.combArrObj)
    def _minimum(self):
        # Nominally computes the minimum pixel value for a stack of
        # identically shaped images
        try:
            # Try using the numarray.images.combine function "minimum" that is available as part of numarray version 1.3
            image.minimum(self.__numarrayObjectList,self.combArrObj,nlow=self.__nlow,nhigh=self.__nhigh,badmasks=self.__masks)
        except:
            # If numarray version 1.3 is not installed so that the "minimum" function is not available.  We will create our own minimum images but no clipping
            # will be available.
            errormsg =  "\n\n#################################################\n"
            errormsg += "#                                               #\n"
            errormsg += "# WARNING:                                      #\n"
            errormsg += "#  Cannot compute a clipped minimum because     #\n"
            errormsg += "#  NUMARRAY version 1.3 or later is not         #\n"
            errormsg += "#  installed.  A minimum image will be created  #\n"
            errormsg += "#  but no clipping will be used.                #\n"
            errormsg += "#                                               #\n"
            errormsg += "#################################################\n"
            print errormsg

            # Create the minimum image from the stack of input images.
            # Find the maximum pixel value for the image stack.
            _maxValue = -1e+9

            for imgobj in self.__numarrayObjectList:
                _newMax = imgobj.max()
                if (_newMax > _maxValue):
                    _maxValue = _newMax

            tmpList = []
            if (self.__numarrayMaskList != None):
                # Sum the weightMaskList elements
                __maskSum = self.__sumImages(self.__numarrayMaskList)

                # For each image, set pixels masked as "bad" to the "super-maximum" value.
                for imgobj in xrange(len(self.__numarrayObjectList)):
                    tmp = n.where(self.__numarrayMaskList[imgobj] == 1,_maxValue+1,self.__numarrayObjectList[imgobj])
                    tmpList.append(tmp)
            else:
                for imgobj in xrange(len(self.__numarrayObjectList)):
                  tmpList.append(imgobj)

            # Create the minimum image by computing a median array throwing out all but one of the pixels in the stack
            # starting from the top of the stack.
            image.median(tmpList,self.combArrObj,nlow=0,nhigh=self.__numObjs-1,badmasks=None)

            # If we have been given masks we need to reset the mask values to 0 in the image
            if (self.__numarrayMaskList != None):
                # Reset any pixl at _maxValue + 1 to 0.
                self.combArrObj = n.where(__maskSum == self.__numObjs, 0, self.combArrObj)            
                        

    def __sumImages(self,numarrayObjectList):
        """ Sum a list of numarray objects. """
        __sum = n.zeros(numarrayObjectList[0].shape,dtype=numarrayObjectList[0].dtype)
        for imgobj in numarrayObjectList:
            __sum += imgobj
        return __sum
