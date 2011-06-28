try:
    # As long as we're using setuptools/distribute, we need to do this the
    # setuptools way or else pkg_resources will throw up unncessary and
    # annoying warnings (even though the namespace mechanism will still
    # otherwise work without it).
    # Get rid of this as soon as setuptools/distribute is dead.
    from pkg_resources import declare_namespace
    declare_namespace(__name__)
except ImportError:
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)
