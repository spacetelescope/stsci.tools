#   PROGRAM: numcombine.py
#   AUTOHOR: Christopher Hanley
#   DATE:    December 12, 2003
#   PURPOSE: --- We want to reporduce limited imcombine functionality ---
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

# Import necessary modules
import numarray as n
import numarray.image.combine as nic

# Version number
__version__ = '0.2.3'

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
        self.combArrObj = n.zeros(self.__numarrayObjectList[0].shape,type=self.__numarrayObjectList[0].type() )

        # Generate masks if necessary and combine them with the input masks (if any).
        self._createMaskList()

        # Combine the input images.
        if ( self.__combinationType.lower() == "median"):
            self._median()
        elif ( self.__combinationType.lower() == "mean" ):
            self._average()
        elif ( self.__combinationType.lower() == "sum" ):
            self._sum()
        else:
            print "Combination type not supported!!!"

    def _createMaskList(self):
        # Create the threshold masks
        if ( (self.__lower != None) or (self.__upper != None) ):
            __tmpMaskList =[]
            for image in self.__numarrayObjectList:
                __tmpMask = nic.threshhold(image,low=self.__lower,high=self.__upper)
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
        nic.median(self.__numarrayObjectList,self.combArrObj,outtype=self.combArrObj.type(),nlow=self.__nlow,nhigh=self.__nhigh,badmasks=self.__masks)
        return None

    def _average(self):
        # Create an average image.
        #print "*  Creating a mean array..."
        nic.average(self.__numarrayObjectList,self.combArrObj,outtype=self.combArrObj.type(),nlow=self.__nlow,nhigh=self.__nhigh,badmasks=self.__masks)
        return None

    def _sum(self):
        # Sum the images in the input list
        #print "* Creating a sum array..."
        for image in self.__numarrayObjectList:
            n.add(self.combArrObj,image,self.combArrObj)
