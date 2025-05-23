"""A module that provides functions for manipulating bitmasks and data quality
(DQ) arrays.

"""
import warnings
import numpy as np
from astropy.utils import deprecated

__version__ = '1.1.2'
__vdate__ = '10-August-2021'
__author__ = 'Mihai Cara'

__all__ = ['interpret_bit_flags', 'bitfield_to_boolean_mask', 'is_bit_flag']

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
# 1.1.2 (11-August-2021) - Improved compatibility with numpy 1.21.*.
#
INT_TYPE = (int, )
SUPPORTED_FLAGS = int(np.bitwise_not(
    0, dtype="uint64", casting='unsafe'
))


def is_bit_flag(n):
    """
    Verifies if the input number is a bit flag (i.e., an integer number that is
    an integer power of 2).

    Parameters
    ----------
    n : int
        A positive integer number. Non-positive integers are considered not to
        be "flags".

    Returns
    -------
    result : bool
        ``True`` if input ``n`` is a bit flag and ``False`` if it is not.

    """
    if n < 1:
        return False

    return bin(n).count('1') == 1


def _is_int(n):
    return (
        (isinstance(n, INT_TYPE) and not isinstance(n, bool)) or
        (isinstance(n, np.generic) and np.issubdtype(n, np.integer))
    )


def interpret_bit_flags(bit_flags, flip_bits=None):
    """
    Converts input bit flags to a single integer value (bitmask) or `None`.

    When input is a list of flags (either a Python list of integer flags or a
    sting of comma- or '+'-separated list of flags), the returned bitmask
    is obtained by summing input flags.

    .. note::
        In order to flip the bits of the returned bitmask,
        for input of `str` type, prepend '~' to the input string. '~' must
        be prepended to the *entire string* and not to each bit flag! For
        input that is already a bitmask or a Python list of bit flags, set
        `flip_bits` for `True` in order to flip the bits of the returned
        bitmask.

    Parameters
    ----------
    bit_flags : int, str, list, None
        An integer bitmask or flag, `None`, a string of comma- or
        '+'-separated list of integer bit flags, or a Python list of integer
        bit flags. If `bit_flags` is a `str` and if it is prepended with '~',
        then the output bitmask will have its bits flipped (compared to simple
        sum of input flags). For input `bit_flags` that is already a bitmask
        or a Python list of bit flags, bit-flipping can be controlled through
        `flip_bits` parameter.

    flip_bits : bool, None
        Indicates whether or not to flip the bits of the returned bitmask
        obtained from input bit flags. This parameter must be set to `None`
        when input `bit_flags` is either `None` or a Python list of flags.

    Returns
    -------
    bitmask : int or None
        Returns and integer bit mask formed from the input bit value
        or `None` if input `bit_flags` parameter is `None` or an empty string.
        If input string value was prepended with '~' (or `flip_bits` was
        set to `True`), then returned value will have its bits flipped
        (inverse mask).

    Examples
    --------
    >>> from stsci.tools.bitmask import interpret_bit_flags
    >>> "{0:016b}".format(0xFFFF & interpret_bit_flags(28))
    '0000000000011100'
    >>> "{0:016b}".format(0xFFFF & interpret_bit_flags('4,8,16'))
    '0000000000011100'
    >>> "{0:016b}".format(0xFFFF & interpret_bit_flags('~4,8,16'))
    '1111111111100011'
    >>> "{0:016b}".format(0xFFFF & interpret_bit_flags('~(4+8+16)'))
    '1111111111100011'
    >>> "{0:016b}".format(0xFFFF & interpret_bit_flags([4, 8, 16]))
    '0000000000011100'
    >>> "{0:016b}".format(0xFFFF & interpret_bit_flags([4, 8, 16], flip_bits=True))
    '1111111111100011'

    """
    has_flip_bits = flip_bits is not None
    flip_bits = bool(flip_bits)
    allow_non_flags = False

    if _is_int(bit_flags):
        return (~int(bit_flags) if flip_bits else int(bit_flags))

    elif bit_flags is None:
        if has_flip_bits:
            raise TypeError(
                "Keyword argument 'flip_bits' must be set to 'None' when "
                "input 'bit_flags' is None."
            )
        return None

    elif isinstance(bit_flags, str):
        if has_flip_bits:
            raise TypeError(
                "Keyword argument 'flip_bits' is not permitted for "
                "comma-separated string lists of bit flags. Prepend '~' to "
                "the string to indicate bit-flipping."
            )

        bit_flags = str(bit_flags).strip()

        if bit_flags.upper() in ['', 'NONE', 'INDEF']:
            return None

        # check whether bitwise-NOT is present and if it is, check that it is
        # in the first position:
        bitflip_pos = bit_flags.find('~')
        if bitflip_pos == 0:
            flip_bits = True
            bit_flags = bit_flags[1:].lstrip()
        else:
            if bitflip_pos > 0:
                raise ValueError("Bitwise-NOT must precede bit flag list.")
            flip_bits = False

        # basic check for correct use of parenthesis:
        while True:
            nlpar = bit_flags.count('(')
            nrpar = bit_flags.count(')')

            if nlpar == 0 and nrpar == 0:
                break

            if nlpar != nrpar:
                raise ValueError("Unbalanced parantheses in bit flag list.")

            lpar_pos = bit_flags.find('(')
            rpar_pos = bit_flags.rfind(')')
            if lpar_pos > 0 or rpar_pos < (len(bit_flags) - 1):
                raise ValueError("Incorrect syntax (incorrect use of "
                                 "parenthesis) in bit flag list.")

            bit_flags = bit_flags[1:-1].strip()

        if ',' in bit_flags:
            bit_flags = bit_flags.split(',')

        elif '+' in bit_flags:
            bit_flags = bit_flags.split('+')

        else:
            if bit_flags == '':
                raise ValueError(
                    "Empty bit flag lists not allowed when either bitwise-NOT "
                    "or parenthesis are present."
                )
            bit_flags = [bit_flags]

        allow_non_flags = len(bit_flags) == 1

    elif hasattr(bit_flags, '__iter__'):
        if not all([_is_int(flag) for flag in bit_flags]):
            raise TypeError("Each bit flag in a list must be an integer.")

    else:
        raise TypeError("Unsupported type for argument 'bit_flags'.")

    bitset = set(map(int, bit_flags))
    if len(bitset) != len(bit_flags):
        warnings.warn("Duplicate bit flags will be ignored")

    bitmask = 0
    for v in bitset:
        if not is_bit_flag(v) and not allow_non_flags:
            raise ValueError("Input list contains invalid (not powers of two) "
                             "bit flags")
        bitmask += v

    if flip_bits:
        bitmask = ~bitmask

    return bitmask


