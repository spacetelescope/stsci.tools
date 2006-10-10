from distutils.core import setup
import sys, os.path

if not hasattr(sys, 'version_info') or sys.version_info < (2,3,0,'alpha',0):
    raise SystemExit, "Python 2.3 or later required to build pytools."

args = sys.argv[:]

for a in args:
    if a.startswith('--local='):
        dir = os.path.abspath(a.split("=")[1])
        sys.argv.extend([
                "--install-lib="+dir,
                "--install-scripts=%s" % dir])
        args.remove(a)
        sys.argv.remove(a)

setup(name = "pytools",
      version = "2.0.0",
      description = "General Use Python Tools",
      author = "Warren Hack, Christopher Hanley",
      author_email = "help@stsci.edu",
      license = "http://www.stsci.edu/resources/software_hardware/pyraf/LICENSE",
      platforms = ["Linux","Solaris","Mac OS X","Win"],
      py_modules = ['imageiter', 'nimageiter', 'numcombine',
                    'versioninfo', 'makewcs', 'irafglob',
                    'parseinput','iterfile', 'readgeis',
                    'xyinterp', 'fileutil', 'wcsutil'],
      package_dir={'':'lib'},
      scripts = ['lib/fitsdiff.py']
      )



