#
# $HeadURL$
# $Rev$
#
# Implements setup.py code common to many of our packages.
#
# The new standard stsci module setup.py is just 
#
#   import pytools.stsci_distutils_hack
#   pytools.stsci_distutils_hack.run( pytools_version = "XX" )
#
# where XX is the version of pytools you expect for the install to work
#

########
#
# actually perform the install
#

def run( pytools_version = None ) :

    import pytools

    # bug: should use distutils version comparator to perform ">" comparisons
    if pytools_version and ( pytools.__version__ != pytools_version ) :
        print "wrong version of pytools!"
        print "have ",pytools.__version__ 
        print "want ",pytools_version
        import sys
        sys.exit(1)

    from distutils.core import setup

    from defsetup import setupargs, pkg

    setup(
        name =              pkg,
        packages =          [ pkg ],
        package_dir=        { pkg : 'lib' },

        **setupargs

        )



########
#
# This part fixes install_data to put data files in the same directory
# with the python library files, which is where our packages want
# them.
#
# This is essentially "smart_install_data" as used in the old
# setup.py files, except that it also understands wildcards
# and os-specific paths.  This means the module author can
# ask for data files with 
#       "data/generic/*" 
# instead of 
#       glob.glob(os.path.join('data', 'generic', '*'))


import os
import glob

import distutils.util

import distutils.command.install_data

o =  distutils.command.install_data.install_data

# same trick as smart_install_data used: save the old run() method and
# insert our own run method ahead of it

o.old_run = o.run

def new_run ( self ) :
        # We want our data files in the directory with the library files
        install_cmd = self.get_finalized_command('install')
        self.install_dir = getattr(install_cmd, 'install_lib')


        # self.data_files is a list of
        #       ( destination_directory, [ source_file, source_file, source_file ] )
        #
        # We want to do wildcard expansion on all the file names.
        #
        l = [ ]
        for f in self.data_files :
            ( dest_dir, files ) = f
            fl = [ ]
            for ff in files :
                ff = distutils.util.convert_path(ff)
                ff = glob.glob(ff)
                fl.extend(ff)
            dest_dir = distutils.util.convert_path(dest_dir)
            l.append( ( dest_dir, fl ) )
        self.data_files = l

        # now use the original run() function to finish
        return distutils.command.install_data.install_data.old_run(self)

o.run = new_run


########
#
# Implements "python setup.py install --place=dir"
#
# This replaces --local from earlier stsci_python releases.  The
# flag is different because it doesn't quite do the same thing.
#
# --place=$dir means that
#   scripts go into $dir/bin
#   python code goes into $dir/lib
#
# This is a less complicated structure than you get from --prefix and --home.

import distutils.command.install

# same trick as smart_install_data used: save the old run() method and
# insert our own run method ahead of it

o = distutils.command.install.install
o.old_finalize_unix  = o.finalize_unix
o.old_finalize_other = o.finalize_other

# INSTALL_SCHEMES are effectively a list of where to put different kinds
# of files.  It exists so you can have complex structures like what 
# --prefix does.  We want a simpler one, so here it is.
distutils.command.install.INSTALL_SCHEMES['unix_place'] = {
        'purelib': '$base/lib',
        'platlib': '$base/lib',
        'headers': '$base/include',
        'scripts': '$base/bin',
        'data'   : '$base/lib',
    }


def new_finalize_unix(self) :
    # this is handled just like --home, but with a different scheme name
    # see finalize_unix() in distutils/command/install.py
    if self.place :
        self.install_base = self.install_platbase = self.place
        self.select_scheme("unix_place")
        return
    self.old_finalize_unix()

def new_finalize_other(self) :
    # need to think about what to do for windows
    # (distutils says that macs come through here, but macs use finalize_unix)
    self.old_finalize_unix()

o.finalize_unix  = new_finalize_unix
o.finalize_other = new_finalize_other

# to make a new option "--foo", you need to create a variable named
# "foo" in the object and add an entry to user_options[]
o.place = None
o.user_options.append( ( "place=", None, "Specify place to install" ) )


########