def bitfield_to_boolean_mask(bitfield, ignore_flags=0, flip_bits=None,
                             good_mask_value=True, dtype=np.bool_):
    """
    Converts an array of bit fields to a boolean (or integer) mask array
    according to a bitmask constructed from the supplied bit flags (see
    ``ignore_flags`` parameter).

    This function is particularly useful to convert data quality arrays to
    boolean masks with selective filtering of DQ flags.

    Parameters
    ----------
    bitfield : numpy.ndarray
        An array of bit flags. By default, values different from zero are
        interpreted as "bad" values and values equal to zero are considered
        as "good" values. However, see ``ignore_flags`` parameter on how to
        selectively ignore some bits in the ``bitfield`` array data.

    ignore_flags : int, str, list, None
        An integer bitmask, a Python list of bit flags, a comma- or
        '+'-separated string list of integer bit flags that indicate what
        bits in the input ``bitfield`` should be *ignored* (i.e., zeroed), or
        `None`.

        Setting ``ignore_flags`` to `None` effectively will make
        `bitfield_to_boolean_mask` interpret all ``bitfield`` elements
        as "good" regardless of their value.

        When ``ignore_flags`` argument is an integer bitmask, it will be
        combined using bitwise-NOT and bitwise-AND with each element of the
        input ``bitfield`` array (``~ignore_flags & bitfield``). If the
        resultant bitfield element is non-zero, that element will be
        interpreted as a "bad" in the output boolean mask and it will be
        interpreted as "good" otherwise. ``flip_bits`` parameter may be used
        to flip the bits (``bitwise-NOT``) of the bitmask thus effectively
        changing the meaning of the ``ignore_flags`` parameter from "ignore"
        to "use only" these flags.

        .. note::

            Setting ``ignore_flags`` to 0 effectively will assume that all
            non-zero elements in the input ``bitfield`` array are to be
            interpreted as "bad".

        When ``ignore_flags`` argument is an Python list of integer bit
        flags, these flags are added together to create an integer bitmask.
        Each item in the list must be a flag, i.e., an integer that is an
        integer power of 2. In order to flip the bits of the resultant
        bitmask, use ``flip_bits`` parameter.

        Alternatively, ``ignore_flags`` may be a string of comma- or
        '+'-separated list of integer bit flags that should be added together
        to create an integer bitmask. For example, both ``'4,8'`` and
        ``'4+8'`` are equivalent and indicate that bit flags 4 and 8 in
        the input ``bitfield`` array should be ignored when generating
        boolean mask.

        .. note::

            ``'None'``, ``'INDEF'``, and empty (or all white space) strings
            are special values of string ``ignore_flags`` that are
            interpreted as `None`.

        .. note::

            Each item in the list must be a flag, i.e., an integer that is an
            integer power of 2. In addition, for convenience, an arbitrary
            **single** integer is allowed and it will be interpretted as an
            integer bitmask. For example, instead of ``'4,8'`` one could
            simply provide string ``'12'``.

        .. note::

            When ``ignore_flags`` is a `str` and when it is prepended with
            '~', then the meaning of ``ignore_flags`` parameters will be
            reversed: now it will be interpreted as a list of bit flags to be
            *used* (or *not ignored*) when deciding which elements of the
            input ``bitfield`` array are "bad". Following this convention,
            an ``ignore_flags`` string value of ``'~0'`` would be equivalent
            to setting ``ignore_flags=None``.

        Defaults to ``0``

        .. warning::

            Because prepending '~' to a string ``ignore_flags`` is equivalent
            to setting ``flip_bits`` to `True`, ``flip_bits`` cannot be used
            with string ``ignore_flags`` and it must be set to `None`.

    flip_bits : bool, None
        Specifies whether or not to invert the bits of the bitmask either
        supplied directly through ``ignore_flags`` parameter or built from the
        bit flags passed through ``ignore_flags`` (only when bit flags are
        passed as Python lists of integer bit flags). Occasionally, it may be
        useful to *consider only specific bit flags* in the ``bitfield``
        array when creating a boolean mask as opposite to *ignoring* specific
        bit flags as ``ignore_flags`` behaves by default. This can be achieved
        by inverting/flipping the bits of the bitmask created from
        ``ignore_flags`` flags which effectively changes the meaning of the
        ``ignore_flags`` parameter from "ignore" to "use only" these flags.
        Setting ``flip_bits`` to `None` means that no bit flipping will be
        performed. Bit flipping for string lists of bit flags must be
        specified by prepending '~' to string bit flag lists
        (see documentation for ``ignore_flags`` for more details).

        Defaults to `None`

        .. warning::
            This parameter can be set to either `True` or `False` **ONLY** when
            ``ignore_flags`` is either an integer bitmask or a Python
            list of integer bit flags. When ``ignore_flags`` is either
            `None` or a string list of flags, ``flip_bits`` **MUST** be set
            to `None`.

    good_mask_value : int, bool
        This parameter is used to derive the values that will be assigned to
        the elements in the output boolean mask array that correspond to the
        "good" bit fields (that are 0 after zeroing bits specified by
        ``ignore_flags``) in the input ``bitfield`` array. When
        ``good_mask_value`` is non-zero or `True` then values in the output
        boolean mask array corresponding to "good" bit fields in ``bitfield``
        will be `True` (if ``dtype`` is `numpy.bool_`) or 1 (if ``dtype`` is
        of numerical type) and values of corresponding to "bad" flags will be
        `False` (or 0). When ``good_mask_value`` is zero or `False` then the
        values in the output boolean mask array corresponding to "good" bit
        fields in ``bitfield`` will be `False` (if ``dtype`` is `numpy.bool_`)
        or 0 (if ``dtype`` is of numerical type) and values of corresponding
        to "bad" flags will be `True` (or 1).

        Defaults to `True`

    dtype : type, str
        The desired data-type for the output binary mask array.

    Returns
    -------
    mask : numpy.ndarray
        Returns an array of the same dimensionality as the input ``bitfield``
        array whose elements can have two possible values,
        e.g., `True` or `False` (or 1 or 0 for integer ``dtype``) according to
        values of to the input ``bitfield`` elements, ``ignore_flags``
        parameter, and the ``good_mask_value`` parameter.

    Examples
    --------
    >>> from stsci.tools import bitmask
    >>> import numpy as np
    >>> dqbits = np.asarray([[0,0,1,2,0,8,12,0],[10,4,0,0,0,16,6,0]])
    >>> bitmask.bitfield_to_boolean_mask(dqbits, ignore_flags=0, dtype=int)
    array([[1, 1, 0, 0, 1, 0, 0, 1],
           [0, 0, 1, 1, 1, 0, 0, 1]])
    >>> bitmask.bitfield_to_boolean_mask(dqbits, ignore_flags=0, dtype=bool)
    array([[ True,  True, False, False,  True, False, False,  True],
           [False, False,  True,  True,  True, False, False,  True]])
    >>> bitmask.bitfield_to_boolean_mask(dqbits, ignore_flags=6, good_mask_value=0, dtype=int)
    array([[0, 0, 1, 0, 0, 1, 1, 0],
           [1, 0, 0, 0, 0, 1, 0, 0]])
    >>> bitmask.bitfield_to_boolean_mask(dqbits, ignore_flags=~6, good_mask_value=0, dtype=int)
    array([[0, 0, 0, 1, 0, 0, 1, 0],
           [1, 1, 0, 0, 0, 0, 1, 0]])
    >>> bitmask.bitfield_to_boolean_mask(dqbits, ignore_flags=6, flip_bits=True, good_mask_value=0, dtype=int)
    array([[0, 0, 0, 1, 0, 0, 1, 0],
           [1, 1, 0, 0, 0, 0, 1, 0]])
    >>> bitmask.bitfield_to_boolean_mask(dqbits, ignore_flags='~(2+4)', good_mask_value=0, dtype=int)
    array([[0, 0, 0, 1, 0, 0, 1, 0],
           [1, 1, 0, 0, 0, 0, 1, 0]])
    >>> bitmask.bitfield_to_boolean_mask(dqbits, ignore_flags=[2, 4], flip_bits=True, good_mask_value=0, dtype=int)
    array([[0, 0, 0, 1, 0, 0, 1, 0],
           [1, 1, 0, 0, 0, 0, 1, 0]])

    """
    bitfield = np.asarray(bitfield)
    if not np.issubdtype(bitfield.dtype, np.integer):
        raise TypeError("Input bitfield array must be of integer type.")

    ignore_mask = interpret_bit_flags(ignore_flags, flip_bits=flip_bits)

    if ignore_mask is None:
        if good_mask_value:
            mask = np.ones_like(bitfield, dtype=dtype)
        else:
            mask = np.zeros_like(bitfield, dtype=dtype)
        return mask

    # filter out bits beyond the maximum supported by the data type:
    ignore_mask = ignore_mask & SUPPORTED_FLAGS

    # invert the "ignore" mask:
    ignore_mask = np.bitwise_not(ignore_mask, dtype=bitfield.dtype.type,
                                 casting='unsafe')

    mask = np.empty_like(bitfield, dtype=np.bool_)
    np.bitwise_and(bitfield, ignore_mask, out=mask, casting='unsafe')

    if good_mask_value:
        np.logical_not(mask, out=mask)

    return mask.astype(dtype=dtype, subok=False, copy=False)


