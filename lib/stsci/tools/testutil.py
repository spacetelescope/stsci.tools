from __future__ import division, print_function
import math, os, sys, time
import unittest
import numpy as N
""" This module extends the built-in unittest capabilities to facilitate
performing floating point comparisons on scalars and numpy arrays. It also
provides functions that automate building a test suite from all tests
present in the module, and running the tests in standard or debug mode.

To use this module, import it along with unittest [QUESTION: should this
module import everything from unittest into its namespace to make life
even easier?]. Subclass test cases from testutil.FPTestCase instead of
unittest.TestCase. Call testall or debug from this module:

import testutil

class FileTestCase(testutil.FPTestCase):
    def setUp(self):
        assorted_test_setup

    def testone(self):
        self.assertEqual(1,2)

    def testtwo(self):
        self.assertApproxNumpy(arr1,arr2,accuracy=1e-6)

    def tearDown(self):
        assorted_test_teardown

if __name__ == '__main__':
    if 'debug' in sys.argv:
        testutil.debug(__name__)
    else:
        testutil.testall(__name__,2)

To run the tests in normal mode from the shell, then do the following:
    python my_module.py
It will run all tests, success or failure, and print a summary of the results.

To run the tests in debug mode from the shell, do the following:
    python -i my_module.py debug
    >>> import pdb
    >>> pdb.pm()
In debug mode, it will run until it encounters the first failed test, then
stop. Thus if you run with the -i switch, you can then import pdb and
proceed with the usual debugger commands.

If you prefer to run your tests from within the python interpreter,
you may import this module and call its testall() and debug() functions
explicitly. The modules you are testing must be visible in your sys.path.

>>>import testutil as U
>>> U.testall('ui_test')

"""

class LogTestCase(unittest.TestCase):
   """Override the .run() method to do some logging"""
   def run(self, result=None):
        if result is None: result = self.defaultTestResult()
        result.startTest(self)
        testMethod = getattr(self, self._testMethodName)
        try:
            try:
                self.setUp()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._exc_info())
                self.log('E')
                return

            ok = False
            try:
                testMethod()
                ok = True
                self.log("P")
            except self.failureException:
                result.addFailure(self, self._exc_info())
                self.log("F")
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._exc_info())
                self.log("E")

            try:
                self.tearDown()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._exc_info())
                ok = False
            if ok: result.addSuccess(self)
        finally:
            result.stopTest(self)

   def log(self,status,name=None):
      """Creates a log file containing the test name, status,and timestamp,
      as well as any attributes in the tda and tra dictionaries if present.
      Does not yet support fancy separating of multi-line items."""
      if name is None:
         try:
            name=self.name
         except AttributeError:
            name=self.id()
      try:
         f=open(name+'.log','w')
      except IOError as e:
         print("Error opening log file: %s"%e.strerror)
         print("***No Logging Performed***")
         return

      f.write("%s:: Name=%s\n"%(name,name))
      f.write("%s:: Status=%s\n"%(name,status))
      f.write("%s:: Time=%s\n"%(name,time.asctime()))
      try:
         for k in self.tda:
            f.write("%s:: tda_%s=%s\n"%(name,str(k),str(self.tda[k])))
      except AttributeError:
         pass

      try:
         for k in self.tra:
            f.write("%s:: tra_%s=%s\n"%(name,str(k),str(self.tra[k])))
      except AttributeError:
         pass

      if status == 'E':
          f.write("%s:: tra_Trace=%s\n"%(name,str(self._exc_info())))

      f.write("END\n")
      f.close()





class FPTestCase(unittest.TestCase):
    ''' Base class to hold some functionality related to floating-point
    precision and array comparisons'''

    def assertApproxFP(self, testvalue, expected, accuracy=1.0e-5):
        ''' Floating point comparison  '''
        result = math.fabs((testvalue - expected) / expected)
        self.failUnless(result <= accuracy,"test: %g, ref: %g"%(testvalue,expected))

    def assertApproxNumpy(self, testarray, expected, accuracy=1.0e-5):
        ''' Floating point array comparison '''
        result=N.abs(testarray-expected)/expected
        self.failUnless(N.alltrue(result <= accuracy))

    def assertEqualNumpy(self, testarray, expected):
        ''' Identical FP array comparison '''
        self.failUnless(N.alltrue(testarray == expected))

class LogTextRunner(unittest.TextTestRunner):
    """ Redefines the .run() method to call a .log() method on the test
    when it is complete. """

    def run(self, test):
        "Run the given test case or test suite."
        result = self._makeResult()
        startTime = time.time()
        test(result)
        stopTime = time.time()
        timeTaken = stopTime - startTime
        result.printErrors()
        self.stream.writeln(result.separator2)
        run = result.testsRun
        self.stream.writeln("Ran %d test%s in %.3fs" %
                            (run, run != 1 and "s" or "", timeTaken))
        self.stream.writeln()
        if not result.wasSuccessful():
            self.stream.write("FAILED (")
            failed, errored = list(map(len, (result.failures, result.errors)))
            if failed:
                self.stream.write("failures=%d" % failed)
                test.log("F")
            if errored:
                if failed: self.stream.write(", ")
                self.stream.write("errors=%d" % errored)
                test.log("E")
            self.stream.writeln(")")
        else:
            self.stream.writeln("OK")
            test.log("P")

        return result

def buildsuite(module):
    """Builds a test suite containing all tests found in the module.
    Returns the suite."""
    M = __import__(module)
    suite = unittest.defaultTestLoader.loadTestsFromModule(M)
    return suite

def debug(module):
    """ Build the test suite, then run in debug mode, which allows for postmortems"""
    buildsuite(module).debug()

def testall(module,verb=0):
    """ Build and run the suite through the testrunner. Verbosity level
    defaults to quiet but can be set to 2 to produce a line as it runs
    each test. A summary of the number of tests run, errors, and failures
    is always printed at the end."""
    result=unittest.TextTestRunner(verbosity=verb).run(buildsuite(module))
    return result

def testlog(module,verb=0):
    result=LogTextRunner(verbosity=verb).run(buildsuite(module))
    return result

def dump_file(fname, hdrwidth=80):
    """ Convenience function to dump a named file to the stdout, with
    an optional header listing the filename.  This is easy to do without
    a convenience function like this, but having one reduces code in the XML
    test files. """
    assert os.path.exists(fname), "dump_file could not find: "+fname
    sys.stdout.flush()
    if hdrwidth>0:
        print("")
        print("="*hdrwidth)
        print(fname+':')
        print("="*hdrwidth)
    f = open(fname, 'r')
    for line in f:
        print(line.rstrip())
    f.close()

def dump_all_log_files(hdrwidth=80):
    """ Convenience function to dump all *.log files in cwd to the stdout,
    with an optional header listing each filename. See dump_file. """
    import glob
    flist = glob.glob('*.log')
    for f in flist:
        dump_file(f, hdrwidth=hdrwidth)
