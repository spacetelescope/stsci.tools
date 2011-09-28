#!/usr/bin/env python
#
"""
   This module is from Lennart Regebro's ComparableMixin class, available at:

       http://regebro.wordpress.com/2010/12/13/
              python-implementing-rich-comparison-the-correct-way/

   It is intended that this will no longer be necessary after th functools
   total_ordering decorator (Python v2.7) is available on all supported
   versions of our software.
"""

class ComparableMixin(object):
    def _compare(self, other, method):
        try:
            return method(self._cmpkey(), other._cmpkey())
        except (AttributeError, TypeError):
            # _cmpkey not implemented, or return different type,
            # so I can't compare with "other".
            return NotImplemented

    def __lt__(self, other):
        return self._compare(other, lambda s,o: s < o)

    def __le__(self, other):
        return self._compare(other, lambda s,o: s <= o)

    def __eq__(self, other):
       return self._compare(other, lambda s,o: s == o)

    def __ge__(self, other):
        return self._compare(other, lambda s,o: s >= o)

    def __gt__(self, other):
        return self._compare(other, lambda s,o: s > o)

    def __ne__(self, other):
        return self._compare(other, lambda s,o: s != o)


class UnitTestClass(ComparableMixin):
    def __init__(self, v):
        self.val = v
    def _cmpkey(self):
        return self.val
    def __str__(self):
        return str(self.val)


def test():
    a = UnitTestClass('a')
    b = UnitTestClass('b')
    c = UnitTestClass('c')
    two = UnitTestClass(2)

    print('a > b ? '+str(a>b))
    print('a < b ? '+str(a<b))
    print('a <= b ? '+str(a<=b))
    print('a == b ? '+str(a==b))
    print('a < c ? '+str(a<c))
    print('a <= c ? '+str(a<=c))
    print('a != c ? '+str(a!=c))
    print('c != c ? '+str(c!=c))
    print('c == c ? '+str(c==c))
    print('b < 2 ? '+str(b<two))
    print('b >= 2 ? '+str(b>=two))
    print('b == 2 ? '+str(b==two))
    print('sorted([b,a,two,c]) ? '+str([str(x) for x in sorted([b,a,two,c])]))


#
# main routine
#
if __name__=='__main__': # in case something else imports this file
    test()
