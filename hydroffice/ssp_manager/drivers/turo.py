import datetime as dt

import netCDF4
import numpy as np
import logging

log = logging.getLogger(__name__)

from .base_format import BaseFormat
from .. import __version__
from ..ssp_dicts import Dicts


class Turo(BaseFormat):
    def __init__(self, filename):
        self.original_path = filename
        super(Turo, self).__init__(file_content=netCDF4.Dataset(self.original_path))
        self.name = "TUR"
        self.driver = self.name + (".%s" % __version__)

        log.info("reading ...")

        self._read_header(None)
        self._read_body(None)

    def _read_header(self, lines):
        log.info("reading > header")

        woce_date = str(self.file_content.variables['woce_date'][0])
        # The hours in the time field don't have a leading zero so forcing to print
        # as a 6 digit integer with leading zeros
        woce_time = "%.6d" % self.file_content.variables['woce_time'][0]

        self.dg_time = dt.datetime(int(woce_date[0:4]), int(woce_date[4:6]), int(woce_date[6:8]), int(woce_time[0:2]),
                                   int(woce_time[2:4]), int(woce_time[4:6]), 0)
        log.info("time: %s" % self.dg_time)

        self.latitude = self.file_content.variables['latitude'][0]
        log.info("latitude: %s" % self.latitude)

        self.longitude = self.file_content.variables['longitude'][0]
        log.info("longitude: %s" % self.longitude)

        self.probe_type = Dicts.probe_types["XBT"]
        log.info("probe type: %s" % self.probe_type)

        self.sensor_type = Dicts.sensor_types["XBT"]
        log.info("sensor type: %s" % self.sensor_type)

    def _read_body(self, lines):
        log.info("reading > body")

        self.depth = self.file_content.variables['depth'][:]
        self.speed = self.file_content.variables['soundSpeed'][0, :, 0, 0]
        self.temperature = self.file_content.variables['temperature'][0, :, 0, 0]
        self.num_samples = self.depth.size
        self.salinity = np.zeros(self.num_samples)
        log.info("total samples: %s" % self.num_samples)

        self.file_content.close()
