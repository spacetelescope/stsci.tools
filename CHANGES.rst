.. _change_log:

======================
stsci.tools Change Log
======================

The version of stsci.tools can be identified using:

>>> import stsci.tools
>>> stsci.tools.__version__

The following notes provide some details on what has been revised for each
version in reverse chronological order (most recent version at the top
of the list).

4.0.1 (2021-08-31)
------------------

- Fixed unpickling of IrafPar. [#141]

4.0.0 (2021-08-12)
------------------

- Removed Python 2 support. Python 3.6 or later is now required. [#121]

- ``astropy`` 2 or later is now required. [#121]

- Improved compatibility of the ``bitmask`` module with ``numpy 1.21``. [#136]

3.6.0 (2019-07-17)
------------------

- Update stpyfits to be compatible with astropy v3.2.1 [#101]

- Fixes a crash in TEAL when loading MDRIZTAB parameters in astrodrizzle [#95]

- Use raw string in regex in irafutils.csvSplit [#85]
