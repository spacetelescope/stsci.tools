"""fitsdiff is now a part of Astropy.

Now this module just provides a wrapper around astropy.io.fits.diff for backwards
compatibility with the old interface in case anyone uses it.
"""
import os
import sys

from astropy.io.fits.diff import FITSDiff
from astropy.io.fits.scripts.fitsdiff import log, main

PY3K = sys.version_info[0] > 2
if PY3K:
    string_types = str
else:
    string_types = basestring


def fitsdiff(input1, input2, comment_excl_list='', value_excl_list='',
             field_excl_list='', maxdiff=10, delta=0.0, neglect_blanks=True,
             output=None):

    if isinstance(comment_excl_list, string_types):
        comment_excl_list = list_parse(comment_excl_list)

    if isinstance(value_excl_list, string_types):
        value_excl_list = list_parse(value_excl_list)

    if isinstance(field_excl_list, string_types):
        field_excl_list = list_parse(field_excl_list)

    diff = FITSDiff(input1, input2, ignore_keywords=value_excl_list,
                    ignore_comments=comment_excl_list,
                    ignore_fields=field_excl_list, numdiffs=maxdiff,
                    tolerance=delta, ignore_blanks=neglect_blanks)

    if output is None:
        output = sys.stdout

    diff.report(output)

    return diff.identical


def list_parse(name_list):
    """Parse a comma-separated list of values, or a filename (starting with @)
    containing a list value on each line.
    """

    if name_list and name_list[0] == '@':
        value = name_list[1:]
        if not os.path.exists(value):
            log.warning('The file %s does not exist' % value)
            return
        try:
            return [v.strip() for v in open(value, 'r').readlines()]
        except IOError as e:
            log.warning('reading %s failed: %s; ignoring this file' %
                        (value, e))
    else:
        return [v.strip() for v in name_list.split(',')]


if __name__ == "__main__":
    sys.exit(main())
