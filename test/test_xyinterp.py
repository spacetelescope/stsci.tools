from nonlincor import xyinterp
import numpy as N

def testxyinterp():
    #test 1
    x=N.array((1,2,3,4,5))
    y=x.copy()
    ans = xyinterp(x,y,3)
    assert ans == 3, "Test 1 failed, ans = %f, should be 3"%ans
    
    #test 2
    ans = xyinterp(x,y,3.5)
    assert ans == 3.5, "Test 2 failed, ans = %f, should be 3.5"%ans

    #test 3
    try:
        ans = xyinterp(x,y,-3)
        print "Test 3 failed; should have thrown an exception"
        print ans
    except ValueError:
        pass

    #test 4
    try:
        ans = xyinterp(x,y,5.6)
        print ans
        print "Test 4 failed; should have thrown an exception"
    except ValueError:
        pass
    
    #test 5
    x=N.array((1,3,7,9,12))
    y=N.array((5,10,15,20,25))
    ans = xyinterp(x,y,8)
    assert ans == 17.5, "Test 5 failed, ans = %f, should be 17.5"%ans

    #test 6
    x=N.array((5,3,6,2,7,0))
    y=N.array((4,6,2,4,6,2))
    try:
        ans = xyinterp(x,y,2)
        print ans
        print "Test 6 failed, should have thrown exception"
    except ValueError:
        pass

    #test 7
    x=N.array((1,2,3,4,5))
    y=N.arange(20)
    
    try:
        ans = xyinterp(x,y,2)
        print ans
        print "Test 7 failed, should have thrown exception"
    except ValueError:
        pass

if __name__ == '__main__':
    testinterp()
