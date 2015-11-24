from __future__ import absolute_import, division, print_function, unicode_literals

import datetime as dt
import numpy as np
import logging

log = logging.getLogger(__name__)

from .base_format import BaseFormat, FormatError
from .. import __version__
from ..ssp_dicts import Dicts


class Saiv(BaseFormat):

    def __init__(self, file_content):
        super(Saiv, self).__init__(file_content=file_content)
        self.name = "SAI"
        self.driver = self.name + (".%s" % __version__)

        self.header_token = 'Ser\tMeas'
        self.depth_token = 'Press'
        self.speed_token = 'S. vel.'
        self.temp_token = 'Temp'
        self.sal_token = 'Sal.'
        self.date_token = 'Date'
        self.time_token = 'Time'
        self.probe_type_token = 'From file:'

        log.info("reading ...")
        lines = self.file_content.splitlines()

        self._read_header(lines)
        self._read_body(lines)

    def _read_header(self, lines):
        log.info("reading > header")

        got_date = False
        got_time = False
        got_depth = False
        got_speed = False
        got_temperature = False
        got_salinity = False
        got_cast_header = False

        probe_type = ''

        self.samples_offset = 0

        for line in lines:

            if line[:len(self.header_token)] == self.header_token:
                got_cast_header = True
                log.info("header line for fields: %s" % line)

                column = 0
                for field_type in line.split('\t'):
                    self.data_index[field_type] = int(column)
                    if field_type == self.depth_token:
                        log.info('col for pressure: %s' % column)
                        got_depth = True
                    elif field_type == self.temp_token:
                        log.info('col for temperature: %s' % column)
                        got_temperature = True
                    elif field_type == self.sal_token:
                        log.info('col for salinity: %s' % column)
                        got_salinity = True
                    elif field_type == self.speed_token:
                        log.info('col for sound speed: %s' % column)
                        got_speed = True
                    elif field_type == self.date_token:
                        log.info('col for date: %s' % column)
                        got_date = True
                    elif field_type == self.time_token:
                        log.info('col for time: %s' % column)
                        got_time = True
                    column += 1

                self.samples_offset += 2
                break

            elif line[:len(self.probe_type_token)] == self.probe_type_token:
                try:
                    probe_type = line.split(':')[1].split()[0].strip()
                    log.info('probe type: %s' % probe_type)
                except (IndexError, ValueError):
                    pass

            self.samples_offset += 1

        if not got_cast_header or \
                not got_depth or not got_speed or not got_temperature or not got_salinity or \
                not got_date or not got_time:
            if not got_cast_header:
                log.error("missing cast header")
            if not got_depth:
                log.error("missing depth field (need depth 'Depth' field)")
            if not got_speed:
                log.error("missing speed field (need speed 'Sound Velocity (calc)' field)")
            if not got_temperature:
                log.error("missing temperature field (need temperature 'Temperature' field)")
            if not got_salinity:
                log.error("missing salinity field (need salinity 'Salinity' field)")
            if not got_date:
                log.error("missing date field (need date 'Date' field)")
            if not got_time:
                log.error("missing time field (need time 'Time' field)")
            return

        self.num_samples = len(lines) - self.samples_offset
        if self.num_samples == 0:
            log.error('no data samples')
            return
        log.info('samples: %s' % self.num_samples)

        if probe_type != 'S2':
            log.info("unknown probe type: %s -> forcing S2" % probe_type)
            probe_type = 'S2'
        self.probe_type = Dicts.probe_types[probe_type]

        self.sensor_type = Dicts.sensor_types["CTD"]
        self.depth = np.zeros(self.num_samples)
        self.speed = np.zeros(self.num_samples)
        self.temperature = np.zeros(self.num_samples)
        self.salinity = np.zeros(self.num_samples)

    def _read_body(self, lines):
        log.info("reading > body")

        count = 0
        valid_date = False
        valid_time = False
        for line in lines[self.samples_offset:len(lines)]:
            try:
                # In case an incomplete file comes through
                data = line.split()
                self.depth[count] = float(data[self.data_index[self.depth_token]])
                self.speed[count] = float(data[self.data_index[self.speed_token]])
                self.temperature[count] = float(data[self.data_index[self.temp_token]])
                self.salinity[count] = float(data[self.data_index[self.sal_token]])

                if not valid_date and not valid_time:
                    # date
                    date_string = data[self.data_index[self.date_token]]
                    month = int(date_string.split('/')[1])
                    day = int(date_string.split('/')[0])
                    year = int(date_string.split('/')[2])
                    valid_date = True
                    log.info('date: %s/%s/%s' % (day, month, year))
                    # time
                    time_string = data[self.data_index[self.time_token]]
                    valid_time = True
                    hour = int(time_string.split(':')[0])
                    minute = int(time_string.split(':')[1])
                    second = int(time_string.split(':')[2])
                    log.info('time: %s:%s:%s' % (hour, minute, second))

                    if (year is not None) and (hour is not None):
                        self.dg_time = dt.datetime(year, month, day, hour, minute, second)

            except ValueError:
                log.error("skipping line %s" % count)
                continue
            count += 1

        if self.num_samples != count:
            self.depth.resize(count)
            self.speed.resize(count)
            self.temperature.resize(count)
            self.salinity.resize(count)
            self.num_samples = count
