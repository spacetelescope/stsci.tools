import os.path
import re

def __set_svn_version__(path="./", fname='svn_version.py', fullInfo=False):
    info = None
    rev = __get_svn_rev__(path)
    version_file = os.path.join(path,'lib',fname)
    #__update_version__(path,rev)

    if rev is None:
        if os.path.exists(version_file) :
            return
        revision = 'Unable to determine SVN revision'
    else:
        if rev == 'exported' and os.path.exists(version_file) :
            return
        revision = 'dev_' + str(rev)

    if fullInfo:
        info = __get_full_info__(path)
    
    f = open(version_file,'w')
    f.write("\n__svn_version__ = %s\n" % repr(revision))
    
    if info:
        f.writelines("\n__full_svn_info__ = %s\n" % info )

    f.close()

    
def __get_svn_rev__(path):
    revision = None
    m = None
    try:
        sin, sout = os.popen4('svnversion')
        
        m=sout.read().strip()
    except:
        pass
    if m:
        return  m 
    entries = os.path.join(path,'.svn','entries')
    if os.path.isfile(entries):
        f = open(entries)
        fstr = f.read()
        f.close()
        if fstr[:5] == '<?xml':  # pre 1.4
            m = re.search(r'revision="(?P<revision>\d+)"',fstr)
            if m:
                revision = int(m.group('revision'))
        else:  # non-xml entries file --- check to be sure that
            m = re.search(r'dir[\n\r]+(?P<revision>\d+)', fstr)
            if m:
                revision = int(m.group('revision'))
    return revision

def __get_full_info__(path):
    info = None
    try:
        sin, sout = os.popen4('svn info %s' % path)
        info = [l.strip() for l in sout.readlines()]
    except: pass
    
    return info
        
