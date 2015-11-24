from __future__ import absolute_import, division, print_function, unicode_literals

import datetime as dt

import numpy as np
import logging

log = logging.getLogger(__name__)

from .base_format import BaseFormat
from .. import __version__
from ..ssp_dicts import Dicts


class Valeport(BaseFormat):
    # A dictionary to resolve sensor type from probe type
    sensor_index = {
        Dicts.probe_types['MONITOR SVP 500']: Dicts.sensor_types["SVPT"],
        Dicts.probe_types['MIDAS SVP 6000']: Dicts.sensor_types["SVPT"],
        Dicts.probe_types['MiniSVP']: Dicts.sensor_types["SVPT"],
        Dicts.probe_types['Unknown']: Dicts.sensor_types["Unknown"]
    }

    def __init__(self, file_content):
        super(Valeport, self).__init__(file_content=file_content)
        self.name = "VAL"

        self.start_data_token = ""
        self.time_token = ""
        self.latitude_token = 'Latitude'
        self.probe_type_token = ""
        self.filename_token = ""

        log.info("reading ...")
        lines = self.file_content.splitlines()

        self._read_header(lines)
        self._read_body(lines)

    def _read_header(self, lines):
        log.info("reading > header")

        if self.file_content[:3] == 'Now':  # MiniSVP
            self.driver = self.name + ".MiniSVP" + (".%s" % __version__)
            self.parse_mini_svp_header(lines)
        else:  # MIDAS or Monitor
            self.driver = self.name + ".MIDAS" + (".%s" % __version__)
            self.parse_midas_header(lines)

    def parse_mini_svp_header(self, lines):
        self.start_data_token = 'Pressure units:'
        self.time_token = 'Now'
        self.probe_type_token = 'MiniSVP:'

        self.samples_offset = 0
        for line in lines:
            if line[:len(self.start_data_token)] == self.start_data_token:
                self.samples_offset += 1
                break

            elif line[:len(self.time_token)] == self.time_token:
                try:
                    date_string = line.split()[1]
                    time_string = line.split()[2]
                    month = int(date_string.split('/')[1])
                    day = int(date_string.split('/')[0])
                    year = int(date_string.split('/')[2])
                    # print day, '/', month, '/', year
                    hour = int(time_string.split(':')[0])
                    minute = int(time_string.split(':')[1])
                    second = int(time_string.split(':')[2])
                    # print hour, ':', minute, ':', second
                    if (year is not None) and (hour is not None):
                        self.dg_time = dt.datetime(year, month, day, hour, minute, second)
                        log.info("date time: %s" % self.dg_time)
                except ValueError:
                    log.error("unable to parse date and time: %s" % line)

            elif line[:len(self.latitude_token)] == self.latitude_token:
                try:
                    self.latitude = float(line.split(':')[-1])
                    log.info("latitude: %s" % self.latitude)
                except ValueError:
                    log.error("unable to parse latitude: %s" % line)

            elif line[:len(self.probe_type_token)] == self.probe_type_token:
                self.probe_type = Dicts.probe_types['MiniSVP']
                try:
                    self.sensor_type = self.sensor_index[self.probe_type]
                    log.info("probe type: %s" % self.sensor_type)
                except KeyError:
                    log.error("unable to recognize probe type: %s" % line)
                    self.sensor_type = Dicts.sensor_types['Unknown']
            self.samples_offset += 1

        self.num_samples = len(lines) - self.samples_offset
        log.info('total samples: %s' % self.num_samples)

        self.depth = np.zeros(self.num_samples)
        self.speed = np.zeros(self.num_samples)
        self.temperature = np.zeros(self.num_samples)
        self.salinity = np.zeros(self.num_samples)

    def parse_midas_header(self, lines):
        self.start_data_token = 'Date / Time'
        self.time_token = 'Time Stamp :'
        self.filename_token = 'File Name :'
        self.probe_type_token = 'Model Name :'

        # There is no lat/long in the .000 file format
        self.latitude = None
        self.longitude = None

        self.samples_offset = 0
        for line in lines:

            if line[:len(self.start_data_token)] == self.start_data_token:
                self.samples_offset += 1
                break

            elif line[:len(self.time_token)] == self.time_token:
                try:
                    date_string = line.split()[-2]
                    time_string = line.split()[-1]
                    day, month, year = [int(i) for i in date_string.split('/')]
                    hour, minute, second = [int(i) for i in time_string.split(':')]
                    self.dg_time = dt.datetime(year, month, day, hour, minute, second)
                    log.info("time: %s" % self.dg_time)
                except ValueError:
                    log.error("unable to parse time: %s" % line)

            elif line[:len(self.filename_token)] == self.filename_token:
                try:
                    self.original_path = line.split()[-1]
                    log.info("filename: %s" % self.original_path)
                except ValueError:
                    log.error("unable to parse filename: %s" % self.original_path)

            elif line[:len(self.probe_type_token)] == self.probe_type_token:
                try:
                    self.probe_type = Dicts.probe_types[line.split(':')[-1].strip()]
                    log.info("probe type: %s" % self.probe_type)
                except (ValueError, KeyError):
                    log.error("unable to parse probe type: %s" % line)
                    self.probe_type = Dicts.probe_types['Unknown']

                try:
                    self.sensor_type = self.sensor_index[self.probe_type]
                    log.info("sensor type: %s" % self.sensor_type)
                except KeyError:
                    log.error("unable to find sensor type: %s" % line)
                    self.sensor_type = Dicts.sensor_types['Unknown']

            self.samples_offset += 1

        self.num_samples = len(lines) - self.samples_offset
        log.info('total samples: %s' % self.num_samples)

        self.depth = np.zeros(self.num_samples)
        self.speed = np.zeros(self.num_samples)
        self.temperature = np.zeros(self.num_samples)
        self.salinity = np.zeros(self.num_samples)

    def _read_body(self, lines):
        log.info("reading > body")
        if self.file_content[:3] == 'Now':  # MiniSVP
            self.parse_mini_svp_body(lines)
        else:  # MIDAS or Monitor
            self.parse_midas_body(lines)

        log.info("number of samples: %s" % self.num_samples)

    def parse_mini_svp_body(self, lines):
        count = 0
        for line in lines[self.samples_offset:len(lines)]:
            try:
                # print count
                data = line.split()

                # Skipping invalid data (above water, negative temperature or crazy sound speed)
                if float(data[0]) < 0.0 or float(data[1]) < -2.0 or float(data[2]) < 1400.0 or float(data[2]) > 1650.0:
                    continue

                self.depth[count] = float(data[0])
                self.temperature[count] = float(data[1])
                self.speed[count] = float(data[2])
                count += 1

            except ValueError:
                log.error("unable to parse: %s" % line)
                break

        if self.num_samples != count:
            self.depth.resize(count)
            self.speed.resize(count)
            self.temperature.resize(count)
            self.salinity.resize(count)
            self.num_samples = count

    def parse_midas_body(self, lines):

        count = 0
        null_ss_count = 0
        for line in lines[self.samples_offset:len(lines)]:
            try:
                # In case an incomplete file comes through
                if self.sensor_type == Dicts.sensor_types["SVPT"]:
                    s_date, s_time, self.speed[count], self.depth[count], self.temperature[count] = line.split()

                if self.speed[count] == 0.0:
                    null_ss_count += 1
                    continue

            except ValueError:
                log.error("skipping line: %s" % count)
                break

            count += 1

        log.info("skipped %s lines with null sound speed" % null_ss_count)

        if self.num_samples != count:
            self.depth.resize(count)
            self.speed.resize(count)
            self.temperature.resize(count)
            self.salinity.resize(count)
            self.num_samples = count
