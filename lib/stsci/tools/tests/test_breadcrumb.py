"""This was pandokia breadcrumb test in stuff.py"""
from __future__ import absolute_import

import os

from .. import capable


def setup_module():
    # Turn off PyRAF display
    os.environ['PYRAF_NO_DISPLAY'] = '1'


def test_has_latest_toolscode():
    assert "28 Dec 2017" in capable.descrip
