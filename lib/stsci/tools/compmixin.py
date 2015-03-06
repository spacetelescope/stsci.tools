#!/usr/bin/env python
#
"""
   This module is from Lennart Regebro's ComparableMixin class, available at:

       http://regebro.wordpress.com/2010/12/13/
              python-implementing-rich-comparison-the-correct-way/

   The idea is to prevent you from having to define lt,le,eq,ne,etc...
   This may no longer be necessary after the functools total_ordering
   decorator (Python v2.7) is available on all Python versions
   supported by our software.

   For simple comparisons, all that is necessary is to derive your class
   from ComparableMixin and override the _cmpkey() method.

   For more complex comparisons (where type-checking needs to occur and
   comparisons to other types are allowed), simply override _compare() instead
   of _cmpkey().

   BEWARE that comparing different types has different results in Python 2.x
   versus Python 3.x:

        Python 2.7
        >>> 'a' < 2
        False

        Python 3.2.1
        >>> 'a' < 2
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
        TypeError: unorderable types: str() < int()
"""
from __future__ import print_function

import sys
if sys.version_info[0] < 3:
    string_types = basestring
else:
    string_types = str

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


class ComparableIntBaseMixin(ComparableMixin):
    """ For those classes which, at heart, are comparable to integers. """
    def _compare(self, other, method):
        if isinstance(other, self.__class__): # two objects of same class
            return method(self._cmpkey(), other._cmpkey())
        else:
            return method(int(self._cmpkey()), int(other))


class ComparableFloatBaseMixin(ComparableMixin):
    """ For those classes which, at heart, are comparable to floats. """
    def _compare(self, other, method):
        if isinstance(other, self.__class__): # two objects of same class
            return method(self._cmpkey(), other._cmpkey())
        else:
            return method(float(self._cmpkey()), float(other))


# -----------------------------------------------------------------------------


# this class is only used for testing this module!
class SimpleStrUnitTest(ComparableMixin):
    def __init__(self, v): self.val = str(v) # all input turned to string
    def __str__(self): return str(self.val)
    def _cmpkey(self): return self.val


# this class is only used for testing this module!
class AnyTypeUnitTest(ComparableMixin):
    def __init__(self, v): self.val = v # leave all input typed as is
    def __str__(self): return str(self.val)

    # define this instead of _cmpkey - handle ALL sorts of scenarios,
    # except intentionally don't compare self strings (strlen>1) with integers
    # so we have a case which fails in our test below
    def _compare(self, other, method):
        if isinstance(other, self.__class__):
            return self._compare(other.val, method) # recurse, get 2 logic below
        if isinstance(other, string_types):
            return method(str(self.val), other)
        elif other==None and self.val==None:
            return method(0, 0)
        elif other==None:
            return method(str(self.val), '') # coerce to str compare
        elif isinstance(other, int):
            # handle ONLY case where self.val is a single char or an int
            if isinstance(self.val, string_types) and len(self.val)==1:
                return method(ord(self.val), other)
            else:
                return method(int(self.val), other) # assume we are int-like
        try:
            return method(self.val, other)
        except (AttributeError, TypeError):
            return NotImplemented


# -----------------------------------------------------------------------------


def test():
    a = SimpleStrUnitTest('a')
    b = SimpleStrUnitTest('b')
    c = SimpleStrUnitTest('c')
    two = SimpleStrUnitTest(2)

    # compare two SimpleStrUnitTest objects
    assert str(a>b) == "False"
    assert str(a<b) == "True"
    assert str(a<=b) == "True"
    assert str(a==b) == "False"
    assert str(b==b) == "True"
    assert str(a<c) == "True"
    assert str(a<=c) == "True"
    assert str(a!=c) == "True"
    assert str(c!=c) == "False"
    assert str(c==c) == "True"
    assert str(b<two) == "False"
    assert str(b>=two) == "True"
    assert str(b==two) == "False"
    assert str([str(jj) for jj in sorted([b,a,two,c])])=="['2', 'a', 'b', 'c']"
    print('Success in first set')

    x = AnyTypeUnitTest('x')
    y = AnyTypeUnitTest('yyy')
    z = AnyTypeUnitTest(0)
    nn = AnyTypeUnitTest(None)

    # compare two AnyTypeUnitTest objects
    assert str(x>y) == "False"
    assert str(x<y) == "True"
    assert str(x<=y) == "True"
    assert str(x==y) == "False"
    assert str(y==y) == "True"
    assert str(x<z) == "False"
    assert str(x<=z) == "False"
    assert str(x>z) == "True"
    assert str(x!=z) == "True"
    assert str(z!=z) == "False"
    assert str(z==z) == "True"
    assert str(y<nn) == "False"
    assert str(y>=nn) == "True"
    assert str(y==nn) == "False"
    assert str(nn==nn) == "True"
    assert str([str(jj) for jj in sorted([y,x,nn,z])]) == "['None', '0', 'x', 'yyy']"
    print('Success in second set')

    # compare AnyTypeUnitTest objects to built-in types
    assert str(x<0) == "False"
    assert str(x<=0) == "False"
    assert str(x>0) == "True"
    assert str(x!=0) == "True"
    assert str(x==0) == "False"
    assert str(x<None) == "False"
    assert str(x<=None) == "False"
    assert str(x>None) == "True"
    assert str(x!=None) == "True"
    assert str(x==None) == "False"
    assert str(x<"abc") == "False"
    assert str(x<="abc") == "False"
    assert str(x>"abc") == "True"
    assert str(x!="abc") == "True"
    assert str(x=="abc") == "False"
    assert str(y<None) == "False"
    assert str(y<=None) == "False"
    assert str(y>None) == "True"
    assert str(y!=None) == "True"
    assert str(y==None) == "False"
    assert str(y<"abc") == "False"
    assert str(y<="abc") == "False"
    assert str(y>"abc") == "True"
    assert str(y!="abc") == "True"
    assert str(y=="abc") == "False"
    print('Success in third set')

    # all of the above should work without errors; now raise some
    print('yyy == 0 ?')
    try:
        y == z # AnyTypeUnitTest intentionally doesn't compare strlen>1 to ints
        assert 0, 'Exception expected but not found'
    except ValueError:
        print('   ... exception handled')

    print('sorted([0, yyy]) ?')
    try:
        sorted([z,y])
        assert 0, 'Exception expected but not found'
    except ValueError:
        print('   ... exception handled')
    print('Test successful')

# -----------------------------------------------------------------------------

if __name__=='__main__': # in case something else imports this file
    test()
