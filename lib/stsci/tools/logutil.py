"""
A collection of utilities for handling output to standard out/err as well as
to file-based or other logging handlers through a single interface.
"""
import builtins
import inspect
import logging
import os
import sys
import threading

global_logging_started = False


# The global_logging system replaces the input builtin
# because:
#
#  1) It's the easiest way to capture the raw_input prompt and subsequent user
#     input to the log.
def global_logging_raw_input(prompt):
    retval = builtins._original_raw_input(prompt)
    if isinstance(sys.stdout, StreamTeeLogger):
        sys.stdout.log_orig(str(prompt) + retval, echo=False)
    return retval


class StreamTeeLogger(logging.Logger):
    """
    A Logger implementation that is meant to replace an I/O stream such as
    `sys.stdout`, `sys.stderr`, or any other stream-like object that supports a
    `write()` method and a `flush()` method.

    When `StreamTeeLogger.write` is called, the written strings are
    line-buffered, and each line is logged through the normal Python logging
    interface.  The `StreamTeeLogger` has two handlers:

     * The LogTeeHandler redirects all log messages to a logger with the same
       name as the module in which the `write()` method was called.  For
       example, if this logger is used to replace `sys.stdout`, all `print`
       statements in the module `foo.bar` will be logged to a logger called
       ``foo.bar``.

    * If the ``stream`` argument was provided, this logger also attaches a
      `logging.StreamHandler` to itself for the given ``stream``.  For example,
      if ``stream=sys.stdout`` then messages sent to this logger will be output
      to `sys.stdout`.  However, only messages created through the `write()`
      method call will re-output to the given stream.

    Parameters
    ----------
    name : string
        The name of this logger, as in `logging.Logger`

    level : int (optional)
        The minimum level at which to log messages sent to this logger; also
        used as the default level for messages logged through the `write()`
        interface (default: `logging.INFO`).

    stream : stream-like object (optional)
        The stream-like object (an object with `write()` and `flush()`
        methods) to tee to; should be the same file object being replaced (i.e.
        sys.stdout).  If `None` (the default) writes to this file will not be
        sent to a stream logger.

    See Also
    --------
    `EchoFilter` is a logger filter that can control which modules' output is
    sent to the screen via the `StreamHandler` on this logger.
    """

    def __init__(self, name, level=logging.INFO, stream=None):
        logging.Logger.__init__(self, name, level)
        self.__thread_local_ctx = threading.local()
        self.__thread_local_ctx.write_count = 0
        self.propagate = False
        self.buffer = ''

        self.stream = None
        self.set_stream(stream)

        self.addHandler(_LogTeeHandler())
        #self.errors = 'strict'
        #self.encoding = 'utf8'

    @property
    def encoding(self):
        if self.stream:
            try:
                return self.stream.encoding
            except AttributeError:
                pass

        # Default value
        return 'utf-8'

    @property
    def errors(self):
        if self.stream:
            try:
                return self.stream.errors
            except AttributeError:
                pass

        # Default value
        return 'strict'

    def set_stream(self, stream):
        """
        Set the stream that this logger is meant to replace.  Usually this will
        be either `sys.stdout` or `sys.stderr`, but can be any object with
        `write()` and `flush()` methods, as supported by
        `logging.StreamHandler`.
        """

        for handler in self.handlers[:]:
            if isinstance(handler, logging.StreamHandler):
                self.handlers.remove(handler)

        if stream is not None:
            stream_handler = logging.StreamHandler(stream)
            stream_handler.addFilter(_StreamHandlerEchoFilter())
            stream_handler.setFormatter(logging.Formatter('%(message)s'))
            self.addHandler(stream_handler)

        self.stream = stream

    def write(self, message):
        """
        Buffers each message until a newline is reached.  Each complete line is
        then published to the logging system through ``self.log()``.
        """

        self.__thread_local_ctx.write_count += 1

        try:
            if self.__thread_local_ctx.write_count > 1:
                return

            # For each line in the buffer ending with \n, output that line to
            # the logger
            msgs = (self.buffer + message).split('\n')
            self.buffer = msgs.pop(-1)
            for m in msgs:
                self.log_orig(m, echo=True)
        finally:
            self.__thread_local_ctx.write_count -= 1

    def flush(self):
        """
        Flushes all handlers attached to this logger; this includes flushing
        any attached stream-like object (e.g. `sys.stdout`).
        """

        for handler in self.handlers:
            handler.flush()

    def fileno(self):
        fd = None
        if self.stream:
            try:
                fd = self.stream.fileno()
            except:
                fd = None
        if fd is None:
            raise IOError('fileno() not defined for logger stream %r' %
                          self.stream)
        return fd

    def log_orig(self, message, echo=True):
        modname, path, lno, func = self.find_actual_caller()
        self.log(self.level, message,
                 extra={'orig_name': modname, 'orig_pathname': path,
                        'orig_lineno': lno, 'orig_func': func, 'echo': echo})

    def find_actual_caller(self):
        """
        Returns the full-qualified module name, full pathname, line number, and
        function in which `StreamTeeLogger.write()` was called.  For example,
        if this instance is used to replace `sys.stdout`, this will return the
        location of any print statement.
        """

        # Gleaned from code in the logging module itself...
        try:
            f = sys._getframe(1)
            ##f = inspect.currentframe(1)
        except Exception:
            f = None
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

            if modname == __name__:
                # Crawl back until the first frame outside of this module
                f = f.f_back
                continue

            rv = (modname, filename, f.f_lineno, co.co_name)
            break
        return rv