@deprecated(since='3.4.6', message='', name='interpret_bits_value',
            alternative='interpret_bit_flags')
def interpret_bits_value(val):
    """
    Converts input bits value from string to a single integer value or None.
    If a comma- or '+'-separated set of values are provided, they are summed.

    .. note::
        In order to flip the bits of the final result (after summation),
        for input of `str` type, prepend '~' to the input string. '~' must
        be prepended to the *entire string* and not to each bit flag!

    Parameters
    ----------
    val : int, str, None
        An integer bit mask or flag, `None`, or a comma- or '+'-separated
        string list of integer bit values. If `val` is a `str` and if
        it is prepended with '~', then the output bit mask will have its
        bits flipped (compared to simple sum of input val).

    Returns
    -------
    bitmask : int or None
        Returns and integer bit mask formed from the input bit value
        or `None` if input `val` parameter is `None` or an empty string.
        If input string value was prepended with '~', then returned
        value will have its bits flipped (inverse mask).

    """
    if isinstance(val, int) or val is None:
        return val

    else:
        val = str(val).strip()

        if val.startswith('~'):
            flip_bits = True
            val = val[1:].lstrip()
        else:
            flip_bits = False

        if val.startswith('('):
            if val.endswith(')'):
                val = val[1:-1].strip()
            else:
                raise ValueError('Unbalanced parantheses or incorrect syntax.')

        if ',' in val:
            valspl = val.split(',')
            bitmask = 0
            for v in valspl:
                bitmask += int(v)

        elif '+' in val:
            valspl = val.split('+')
            bitmask = 0
            for v in valspl:
                bitmask += int(v)

        elif val.upper() in ['', 'NONE', 'INDEF']:
            return None

        else:
            bitmask = int(val)

        if flip_bits:
            bitmask = ~bitmask

    return bitmask


