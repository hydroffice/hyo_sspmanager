from __future__ import absolute_import, division, print_function, unicode_literals

from abc import ABCMeta, abstractmethod

import numpy as np
import logging

log = logging.getLogger(__name__)

from ..helper import SspError
from ..ssp_dicts import Dicts


class FormatError(SspError):
    """ Error raised for format issues """
    def __init__(self, message, *args):
        self.message = message
        # allow users initialize misc. arguments as any other builtin Error
        super(FormatError, self).__init__(message, *args)


class BaseFormat(object):
    """ Common abstract data format """

    __metaclass__ = ABCMeta

    # A dictionary to store data type column indices
    data_index = {}

    def __init__(self, file_content):
        super(BaseFormat, self).__init__()
        self.name = "FMT"

        self.file_content = file_content

        self.latitude = None
        self.longitude = None
        self.dg_time = None
        self.driver = self.name + ".DRIVER"
        self.original_path = None
        self.probe_type = None
        self.sensor_type = None

        self.samples_offset = 0
        self.num_samples = 0
        self.input_salinity = None

        self.depth = None
        self.speed = None
        self.temperature = None
        self.salinity = None

    @classmethod
    def replace_non_ascii_byte(cls, txt):
        return ''.join([i if ord(i) < 128 else ',' for i in txt])

    def convert_ssp(self, ssp=None):
        if ssp is None:
            from ..ssp import SspData
            ssp = SspData()

        ssp.set_position(self.latitude, self.longitude)
        ssp.set_time(self.dg_time)

        if self.depth is None:
            raise FormatError("missing depth array")
        if self.speed is None:
            raise FormatError("missing speed array")
        if self.temperature is None:
            raise FormatError("missing temperature array")
        if self.salinity is None:
            raise FormatError("missing salinity array")
        ssp.set_samples(depth=self.depth, speed=self.speed, temperature=self.temperature, salinity=self.salinity,
                        source=np.zeros(self.num_samples), flag=np.zeros(self.num_samples))
        ssp.store_raw()

        ssp.source_info = Dicts.first_match(Dicts.probe_types, self.probe_type)
        ssp.sensor_type = self.sensor_type
        ssp.driver = self.driver
        ssp.original_path = self.original_path

        return ssp

    def __repr__(self):
        output = str()

        output += "- Date Time: %s\n" % self.dg_time
        output += "- Position: %s %s\n" % (self.longitude, self.latitude)
        output += '- Original Path: %s\n' % self.original_path
        output += '- Sensor Type: %s\n' % self.sensor_type
        output += '- Probe Type: %s\n' % self.probe_type
        output += '- Driver: %s\n' % self.driver
        output += '- Samples: %d\n' % self.num_samples

        if self.num_samples < 10:
            for count in range(self.num_samples):
                output += '%.2f %.2f %.2f %.2f\n' \
                          % (self.depth[count], self.speed[count],
                             self.temperature[count], self.salinity[count])
        else:
            # first 5 values
            for count in range(5):
                output += '%.2f %.2f %.2f %.2f\n' \
                          % (self.depth[count],
                             self.speed[count],
                             self.temperature[count],
                             self.salinity[count])

            output += '.... .... .... .... ....\n'
            output += '%.2f %.2f %.2f %.2f\n' \
                      % (self.depth[-1],
                         self.speed[-1],
                         self.temperature[-1],
                         self.salinity[-1])

        return output