class EchoFilter:
    """
    A logger filter primarily for use with `StreamTeeLogger`.  Adding an
    `EchoFilter` to a `StreamTeeLogger` instances allows control over which
    modules' print statements, for example, are output to stdout.

    For example, to allow only output from the 'foo' module to be printed to
    the console:

    >>> stdout_logger = logging.getLogger('stsci.tools.logutil.stdout')
    >>> stdout_logger.addFilter(EchoFilter(include=['foo']))

    Now only print statements in the 'foo' module (or any sub-modules if 'foo'
    is a package) are printed to stdout.   Any other print statements are just
    sent to the appropriate logger.

    Parameters
    ----------
    include : iterable
        Packages or modules to include in stream output.  If set, then only the
        modules listed here are output to the stream.

    exclude : iterable
        Packages or modules to be excluded from stream output.  If set then all
        modules except for those listed here are output to the stream.  If both
        ``include`` and ``exclude`` are provided, ``include`` takes precedence
        and ``exclude`` is ignored.
    """

    def __init__(self, include=None, exclude=None):
        self.include = set(include) if include is not None else include
        self.exclude = set(exclude) if exclude is not None else exclude

    def filter(self, record):
        if ((self.include is None and self.exclude is None) or
            not hasattr(record, 'orig_name')):
            return True

        record_name = record.orig_name.split('.')
        while record_name:
            if self.include is not None:
                if '.'.join(record_name) in self.include:
                    return True
            elif self.exclude is not None:
                if '.'.join(record_name) not in self.exclude:
                    return True
                else:
                    break
            record_name.pop()

        record.echo = False
        return True


class LoggingExceptionHook:
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


def setup_global_logging():
    """
    Initializes capture of stdout/stderr, Python warnings, and exceptions;
    redirecting them to the loggers for the modules from which they originated.
    """

    global global_logging_started

    if global_logging_started:
        return

    orig_logger_class = logging.getLoggerClass()
    logging.setLoggerClass(StreamTeeLogger)
    try:
        stdout_logger = logging.getLogger(__name__ + '.stdout')
        stderr_logger = logging.getLogger(__name__ + '.stderr')
    finally:
        logging.setLoggerClass(orig_logger_class)

    stdout_logger.setLevel(logging.INFO)
    stderr_logger.setLevel(logging.ERROR)
    stdout_logger.set_stream(sys.stdout)
    stderr_logger.set_stream(sys.stderr)
    sys.stdout = stdout_logger
    sys.stderr = stderr_logger

    exception_logger = logging.getLogger(__name__ + '.exc')
    sys.excepthook = LoggingExceptionHook(exception_logger)

    logging.captureWarnings(True)

    rawinput = 'input'
    builtins._original_raw_input = getattr(builtins, rawinput)
    setattr(builtins, rawinput, global_logging_raw_input)

    global_logging_started = True


def teardown_global_logging():
    """Disable global logging of stdio, warnings, and exceptions."""

    global global_logging_started
    if not global_logging_started:
        return

    stdout_logger = logging.getLogger(__name__ + '.stdout')
    stderr_logger = logging.getLogger(__name__ + '.stderr')
    if sys.stdout is stdout_logger:
        sys.stdout = sys.stdout.stream
    if sys.stderr is stderr_logger:
        sys.stderr = sys.stderr.stream

    # If we still have an unhandled exception go ahead and handle it with the
    # replacement excepthook before deleting it
    exc_type, exc_value, exc_traceback = sys.exc_info()
    if exc_type is not None:
        sys.excepthook(exc_type, exc_value, exc_traceback)
    del exc_type
    del exc_value
    del exc_traceback

    del sys.excepthook
    logging.captureWarnings(False)

    rawinput = 'input'
    if hasattr(builtins, '_original_raw_input'):
        setattr(builtins, rawinput, builtins._original_raw_input)
        del builtins._original_raw_input

    global_logging_started = False


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


class _StreamHandlerEchoFilter(logging.Filter):
    """
    Filter used by the `logging.StreamHandler` internal to `StreamTeeLogger`;
    any message logged through `StreamTeeLogger.write()` has an ``echo=True``
    attribute attached to the `LogRecord`.  This ensures that the
    `StreamHandler` only logs messages with this ``echo`` attribute set to
    `True`.
    """

    def filter(self, record):
        if hasattr(record, 'echo'):
            return record.echo
        return False


class _LogTeeHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        logging.Handler.__init__(self, level)
        self.__thread_local_ctx = threading.local()
        self.__thread_local_ctx.logger_handle_counts = {}

    def emit(self, record):
        # Hand off to the global logger with the name same as the module of
        # origin for this record
        if not hasattr(record, 'orig_name'):
            return

        record = logging.LogRecord(record.orig_name, record.levelno,
                                   record.orig_pathname, record.orig_lineno,
                                   record.msg, record.args, record.exc_info,
                                   record.orig_func)
        record.origin = ""
        logger = logging.getLogger(record.name)
        if not logger.handlers:
            logger.addHandler(logging.NullHandler())

        counts = self.__thread_local_ctx.logger_handle_counts
        if logger.name in counts:
            counts[logger.name] += 1
        else:
            counts[logger.name] = 1
            if self._search_stack():
                return
        try:
            if counts[logger.name] > 1:
                return
            logger.handle(record)
        finally:
            counts[logger.name] -= 1

    def _search_stack(self):
        curr_frame = sys._getframe(3)
        ##curr_frame = inspect.currentframe(3)
        while curr_frame:
            if 'self' in curr_frame.f_locals:
                s = curr_frame.f_locals['self']
                if (isinstance(s, logging.Logger) and not
                    isinstance(s, StreamTeeLogger)):
                    return True
            curr_frame = curr_frame.f_back
        return False