@deprecated(since='3.4.6', message='', name='bitmask2mask',
            alternative='bitfield_to_boolean_mask')
def bitmask2mask(bitmask, ignore_bits, good_mask_value=1, dtype=np.bool_):
    r"""
    bitmask2mask(bitmask, ignore_bits, good_mask_value=1, dtype=numpy.bool\_)
    Interprets an array of bit flags and converts it to a "binary" mask array.
    This function is particularly useful to convert data quality arrays to
    binary masks.

    Parameters
    ----------
    bitmask : numpy.ndarray
        An array of bit flags. Values different from zero are interpreted as
        "bad" values and values equal to zero are considered as "good" values.
        However, see `ignore_bits` parameter on how to ignore some bits
        in the `bitmask` array.

    ignore_bits : int, str, None
        An integer bit mask, `None`, or a comma- or '+'-separated
        string list of integer bit values that indicate what bits in the
        input `bitmask` should be *ignored* (i.e., zeroed). If `ignore_bits`
        is a `str` and if it is prepended with '~', then the meaning
        of `ignore_bits` parameters will be reversed: now it will be
        interpreted as a list of bits to be *used* (or *not ignored*) when
        deciding what elements of the input `bitmask` array are "bad".

        The `ignore_bits` parameter is the integer sum of all of the bit
        values from the input `bitmask` array that should be considered
        "good" when creating the output binary mask. For example, if
        values in the `bitmask` array can be combinations
        of 1, 2, 4, and 8 flags and one wants to consider that
        values having *only* bit flags 2 and/or 4 as being "good",
        then `ignore_bits` should be set to 2+4=6. Then a `bitmask` element
        having values 2,4, or 6 will be considered "good", while an
        element with a value, e.g., 1+2=3, 4+8=12, etc. will be interpreted
        as "bad".

        Alternatively, one can enter a comma- or '+'-separated list
        of integer bit flags that should be added to obtain the
        final "good" bits. For example, both ``4,8`` and ``4+8``
        are equivalent to setting `ignore_bits` to 12.

        See :py:func:`interpret_bits_value` for examples.

        | Setting `ignore_bits` to `None` effectively will interpret
          all `bitmask` elements as "good" regardless of their value.

        | Setting `ignore_bits` to 0 effectively will assume that all
          non-zero elements in the input `bitmask` array are to be
          interpreted as "bad".

        | In order to reverse the meaning of the `ignore_bits`
          parameter from indicating bits in the values of `bitmask`
          elements that should be ignored when deciding which elements
          are "good" (these are the elements that are zero after ignoring
          `ignore_bits`), to indicating the bits should be used
          exclusively in deciding whether a `bitmask` element is "good",
          prepend '~' to the string value. For example, in order to use
          **only** (or **exclusively**) flags 4 and 8 (2nd and 3rd bits)
          in the values of the input `bitmask` array when deciding whether
          or not that element is "good", set `ignore_bits` to ``~4+8``,
          or ``~4,8 To obtain the same effect with an `int` input value
          (except for 0), enter -(4+8+1)=-9. Following this convention,
          a `ignore_bits` string value of ``'~0'`` would be equivalent to
          setting ``ignore_bits=None``.

    good_mask_value : int, bool (Default = 1)
        This parameter is used to derive the values that will be assigned to
        the elements in the output `mask` array that correspond to the "good"
        flags (that are 0 after zeroing bits specified by `ignore_bits`)
        in the input `bitmask` array. When `good_mask_value` is non-zero or
        `True` then values in the output mask array corresponding to "good"
        bit flags in `bitmask` will be 1 (or `True` if `dtype` is `bool`) and
        values of corresponding to "bad" flags will be 0. When
        `good_mask_value` is zero or `False` then values in the output mask
        array corresponding to "good" bit flags in `bitmask` will be 0
        (or `False` if `dtype` is `bool`) and values of corresponding
        to "bad" flags will be 1.

    dtype : data-type (Default = numpy.uint8)
        The desired data-type for the output binary mask array.

    Returns
    -------
    mask : numpy.ndarray
        Returns an array whose elements can have two possible values,
        e.g., 1 or 0 (or `True` or `False` if `dtype` is `bool`) according to
        values of to the input `bitmask` elements, `ignore_bits` parameter,
        and the `good_mask_value` parameter.

    """
    if not np.issubdtype(bitmask.dtype, np.integer):
        raise TypeError("Input 'bitmask' array must be of integer type.")

    ignore_bits = interpret_bits_value(ignore_bits)

    if ignore_bits is None:
        if good_mask_value:
            mask = np.ones_like(bitmask, dtype=dtype)
        else:
            mask = np.zeros_like(bitmask, dtype=dtype)
        return mask

    ignore_bits = ~bitmask.dtype.type(ignore_bits)

    mask = np.empty_like(bitmask, dtype=np.bool_)
    np.bitwise_and(bitmask, ignore_bits, out=mask, casting='unsafe')

    if good_mask_value:
        np.logical_not(mask, out=mask)

    return mask.astype(dtype=dtype, subok=False, copy=False)
