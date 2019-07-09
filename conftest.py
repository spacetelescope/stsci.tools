def pytest_report_header(config):
    """Report dependency versions"""
    import numpy
    import astropy

    return 'numpy: {}\nastropy: {}'.format(
        numpy.__version__, astropy.__version__)
