"""
Hydro-Package
SSP
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__version__ = '0.2.0'
__doc__ = "SSP"
__author__ = 'gmasetti@ccom.unh.edu; brc@ccom.unh.edu; matthew.wilson@noaa.gov'
__license__ = 'BSD-like license'
__copyright__ = 'Copyright 2015 HydrOffice\'s authors'


def hyo():
    return __doc__, __version__
