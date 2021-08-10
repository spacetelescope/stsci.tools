"""A module that provides functions for manipulating bitmasks and data quality
(DQ) arrays.

"""
import warnings
import numpy as np
from astropy.utils import deprecated

__version__ = '1.2.0'
__vdate__ = '10-August-2021'
__author__ = 'Mihai Cara'

# Revision history:
# 0.1.0 (29-March-2015) - initial release based on code from stsci.skypac
# 0.1.1 (21-February-2017) - documentation typo fix
# 0.2.0 (23-February-2017) - performance and stability improvements. Changed
#       default output mask type from numpy.uint8 to numpy.bool_.
# 1.0.0 (16-March-2017) - Multiple enhancements:
#       1. Deprecated 'interpret_bits_value()'in favor of
#          'interpret_bit_flags()' which now takes 'flip_bits' argument to flip
#          bits in (list of) integer flags.
#       2. Deprecated 'bitmask2mask()' in favor of 'bitfield_to_boolean_mask()'
#          which now also takes 'flip_bits' argument.
#       3. Renamed arguments of 'interpret_bit_flags()' and
#          'bitfield_to_boolean_mask()' to be more technically correct.
#       4. 'interpret_bit_flags()' and 'bitfield_to_boolean_mask()' now
#          accept Python lists of bit flags (in addition to integer bitmasks
#          and string comma- (or '+') separated lists of bit flags).
#       5. Added 'is_bit_flag()' function to check if an integer number has
#          only one bit set (i.e., that it is a power of 2).
# 1.1.0 (29-January-2018) - Multiple enhancements:
#       1. Added support for long type in Python 2.7 in
#          `interpret_bit_flags()` and `bitfield_to_boolean_mask()`.
#       2. `interpret_bit_flags()` now always returns `int` (or `int` or `long`
#           in Python 2.7). Previously when input was of integer-like type
#           (i.e., `numpy.uint64`), it was not converted to Python `int`.
#       3. `bitfield_to_boolean_mask()` will no longer crash when
#          `ignore_flags` argument contains bit flags beyond what the type of
#          the argument `bitfield` can hold.
# 1.1.1 (30-January-2018) - Improved filtering of high bits in flags.
# 1.1.2 (10-August-2020) - Switched to astropy implementation (which was
#          originally ported from here). We plan to remove bitmask module
#          from stsci.tools package in favor of astropy's implementation
#          in a future release.
#
import warnings
from astropy.nddata.bitmask import *


warnings.warn("stsci.tools.bitmask module has been deprecated and it will be "
              "removed in a future release of stsci.tools. "
              "Use astropy.nddata,bitmask instead.", DeprecationWarning)
