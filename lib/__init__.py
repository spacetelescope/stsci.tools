#revision based svn info
try:
    import svn_version
    __svn_version__ = svn_version.__svn_version__
except:
    __svn_version__ = 'Unable to determine SVN revision'
