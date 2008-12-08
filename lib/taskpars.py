""" Contains the TaskPars class and any related functions.

$Id: taskpars.py 1 2008-11-04 15:45:32Z sontag $
"""

class TaskPars:
    """ This represents a task's collection of configurable parameters.
    This class is meant to be mostly abstract, though there is some
    functionality included which could be common to most derived classes.
    This also serves to document the interface which must be met for EPAR.
    """

    def getName(self, *args, **kw):
        """ Returns the string name of the task. """
        raise RuntimeError("Bug: class TaskPars is not to be used directly")

    def getPkgname(self, *args, **kw):
        """ Returns the string name of the package, if applicable. """
        raise RuntimeError("Bug: class TaskPars is not to be used directly")

    def getParList(self, *args, **kw):
        """ Returns a list of parameter objects. """
        raise RuntimeError("Bug: class TaskPars is not to be used directly")

    def getDefaultParList(self, *args, **kw):
        """ Returns a list of parameter objects with default values set. """
        raise RuntimeError("Bug: class TaskPars is not to be used directly")

    def setParam(self, *args, **kw):
        """ Allows one to set the value of a single parameter. """
        raise RuntimeError("Bug: class TaskPars is not to be used directly")

    def getFilename(self, *args, **kw):
        """ Returns the string name of any associated config/parameter file. """
        raise RuntimeError("Bug: class TaskPars is not to be used directly")

    def saveParList(self, *args, **kw):
        """ Allows one to save the entire set to a file. """
        raise RuntimeError("Bug: class TaskPars is not to be used directly")

    def run(self, *args, **kw):
        """ Runs the task with the known parameters. """
        raise RuntimeError("Bug: class TaskPars is not to be used directly")

    def canPerformValidation(self):
        """ Returns bool.  If True, expect tryValue() to be called next. """
        return False

    # also, eparam, lParam, tParam, dParam ?
