from __future__ import absolute_import, division, print_function, unicode_literals

import logging

log = logging.getLogger(__name__)

from .ssp import SspData
from .helper import SspError

from operator import methodcaller


class SspCollection(object):
    """A class that represents a collection of SSP data"""
    def __init__(self):
        self.data = list()

    def append(self, item):
        if not isinstance(item, SspData):
            raise SspError("invalid item passed: %s" % type(item))
        self.data.append(item)

    def date_time_sort(self):
        self.data = sorted(self.data, key=methodcaller('sorting_time') )

    def __repr__(self):
        output = str()
        for i in range(len(self.data)):
            output += "> %s: %s %s -> samples: %s (driver: %s)\n" \
                      % (i, self.data[i].date_time, self.data[i].original_path,
                         self.data[i].data.shape[1], self.data[i].driver)
        return output

