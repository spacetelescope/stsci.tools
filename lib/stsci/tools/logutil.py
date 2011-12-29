"""
A collection of utilities for handling output to standard out/err as well as
to file-based or other logging handlers through a single interface.
"""


import inspect
import logging
import os
import sys


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


logging_started = False


class LogFileTee(object):
    """
    File-like object meant to replace stdout/stderr or any other file-like
    object so that it writes to a given logger instead.

    Parameters
    ----------
    fileobj : file-like object (optional)
        The file-like object to tee to; should be the same file object being
        replaced (i.e. sys.stdout).  If `None` (the default) all writes to this
        file will be sent to the logger only.

    logger : string, logger (optional)
        A `logging.Logger` object or the name of a logger that can be used with
        `logging.getLogger`.  Uses the root logger by default.

    level : int (optional)
        The log level with which to log all messages sent to this file.  Uses
        `logging.INFO` by default.
    """

    def __init__(self, fileobj=None, logger=None, level=logging.INFO):
        self.fileobj = fileobj

        if isinstance(logger, basestring):
            self.logger = logging.getLogger(logger)
        elif isinstance(logger, logging.Logger):
            self.logger = logger
        else:
            raise TypeError('logger must be a string or logging.Logger '
                            'object; got %r' % logger)

        if not self.logger.handlers:
            self.logger.addHandler(logging.NullHandler())

        self.level = level
        self.buffer = StringIO()

    def write(self, message):
        if self.fileobj is not None:
            self.fileobj.write(message)

        self.buffer.write(message)
        # For each line in the buffer ending with \n, output that line to the
        # logger
        self.buffer.seek(0)
        for line in self.buffer:
            if line[-1] != '\n':
                self.buffer.truncate(0)
                self.buffer.write(line)
                return
            else:
                caller_info = self.find_caller()

                self.logger.log(self.level, line.rstrip(),
                                extra={'actual_caller': caller_info})
        self.buffer.truncate(0)

    def flush(self):
        if self.fileobj is not None:
            self.fileobj.flush()

        for handler in self.logger.handlers:
            handler.flush()

    def find_caller(self):
        # Gleaned from code in the logging module itself...
        f = inspect.currentframe(1)
        # On some versions of IronPython, currentframe() returns None if
        # IronPython isn't run with -X:Frames.
        if f is not None:
            f = f.f_back
        rv = "(unknown module)", "(unknown file)", 0, "(unknown function)"
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            mod = inspect.getmodule(f)
            if mod is None:
                modname = '__main__'
            else:
                modname = mod.__name__
            rv = (modname, co.co_filename, f.f_lineno, co.co_name)
            break
        return rv


class LogTeeHandler(logging.Handler):
    def emit(self, record):
        if not hasattr(record, 'actual_caller'):
            return
        modname, path, lno, func = record.actual_caller
        if modname == '(unknown module)':
            modname = 'root'
        record.name = modname
        record.pathname = path
        try:
            record.filename = os.path.basename(path)
            record.module = os.path.splitext(record.filename)[0]
        except (TypeError, ValueError, AttributeError):
            record.filename = path
            record.module = 'Unknown module'
        record.lineno = lno
        record.funcName = func

        # Hand off to the global logger with the name same as the module of
        # origin for this record
        logger = logging.getLogger(modname)
        if not logger.handlers:
            logger.addHandler(logging.NullHandler())
        logger.handle(record)


class LoggingExceptionHook(object):
    def __init__(self, logger, level=logging.ERROR):
        self._oldexcepthook = sys.excepthook
        self.logger = logger
        self.level = level
        if not self.logger.handlers:
            self.logger.addHandler(logging.NullHandler())

    def __del__(self):
        try:
            try:
                sys.excepthook = self._oldexcepthook
            except AttributeError:
                sys.excepthook = sys.__excepthook__
        except AttributeError:
            pass

    def __call__(self, exc_type, exc_value, traceback):
        self.logger.log(self.level, 'An unhandled exception ocurred:',
                        exc_info=(exc_type, exc_value, traceback))
        self._oldexcepthook(exc_type, exc_value, traceback)


def setup_logging():
    """
    Initializes the root logger to capture console output, Python warnings,
    and Numpy warnings in a sensible manner.
    """

    global logging_started

    if logging_started:
        return

    stdout_logger = logging.getLogger(__name__ + '.stdout')
    stdout_logger.addHandler(LogTeeHandler())
    stdout_logger.setLevel(logging.INFO)
    sys.stdout = LogFileTee(sys.stdout, logger=stdout_logger)

    exception_logger = logging.getLogger(__name__ + '.exc')
    sys.excepthook = LoggingExceptionHook(exception_logger)

    logging.captureWarnings(True)

    logging_started = True


