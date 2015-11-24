from __future__ import absolute_import, division, print_function, unicode_literals

import datetime as dt
import numpy as np
import logging

log = logging.getLogger(__name__)

from ..base_format import BaseFormat, FormatError
from ... import __version__
from ...ssp_dicts import Dicts


class Sippican(BaseFormat):

    # A dictionary to resolve sensor type from probe type
    sensor_index = {
        Dicts.probe_types["Deep Blue"]: Dicts.sensor_types["XBT"],
        Dicts.probe_types["T-10"]: Dicts.sensor_types["XBT"],
        Dicts.probe_types["T-11 (Fine Structure)"]: Dicts.sensor_types["XBT"],
        Dicts.probe_types["T-4"]: Dicts.sensor_types["XBT"],
        Dicts.probe_types["T-5"]: Dicts.sensor_types["XBT"],
        Dicts.probe_types["T-5/20"]: Dicts.sensor_types["XBT"],
        Dicts.probe_types["T-7"]: Dicts.sensor_types["XBT"],
        Dicts.probe_types["XSV-01"]: Dicts.sensor_types["XSV"],
        Dicts.probe_types["XSV-02"]: Dicts.sensor_types["XSV"],
        Dicts.probe_types["XCTD-1"]: Dicts.sensor_types["XCTD"],
        Dicts.probe_types["XCTD-2"]: Dicts.sensor_types["XCTD"]
    }

    def __init__(self, file_content):
        super(Sippican, self).__init__(file_content)
        self.name = "SPC"
        self.driver = self.name + (".%s" % __version__)

        log.info("reading ...")
        lines = self.file_content.splitlines()
        self.is_var_alpha = False

        self._read_header(lines)
        self._read_body(lines)

    def _read_header(self, lines):
        log.info("reading Sippican > header")
        start_token = 'Depth (m)'
        date_token = 'Date of Launch'
        time_token = 'Time of Launch'
        latitude_token = 'Latitude'
        longitude_token = 'Longitude'
        filename_token = 'Raw Data Filename'
        salinity_token = '// Sound velocity derived with assumed salinity'
        probe_token = 'Probe Type'
        field_token = 'Field'
        var_alpha_start_token = '// Data'  # There's a funny file format where this is beginning marker
        var_alpha_salinity_token = 'Salinity'

        year = None
        month = None
        day = None
        hour = None
        minute = None
        second = None
        for line in lines:

            line = self.replace_non_ascii_byte(line)

            if line[:len(start_token)] == start_token:  # use a token to find the initial data offset
                self.samples_offset += 1
                log.info("samples offset: %s" % self.samples_offset)
                break

            elif (line[:len(var_alpha_start_token)] == var_alpha_start_token) \
                    and (len(line) <= len(var_alpha_start_token)):  # token for variant alpha of the format
                self.is_var_alpha = True
                self.samples_offset += 1
                log.info("samples offset: %s [var alpha]" % self.samples_offset)
                break

            elif line[:len(date_token)] == date_token:  # retrieve date
                date_str = line.split()[-1]
                try:
                    month, day, year = [int(i) for i in date_str.split('/')]
                except ValueError:
                    raise FormatError("issue in casting the date format: %s" % date_str)
                log.info("date: %s / %s / %s" % (month, day, year))

            elif line[:len(time_token)] == time_token:  # retrieve time
                time_str = line.split()[-1]
                try:
                    hour, minute, second = [int(i) for i in time_str.split(':')]
                except ValueError:
                    raise FormatError("issue in casting the time format: %s" % time_str)
                log.info("time: %s : %s : %s" % (hour, minute, second))

            elif line[:len(latitude_token)] == latitude_token:
                lat_str = line.split(':')[-1].lstrip().strip()
                if len(lat_str) > 0:
                    try:
                        lat_deg = int(line.split()[-2])
                        lat_min = float(line.split()[-1][:-1])
                        lat_dir = line.split()[-1][-1]
                        self.latitude = lat_deg + lat_min / 60.
                        if lat_dir == 'S':
                            self.latitude *= -1
                        log.info("lat: %s" % self.latitude)
                    except ValueError:
                        raise FormatError("issue in casting the latitude format: %s" % lat_str)
                else:
                    self.latitude = None
                    log.info("lat: invalid")

            elif line[:len(longitude_token)] == longitude_token:
                lon_str = line.split(':')[-1].lstrip().strip()
                if len(lon_str) > 0:
                    try:
                        lon_deg = int(line.split()[-2])
                        lon_min = float(line.split()[-1][:-1])
                        lon_dir = line.split()[-1][-1]
                        self.longitude = lon_deg + lon_min / 60.
                        log.info("long: %s" % self.longitude)
                        if lon_dir == 'W':
                            self.longitude *= -1
                    except ValueError:
                        raise FormatError("issue in casting the longitude format: %s" % lon_str)
                else:
                    self.longitude = None
                    log.info("long: invalid")

            elif line[:len(filename_token)] == filename_token:
                self.original_path = line.split()[-1]
                log.info("filename: %s" % self.original_path)

            elif line[:len(salinity_token)] == salinity_token:
                sal_str = line.split()[-2]
                try:
                    self.input_salinity = float(sal_str)
                except ValueError:
                    raise FormatError("issue in casting the salinity format: %s" % sal_str)
                log.info("salinity: %s" % self.input_salinity)

            elif line[:len(var_alpha_salinity_token)] == var_alpha_salinity_token:
                sal_str = line.split()[-2]
                try:
                    self.input_salinity = float(sal_str)
                except ValueError:
                    raise FormatError("issue in casting the salinity format: %s [var alpha]" % sal_str)
                self.is_var_alpha = True
                log.info("salinity: %s [var alpha]" % self.input_salinity)

            elif line[:len(probe_token)] == probe_token:
                try:
                    self.probe_type = Dicts.probe_types[line.split(':')[-1].lstrip().strip()]
                    self.sensor_type = self.sensor_index[self.probe_type]
                    log.info("probe type: %s" % self.sensor_type)

                except (IndexError, KeyError):
                    self.probe_type = Dicts.probe_types['Unknown']
                    self.sensor_type = Dicts.sensor_types['Unknown']
                    log.info("probe type: unknown")

            elif line[:len(field_token)] == field_token:
                column = int(line[5]) - 1
                probe_type = line.split()[2]
                self.data_index[probe_type] = int(column)
                self.is_var_alpha = True
                log.info("data index: %s [var alpha]" % self.data_index[probe_type])

            self.samples_offset += 1

        self.num_samples = len(lines) - self.samples_offset
        if self.num_samples == 0:
            raise FormatError("unable to parse the data samples")
        log.info("max samples: %s" % self.num_samples)

        if (year is not None) and (hour is not None):
            self.dg_time = dt.datetime(year, month, day, hour, minute, second)

        self.depth = np.zeros(self.num_samples)
        self.speed = np.zeros(self.num_samples)
        self.temperature = np.zeros(self.num_samples)
        self.salinity = np.zeros(self.num_samples)

        log.info("sensor type: %s" % self.sensor_type)
        log.info("var alpha: %s" % self.is_var_alpha)

    def _read_body(self, lines):
        log.info("reading > body")
        if self.sensor_type == Dicts.sensor_types["XBT"]:
            self.salinity[:] = self.input_salinity

        count = 0
        for line in lines[self.samples_offset:len(lines)]:

            # skip empty lines
            if len(line.split()) == 0:
                continue

            try:
                if not self.is_var_alpha:

                    field_count = 0
                    fields = line.split()

                    if self.sensor_type == Dicts.sensor_types["XBT"]:
                        if len(fields) < 3:
                            raise FormatError("too few fields for line: %s" % line)

                        # skip 0-speed value
                        if float(fields[2]) == 0.0:
                            log.info("skipping 0-speed row")
                            continue

                        for field in fields:
                            if field_count == 0:
                                self.depth[count] = field
                            elif field_count == 1:
                                self.temperature[count] = field
                            elif field_count == 2:
                                self.speed[count] = field
                            field_count += 1

                    elif self.sensor_type == Dicts.sensor_types["XSV"]:
                        if len(fields) < 2:
                            raise FormatError("too few fields for line: %s" % line)

                        # skip 0-speed value
                        if float(fields[1]) == 0.0:
                            log.info("skipping 0-speed row")
                            continue

                        for field in fields:
                            if field_count == 0:
                                self.depth[count] = field
                            elif field_count == 1:
                                self.speed[count] = field
                            field_count += 1

                    elif self.sensor_type == Dicts.sensor_types["XCTD"]:
                        if len(fields) < 6:
                            raise FormatError("too few fields for line: %s" % line)

                        # skip 0-speed value
                        if float(fields[4]) == 0.0:
                            log.info("skipping 0-speed row")
                            continue

                        for field in fields:
                            if field_count == 0:
                                self.depth[count] = field
                            elif field_count == 1:
                                self.temperature[count] = field
                            elif field_count == 2:
                                # conductivity = field
                                pass
                            elif field_count == 3:
                                self.salinity[count] = field
                            elif field_count == 4:
                                self.speed[count] = field
                            elif field_count == 5:
                                # density = field
                                pass
                            elif field_count == 6:
                                # status = field
                                pass
                            field_count += 1

                else:  # var alpha

                    fields = line.split()

                    if self.sensor_type == Dicts.sensor_types["XBT"]:

                        # skip 0-speed value
                        if float(fields[self.data_index["Sound"]]) == 0.0:
                            log.info("skipping 0-speed row")
                            continue

                        self.depth[count] = float(fields[self.data_index["Depth"]])
                        self.speed[count] = float(fields[self.data_index["Sound"]])
                        self.temperature[count] = float(fields[self.data_index["Temperature"]])

                    elif self.sensor_type == Dicts.sensor_types["XSV"]:
                        raise FormatError("No sample data file seen for XSV in this format, please send us this file!")

                    elif self.sensor_type == Dicts.sensor_types["XCTD"]:

                        # skip 0-speed value
                        if float(fields[self.data_index["Sound"]]) == 0.0:
                            log.info("skipping 0-speed row")
                            continue

                        self.depth[count] = float(fields[self.data_index["Depth"]])
                        self.speed[count] = float(fields[self.data_index["Sound"]])
                        self.temperature[count] = float(fields[self.data_index["Temperature"]])
                        self.salinity[count] = float(fields[self.data_index["Salinity"]])

            except Exception as e:
                log.error("issue in reading line #%s: %s" % (count, e))
                break
            count += 1

        if self.num_samples != count:
            self.depth.resize(count)
            self.speed.resize(count)
            self.temperature.resize(count)
            self.salinity.resize(count)
            self.num_samples = count
