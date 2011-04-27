from __future__ import division # confidence high

from stsci.tools.xyinterp import xyinterp
import numpy as N

x=N.array((1,2,3,4,5))
y=x.copy()

def test_xyinterp_1():
    #test 1
    ans = xyinterp(x,y,3)
    assert ans == 3, "Test 1 failed, ans = %f, should be 3"%ans

def test_xyinterp_2():
    #test 2
    ans = xyinterp(x,y,3.5)
    assert ans == 3.5, "Test 2 failed, ans = %f, should be 3.5"%ans

def test_xyinterp_3():
    #test 3
    try:
        ans = xyinterp(x,y,-3)
        raise AssertionError( "Test 3 failed; should have thrown an exception, answer = %s" % str(ans))
    except ValueError:
        pass

def test_xyinterp_4():
    #test 4
    try:
        ans = xyinterp(x,y,5.6)
        raise AssertionError( "Test 4 failed; should have thrown an exception, answer = %s" % str(ans))
    except ValueError:
        pass
    
def test_xyinterp_5():
    #test 5
    x=N.array((1,3,7,9,12))
    y=N.array((5,10,15,20,25))
    ans = xyinterp(x,y,8)
    assert ans == 17.5, "Test 5 failed, ans = %f, should be 17.5"%ans

def test_xyinterp_6():
    #test 6
    x=N.array((5,3,6,2,7,0))
    y=N.array((4,6,2,4,6,2))
    try:
        ans = xyinterp(x,y,2)
        raise AssertionError( "Test 6 failed; should have thrown an exception, answer = %s" % str(ans))
    except ValueError:
        pass

def test_xyinterp_7():
    #test 7
    x=N.array((1,2,3,4,5))
    y=N.arange(20)
    
    try:
        ans = xyinterp(x,y,2)
        raise AssertionError( "Test 7 failed; should have thrown an exception, answer = %s" % str(ans))
    except ValueError:
        pass

if __name__ == '__main__':
    test_xyinterp_1()
    test_xyinterp_2()
    test_xyinterp_3()
    test_xyinterp_4()
    test_xyinterp_5()
    test_xyinterp_6()
    test_xyinterp_7()
