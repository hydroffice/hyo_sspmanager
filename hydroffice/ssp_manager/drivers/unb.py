from __future__ import absolute_import, division, print_function, unicode_literals

import datetime as dt
import numpy as np
import logging

log = logging.getLogger(__name__)

from .base_format import BaseFormat, FormatError
from .. import __version__
from ..ssp_dicts import Dicts


class Unb(BaseFormat):

    def __init__(self, file_content):
        super(Unb, self).__init__(file_content)
        self.name = "UNB"
        self.driver = self.name + (".%s" % __version__)
        self.version = ""

        log.info("reading ...")
        lines = self.file_content.splitlines()

        self._read_header(lines)
        self._read_body(lines)

    def _read_header(self, lines):
        log.info("reading > header")

        try:
            self.version = int(lines[0].split()[0])
            log.info("version: %s" % self.version)
        except ValueError:
            log.error("unable to parse the version: %s" % lines[0])

        try:
            year = int(lines[1].split()[0])
            jday = int(lines[1].split()[1])
            time = lines[1].split()[2]
            hour, minute, second = [int(i) for i in time.split(':')]
            utc_time = dt.datetime(year, 1, 1, hour, minute, second) + dt.timedelta(days=jday-1)
            self.dg_time = utc_time
            log.info("time: %s" % self.dg_time)
        except ValueError:
            log.error("unable to parse the time: %s" % lines[1])

        try:
            latitude = float(lines[3].split()[0])
            longitude = float(lines[3].split()[1])
            self.latitude = latitude
            self.longitude = longitude
            log.info("position: %s %s" % (self.latitude, self.longitude))
        except ValueError:
            log.error("unable to parse the position: %s" % lines[3])

        try:
            num_samples = int(lines[5].split()[0])
            self.num_samples = num_samples
            log.info("total samples: %s" % self.num_samples)
        except ValueError:
            log.error("unable to parse the number of samples: %s" % lines[5])

        # Faking an XBT for now to help make examples of how CTDs can augment XBTs with salinity
        self.sensor_type = Dicts.sensor_types['XBT']
        log.info("sensor type: %s" % self.sensor_type)
        self.probe_type = Dicts.probe_types['XBT']
        log.info("probe type: %s" % self.probe_type)

        self.depth = np.zeros(self.num_samples)
        self.speed = np.zeros(self.num_samples)
        self.temperature = np.zeros(self.num_samples)
        self.salinity = np.zeros(self.num_samples)
        self.flag = np.zeros(self.num_samples)

    def _read_body(self, lines):
        log.info("reading > body")

        count = 0
        for line in lines[16:len(lines)]:
            try:
                # In case an incomplete file comes through
                data = line.split()
                self.depth[count] = float(data[1])
                self.speed[count] = float(data[2])

                if self.version == 2:
                    # Only version 2 and higher holds T/S and flags
                    self.temperature[count] = float(data[3])
                    self.salinity[count] = float(data[4])
                    # The fifth field is an extra field
                    self.flag[count] = float(data[6])
            except ValueError:
                log.error("failure in reading sample %s" % count)
                break
            count += 1

        if self.num_samples != count:
            self.depth.resize(count)
            self.speed.resize(count)
            self.temperature.resize(count)
            self.salinity.resize(count)
            self.flag.resize(count)
            self.num_samples = count
