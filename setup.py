

# We can't import this because we are not installed yet, so
# exec it instead.  We only want it to initialize itself,
# so we don't need to keep the symbol table.

f=open("lib/stsci_distutils_hack.py","r")
exec f in { }
f.close()


from distutils.core import setup

from defsetup import setupargs, pkg

setup(
    name =              pkg,
    packages =          [ pkg ],
    package_dir=        { pkg : 'lib' },
    **setupargs
    )
