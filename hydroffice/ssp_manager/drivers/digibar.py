from __future__ import absolute_import, division, print_function, unicode_literals

import datetime as dt
import numpy as np
import logging

log = logging.getLogger(__name__)

from .base_format import BaseFormat, FormatError
from ..ssp_dicts import Dicts
from .. import __version__


class DigibarPro(BaseFormat):

    def __init__(self, file_content, input_format):
        super(DigibarPro, self).__init__(file_content=file_content)

        if input_format != Dicts.import_formats["DIGIBAR_PRO"]:
            raise FormatError("invalid import format for this driver: %s" % input_format)

        self.name = "DGP"
        self.model = input_format
        self.driver = "%s.%s.%s" % (self.name, Dicts.first_match(Dicts.import_formats, input_format), __version__)

        log.info("reading ...")
        lines = self.file_content.splitlines()

        self._read_header(lines)
        self._read_body(lines)

    def _read_header(self, lines):
        log.info("reading > header")

        token_cast_time = "DATE:"

        for line in lines:

            if line[:len(token_cast_time)] == token_cast_time:
                try:
                    fields = line.split(" ")
                    if len(fields) == 2:
                        date_fields = fields[0].split(':')

                        if len(date_fields) == 2:
                            # we are assuming that the cast time is after 2000
                            year = 2000 + int(date_fields[-1][:2])
                            yr_day = int(date_fields[-1][2:])
                            self.dg_time = dt.datetime(year, 1, 1) + dt.timedelta(yr_day - 1)
                            # print(self.dg_time)
                        time_fields = fields[1].split(':')

                        if len(time_fields) == 2:
                            hour = int(time_fields[-1][:2])
                            minute = int(time_fields[-1][2:4])
                            self.dg_time += dt.timedelta(0, 0, 0, 0, minute, hour)

                        log.info("date: %s" % self.dg_time)

                except ValueError:
                    log.error("unable to parse date and time from: %s" % line)

        self.probe_type = Dicts.probe_types["SVP"]
        log.info("probe type: %s" % self.probe_type)
        self.sensor_type = Dicts.sensor_types["SVP"]
        log.info("sensor type: %s" % self.sensor_type)

        self.num_samples = len(lines)
        log.info("max number of samples: %s" % self.num_samples)

        self.depth = np.zeros(self.num_samples)
        self.speed = np.zeros(self.num_samples)
        self.temperature = np.zeros(self.num_samples)
        self.salinity = np.zeros(self.num_samples)

    def _read_body(self, lines):
        log.info("reading > body")

        count = 0
        samples = 0
        for line in lines:

            # Skip over the header
            if count < 5:
                count += 1
                continue

            # In case an incomplete file comes through
            try:
                dpt, spd, tmp = line.split()

                if spd == 0.0:
                    log.info("skipping 0-speed row: %s" % line)
                    count += 1
                    continue

                self.depth[samples] = dpt
                self.speed[samples] = spd
                self.temperature[samples] = tmp
                log.info("%d %7.1f %7.1f %5.1f"
                         % (samples, self.depth[samples], self.speed[samples], self.temperature[samples]))

            except ValueError:
                log.error("skipping line %s" % count)
                count += 1
                continue

            samples += 1
            count += 1

        log.info("good samples: %s" % samples)

        if self.num_samples != samples:
            log.info("resizing from %s to %s" % (self.num_samples, samples))
            self.depth.resize(samples)
            self.speed.resize(samples)
            self.temperature.resize(samples)
            self.salinity.resize(samples)
            self.num_samples = samples


class DigibarS(BaseFormat):

    def __init__(self, file_content, input_format):
        super(DigibarS, self).__init__(file_content=file_content)

        if input_format != Dicts.import_formats["DIGIBAR_S"]:
            raise FormatError("invalid import format for this driver: %s" % input_format)

        self.name = "DGS"
        self.model = input_format
        name_format = [key for key, value in Dicts.import_formats.items() if value == input_format][0]
        self.driver = "%s.%s.%s" % (self.name, name_format, __version__)

        log.info("reading ...")
        lines = self.file_content.splitlines()

        self._read_header(lines)
        self._read_body(lines)

    def _read_header(self, lines):
        log.info("reading > header")

        self.probe_type = Dicts.probe_types['SVP']
        log.info("probe type: %s" % self.probe_type)
        self.sensor_type = Dicts.sensor_types['SVP']
        log.info("sensor type: %s" % self.sensor_type)

        self.num_samples = len(lines)
        log.info("max number of samples: %s" % self.num_samples)
        self.depth = np.zeros(self.num_samples)
        self.speed = np.zeros(self.num_samples)
        self.temperature = np.zeros(self.num_samples)
        self.salinity = np.zeros(self.num_samples)

    def _read_body(self, lines):
        log.info("reading > body")

        count = 0
        first_time = None
        first_date = None
        for line in lines:

            try:
                # 7-30-13, 8:57:31, 1503.50, 0.80, 16.40, 4.10
                date, time, spd, dpt, tmp, other = line.split(",")
                if spd == 0.0:
                    log.info("skipping 0-value speed")
                    continue

                self.depth[count] = dpt
                self.speed[count] = spd
                self.temperature[count] = tmp

                log.info("%s %s %7.1f %7.1f %5.1f %s"
                         % (date, time, self.speed[count], self.depth[count], self.temperature[count], other))

                if not first_time:
                    first_time = time

                if not first_date:
                    first_date = date

            except ValueError:
                log.error("skipping line %s" % count)
                continue

            count += 1

        log.info("total count: %s" % count)

        if self.num_samples != count:
            log.info("resizing from %s to %s" % (self.num_samples, count))
            self.depth.resize(count)
            self.speed.resize(count)
            self.temperature.resize(count)
            self.salinity.resize(count)
            self.num_samples = count

        log.info("original date/time: %s %s" % (first_date, first_time))
        try:
            hour, minute, second = [int(i) for i in first_time.split(':')]
            # log.info("converted %s:%s:%s" % (hour, minute, second))
            month, day, year = [int(i) for i in first_date.split('-')]
            # log.info("converted %s/%s/%s" % (month, day, year))
            year += 2000
            self.dg_time = dt.datetime(year, month, day, hour, minute, second)
            log.info("converted date/time: %s" % self.dg_time)

        except ValueError:
            log.error("failure in date/time conversion")
