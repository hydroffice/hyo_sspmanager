from __future__ import absolute_import, division, print_function, unicode_literals

import datetime as dt
import numpy as np
import logging

log = logging.getLogger(__name__)

from .base_format import BaseFormat, FormatError
from .. import __version__
from ..ssp_dicts import Dicts


class Castaway(BaseFormat):

    def __init__(self, file_content):
        super(Castaway, self).__init__(file_content=file_content)
        self.name = "CST"
        self.driver = self.name + (".%s" % __version__)

        log.info("reading ...")
        lines = self.file_content.splitlines()
        self.depth_token = 'Depth'
        self.salinity_token = 'Salinity'
        self.temperature_token = 'Temperature'
        self.sound_speed_token = 'Sound'

        self._read_header(lines)
        self._read_body(lines)

    def _read_header(self, lines):
        log.info("reading > header")
        token_filename = '% File name'
        token_cast_time = '% Cast time (UTC)'
        token_latitude = '% Start latitude'
        token_longitude = '% Start longitude'

        # self.num_samples = 0
        latitude = None
        longitude = None
        utc_time = None

        got_depth = False
        got_speed = False
        got_temperature = False
        got_salinity = False

        for line in lines:

            # field headers
            if line[0] != '%':
                count = 0
                for field in line.split(","):
                    field_type = field.split()[0]
                    column = count
                    self.data_index[field_type] = int(column)

                    if field_type == self.depth_token:
                        got_depth = True
                    elif field_type == self.sound_speed_token:
                        got_speed = True
                    elif field_type == self.temperature_token:
                        got_temperature = True
                    elif field_type == self.salinity_token:
                        got_salinity = True

                    count += 1
                self.samples_offset += 1
                log.info("samples offset: %s" % self.samples_offset)
                break

            elif line[:len(token_filename)] == token_filename:
                self.original_path = line.split(",")[-1]
                log.info("filename: %s" % self.original_path)

            elif line[:len(token_cast_time)] == token_cast_time:
                try:
                    field = line.split(",")[-1]
                    if len(field) != 0:
                        ymd = field.split()[-2]
                        year = int(ymd.split("-")[-3])
                        month = int(ymd.split("-")[-2])
                        day = int(ymd.split("-")[-1])
                        time_string = field.split()[-1]
                        hour, minute, second = [int(i) for i in time_string.split(':')]
                        utc_time = dt.datetime(year, month, day, hour, minute, second)
                        log.info("date: %s" % utc_time)
                except ValueError:
                    log.error("unable to parse date and time from: %s" % line)

            elif line[:len(token_latitude)] == token_latitude:
                try:
                    lat_str = line.split(",")[-1]
                    if len(lat_str) != 0:
                        latitude = float(lat_str)
                        log.info("latitude: %s" % latitude)
                except ValueError:
                    log.error("unable to parse latitude: %s" % line)

            elif line[:len(token_longitude)] == token_longitude:
                try:
                    lon_str = line.split(",")[-1]
                    if len(lon_str) != 0:
                        longitude = float(lon_str)
                        log.info("longitude: %s" % longitude)
                except ValueError:
                    log.error("unable to parse longitude: %s" % line)

            self.samples_offset += 1

        if not got_depth or not got_speed or not got_temperature or not got_salinity:
            msg = ""
            if not got_depth:
                msg += "Missing depth field (need depth 'Depth' field)\n"
            if not got_speed:
                msg += "Missing speed field (need speed 'Sound Velocity (calc)' field)\n"
            if not got_temperature:
                msg += "Missing temperature field (need temperature 'Temperature' field)\n"
            if not got_salinity:
                msg += "Missing salinity field (need salinity 'Salinity' field)"
            raise FormatError(msg)

        self.latitude = latitude
        self.longitude = longitude
        self.dg_time = utc_time
        
        self.num_samples = len(lines) - self.samples_offset
        log.info("max samples: %s" % self.num_samples)

        self.depth = np.zeros(self.num_samples)
        self.speed = np.zeros(self.num_samples)
        self.temperature = np.zeros(self.num_samples)
        self.salinity = np.zeros(self.num_samples)

        self.sensor_type = Dicts.sensor_types['CTD']
        self.probe_type = Dicts.probe_types['Castaway']
        log.info("sensor type: %s" % self.sensor_type)
        log.info("probe_type: %s" % self.probe_type)

    def _read_body(self, lines):
        log.info("reading > body")

        count = 0
        for line in lines[self.samples_offset:len(lines)]:

            # skip empty lines
            if len(line.split()) == 0:
                continue

            try:
                data = line.split(",")
                self.depth[count] = float(data[self.data_index[self.depth_token]])
                self.speed[count] = float(data[self.data_index[self.sound_speed_token]])
                self.temperature[count] = float(data[self.data_index[self.temperature_token]])
                self.salinity[count] = float(data[self.data_index[self.salinity_token]])

            except ValueError:
                raise FormatError("invalid conversion parsing of line: %s" % line)

            except IndexError:
                raise FormatError("invalid index parsing of line: %s" % line)

            count += 1

        if self.num_samples != count:
            self.depth.resize(count)
            self.speed.resize(count)
            self.temperature.resize(count)
            self.salinity.resize(count)
            self.num_samples = count