def teardown_logging():
    global logging_started
    if not logging_started:
        return

    sys.stdout = sys.stdout.fileobj
    del sys.excepthook
    logging.captureWarnings(False)

    logging_started = False


# Cribbed, with a few tweaks from Tom Aldcroft at
# http://www.astropython.org/snippet/2010/2/Easier-python-logging
def create_logger(name, format='%(levelname)s: %(message)s', datefmt=None,
                  stream=None, level=logging.INFO, filename=None, filemode='w',
                  filelevel=None, propagate=True):
    """
    Do basic configuration for the logging system. Similar to
    logging.basicConfig but the logger ``name`` is configurable and both a file
    output and a stream output can be created. Returns a logger object.

    The default behaviour is to create a logger called ``name`` with a null
    handled, and to use the "%(levelname)s: %(message)s" format string, and add
    the handler to the ``name`` logger.

    A number of optional keyword arguments may be specified, which can alter
    the default behaviour.

    :param name: Logger name
    :param format: handler format string
    :param datefmt: handler date/time format specifier
    :param stream: add a StreamHandler using ``stream``
                    (None disables the stream, default=None)
    :param level: logger level (default=INFO).
    :param filename: add a FileHandler using ``filename`` (default=None)
    :param filemode: open ``filename`` with specified filemode ('w' or 'a')
    :param filelevel: logger level for file logger (default=``level``)
    :param propagate: propagate message to parent (default=True)

    :returns: logging.Logger object
    """

    # Get a logger for the specified name
    logger = logging.getLogger(name)
    logger.setLevel(level)
    fmt = logging.Formatter(format, datefmt)
    logger.propagate = propagate

    # Remove existing handlers, otherwise multiple handlers can accrue
    for hdlr in logger.handlers:
        logger.removeHandler(hdlr)

    # Add handlers. Add NullHandler if no file or stream output so that
    # modules don't emit a warning about no handler.
    if not (filename or stream):
        logger.addHandler(logging.NullHandler())

    if filename:
        hdlr = logging.FileHandler(filename, filemode)
        if filelevel is None:
            filelevel = level
        hdlr.setLevel(filelevel)
        hdlr.setFormatter(fmt)
        logger.addHandler(hdlr)

    if stream:
        hdlr = logging.StreamHandler(stream)
        hdlr.setLevel(level)
        hdlr.setFormatter(fmt)
        logger.addHandler(hdlr)

    return logger


if sys.version_info[:2] < (2, 7):
    # We need to backport logging.captureWarnings
    import warnings

    PY26 = sys.version_info[:2] >= (2, 6)

    logging._warnings_showwarning = None

    class NullHandler(logging.Handler):
        """
        This handler does nothing. It's intended to be used to avoid the "No
        handlers could be found for logger XXX" one-off warning. This is
        important for library code, which may contain code to log events. If a
        user of the library does not configure logging, the one-off warning
        might be produced; to avoid this, the library developer simply needs to
        instantiate a NullHandler and add it to the top-level logger of the
        library module or package.
        """

        def handle(self, record):
            pass

        def emit(self, record):
            pass

        def createLock(self):
            self.lock = None

    logging.NullHandler = NullHandler


    def _showwarning(message, category, filename, lineno, file=None,
                     line=None):
        """
        Implementation of showwarnings which redirects to logging, which will
        first check to see if the file parameter is None. If a file is
        specified, it will delegate to the original warnings implementation of
        showwarning. Otherwise, it will call warnings.formatwarning and will
        log the resulting string to a warnings logger named "py.warnings" with
        level logging.WARNING.
        """

        if file is not None:
            if logging._warnings_showwarning is not None:
                if PY26:
                    _warnings_showwarning(message, category, filename, lineno,
                                          file, line)
                else:
                    # Python 2.5 and below don't support the line argument
                    _warnings_showwarning(message, category, filename, lineno,
                                          file)
        else:
            if PY26:
                s = warnings.formatwarning(message, category, filename, lineno,
                                           line)
            else:
                s = warnings.formatwarning(message, category, filename, lineno)

            logger = logging.getLogger("py.warnings")
            if not logger.handlers:
                logger.addHandler(NullHandler())
            logger.warning("%s", s)
    logging._showwarning = _showwarning
    del _showwarning

    def captureWarnings(capture):
        """
        If capture is true, redirect all warnings to the logging package.
        If capture is False, ensure that warnings are not redirected to logging
        but to their original destinations.
        """
        if capture:
            if logging._warnings_showwarning is None:
                logging._warnings_showwarning = warnings.showwarning
                warnings.showwarning = logging._showwarning
        else:
            if logging._warnings_showwarning is not None:
                warnings.showwarning = logging._warnings_showwarning
                logging._warnings_showwarning = None
    logging.captureWarnings = captureWarnings
    del captureWarnings
