.. _change_log:

=======================
stsci.tools change log
=======================

The version of stsci.tools can be identified using ::

> python
>>> import stsci.tools
>>> stsci.tools.__version__

The following notes provide some details on what has been revised for each
version in reverse chronological order (most recent version at the top
of the list).

3.6.0 (2019-07-17)
------------------

- Update stpyfits to be compatible with astropy v3.2.1 [#101]

- Fixes a crash in TEAL when loading MDRIZTAB parameters in astrodrizzle [#95]

- Use raw string in regex in irafutils.csvSplit [#85]
