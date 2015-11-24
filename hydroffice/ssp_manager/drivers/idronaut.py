from __future__ import absolute_import, division, print_function, unicode_literals

import datetime as dt
import numpy as np
import logging

log = logging.getLogger(__name__)

from .base_format import BaseFormat, FormatError
from .. import __version__
from ..ssp_dicts import Dicts


class Idronaut(BaseFormat):

    def __init__(self, file_content):
        super(Idronaut, self).__init__(file_content=file_content)
        self.name = "IDR"
        self.driver = self.name + (".%s" % __version__)

        log.info("reading ...")
        lines = self.file_content.splitlines()
        self.depth_token = 'Depth'
        self.salinity_token = 'Salinity'
        self.temperature_token = 'Temperature'
        self.sound_speed_token = 'Sound Velocity (calc)'
        
        self._read_header(lines)
        self._read_body(lines)

    def _read_header(self, lines):
        log.info("reading > header")
        cast_token = 'cast'
        token_probe_type = 'cast probe type'
        token_start_time = 'cast start time'
        token_start_latitude = 'cast start latitude'
        token_start_longitude = 'cast start longitude'

        got_depth = False
        got_speed = False
        got_temperature = False
        got_salinity = False
        got_cast_header = False

        year = None
        month = None
        day = None
        hour = None
        minute = None
        second = None

        probe_type = ''

        for line in lines:

            # look for the first row of 'cast'
            if not got_cast_header:
                if line[:len(cast_token)] == cast_token:
                    got_cast_header = True
                    log.info("first \'cast\' line: %s" % self.samples_offset)
                else:
                    self.samples_offset += 1
                    continue

            # the first line that has not a 'cast' field is the field description
            if line[:len(cast_token)] != cast_token:

                column = 0
                for field_type in line.split('\t'):
                    self.data_index[field_type] = int(column)
                    if field_type == self.depth_token:
                        got_depth = True
                    elif field_type == self.temperature_token:
                        got_temperature = True
                    elif field_type == self.salinity_token:
                        got_salinity = True
                    elif field_type == self.sound_speed_token:
                        got_speed = True
                    column += 1

                self.samples_offset += 1
                log.info("samples offset: %s" % self.samples_offset)
                break

            elif line[:len(token_probe_type)] == token_probe_type:
                probe_type += line.split(':')[-1].strip()

            elif line[:len(token_start_time)] == token_start_time:
                try:
                    date_string = line.split()[3]
                    month = int(date_string.split('/')[1])
                    day = int(date_string.split('/')[0])
                    year = int(date_string.split('/')[2])
                except ValueError:
                    raise FormatError("invalid cast of date string: %s" % line)

                try:
                    time_string = line.split()[4]
                    hour = int(time_string.split(':')[0])
                    minute = int(time_string.split(':')[1])
                    second = int(time_string.split(':')[2])
                except ValueError:
                    raise FormatError("invalid cast of time string: %s" % line)

            elif line[:len(token_start_latitude)] == token_start_latitude:
                lat_token = line.split()[-1]
                if len(lat_token) == 0:
                    self.samples_offset += 1
                    continue
                lat_deg = int(lat_token.split('\xb0')[0])
                lat_min = int(lat_token.split('\'')[0].split('\xb0')[1])
                lat_sec = float(lat_token.split('\'')[1])

                if lat_deg < 0:
                    lat_sign = -1.0
                    lat_deg = abs(lat_deg)
                else:
                    lat_sign = 1.0

                self.latitude = lat_sign * (lat_deg + lat_min / 60.0 + lat_sec / 3600.0)
                log.info('lat: %s' % self.latitude)

            elif line[:len(token_start_longitude)] == token_start_longitude:
                lon_token = line.split()[-1]
                if len(lon_token) == 0:
                    self.samples_offset += 1
                    continue
                lon_deg = int(lon_token.split('\xb0')[0])
                lon_min = int(lon_token.split('\'')[0].split('\xb0')[1])
                lon_sec = float(lon_token.split('\'')[1])

                if lon_deg < 0:
                    lon_sign = -1.0
                    lon_deg = abs(lon_deg)
                else:
                    lon_sign = 1.0
                self.longitude = lon_sign * (lon_deg + lon_min / 60.0 + lon_sec / 3600.0)
                log.info('long: %s' % self.longitude)

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

        if (year is not None) and (hour is not None):
            self.dg_time = dt.datetime(year, month, day, hour, minute, second)

        self.num_samples = len(lines) - self.samples_offset
        if probe_type != 'Idronaut':
            log.info("unknown probe type: %s -> forcing Idronaut" % probe_type)
            probe_type = 'Idronaut'
        self.probe_type = Dicts.probe_types[probe_type]
        log.info("probe_type: %s" % self.probe_type)

        self.depth = np.zeros(self.num_samples)
        self.speed = np.zeros(self.num_samples)
        self.temperature = np.zeros(self.num_samples)
        self.salinity = np.zeros(self.num_samples)

        self.sensor_type = Dicts.sensor_types['CTD']
        log.info("sensor type: %s" % self.sensor_type)

    def _read_body(self, lines):
        log.info("reading > body")

        count = 0
        for line in lines[self.samples_offset:len(lines)]:

            try:
                # In case an incomplete file comes through
                data = line.split()
                self.depth[count] = float(data[self.data_index[self.depth_token]])
                self.speed[count] = float(data[self.data_index[self.sound_speed_token]])
                self.temperature[count] = float(data[self.data_index[self.temperature_token]])
                self.salinity[count] = float(data[self.data_index[self.salinity_token]])

            except ValueError:
                log.error("invalid parsing of line: %s" % line)
                continue

            count += 1

        if self.num_samples != count:
            self.depth.resize(count)
            self.speed.resize(count)
            self.temperature.resize(count)
            self.salinity.resize(count)
            self.num_samples = count
