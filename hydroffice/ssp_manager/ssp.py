from __future__ import absolute_import, division, print_function, unicode_literals

import math
import socket
import copy
from datetime import datetime
import functools
import operator
from io import open
import numpy as np
import logging

log = logging.getLogger(__name__)

from .ssp_dicts import Dicts
from .ssp_aux import SspAux
from . import oceanography
from .drivers.sippican.sippican import Sippican
from .drivers.valeport import Valeport
from .drivers.turo import Turo
from .drivers.seabird import Seabird
from .drivers.digibar import DigibarPro, DigibarS
from .drivers.castaway import Castaway
from .drivers.unb import Unb
from .drivers.idronaut import Idronaut
from .drivers.saiv import Saiv
from .helper import SspError


class SspData(object):
    """ an SSP class that holds SSP data """

    def __init__(self):

        self.date_time = None
        self.longitude = None
        self.latitude = None
        self.survey_name = "default"
        self.original_path = "N/A"
        self.sensor_type = None
        self.source_info = ""
        self.driver = "UNKNOWN"

        self.data = None
        self.raw_data = None
        self.sis_data = None

        self.tx_data = None

    # ### input functions ###

    def read_input_file_by_format(self, input_file, input_format):

        file_content = None
        if input_format == Dicts.import_formats["TURO"]:  # we directly pass the filename for opening with NetCDF lib
            pass
        else:
            if input_format == Dicts.import_formats["IDRONAUT"]:
                infile = open(input_file, 'r', encoding='latin-1')
            else:
                infile = open(input_file, 'r')
            file_content = infile.read()
            infile.close()

        if input_format == Dicts.import_formats["CASTAWAY"]:
            ss_data = Castaway(file_content)
        elif input_format == Dicts.import_formats["DIGIBAR_PRO"]:
            ss_data = DigibarPro(file_content, input_format)
        elif input_format == Dicts.import_formats["DIGIBAR_S"]:
            ss_data = DigibarS(file_content, input_format)
        elif input_format == Dicts.import_formats["IDRONAUT"]:
            ss_data = Idronaut(file_content)
        elif input_format == Dicts.import_formats["SIPPICAN"]:
            ss_data = Sippican(file_content)
        elif input_format == Dicts.import_formats["SAIV"]:
            ss_data = Saiv(file_content)
        elif input_format == Dicts.import_formats["SEABIRD"]:
            ss_data = Seabird(file_content)
        elif input_format == Dicts.import_formats["TURO"]:
            ss_data = Turo(input_file)
        elif input_format == Dicts.import_formats["UNB"]:
            ss_data = Unb(file_content)
        elif input_format == Dicts.import_formats["VALEPORT_MIDAS"] \
                or input_format == Dicts.import_formats["VALEPORT_MINI_SVP"] \
                or input_format == Dicts.import_formats["VALEPORT_MONITOR"]:
            ss_data = Valeport(file_content)
        else:
            raise SspError("Unknown file type to read: %s" % input_format)
        ss_data.original_path = input_file

        log.info("raw: %s" % ss_data)

        # set the collected information
        ss_data.convert_ssp(self)

    # #### setting/getting functions ###

    def set_time(self, ssp_time):
        """ set the time of the cast """
        self.date_time = ssp_time

    def set_position(self, latitude, longitude):
        """ set the position of the cast """
        self.latitude = latitude
        self.longitude = longitude

    def set_sis_samples(self, depth, speed, temperature, salinity, source, flag):
        """ copy the sis data into a multi array """
        self.sis_data = np.vstack([depth, speed, temperature, salinity, source, flag])
        log.info("resulting sis data size: (%s, %s)" % self.sis_data.shape)

    def set_raw_samples(self, depth, speed, temperature, salinity, source, flag):
        """ copy the raw data into a multi array """
        self.raw_data = np.vstack([depth, speed, temperature, salinity, source, flag])
        log.info("resulting raw data size: (%s, %s)" % self.raw_data.shape)

    def set_samples(self, depth, speed, temperature, salinity, source, flag):
        """ copy the processed data into a multi array """
        self.data = np.vstack([depth, speed, temperature, salinity, source, flag])
        log.info("resulting processed data size: (%s, %s)" % self.data.shape)

    def sorting_time(self):
        """ used to sort by time """
        if not self.date_time:
            log.info("missing date/time for %s/%s returning fake: %s"
                     % (self.sensor_type, self.source_info, datetime(1, 1, 1)))
            return datetime(1, 1, 1)
        else:
            return self.date_time

    def store_raw(self):
        """ storing raw data """
        log.info("storing raw data")
        self.raw_data = np.empty_like(self.data)
        self.raw_data[:] = self.data

    def restart_processing(self):
        """ Clean the sis data and the source_info, substitute processed with raw """
        self.sis_data = None
        log.info("cleaned sis data")

        self.source_info = self.source_info.split('/')[0]
        log.info("cleaned source_info: %s" % self.source_info)

        self.data = np.empty_like(self.raw_data)
        self.data[:] = self.raw_data
        log.info("dropped processed data")

    def modify_source_info(self, added_info):
        source_info_tokens = self.source_info.split('/')
        self.source_info = str()
        log.info("modifying source info with: %s" % added_info)
        info_found = False
        for i in range(len(source_info_tokens)):
            if added_info[:10] in source_info_tokens[i]:
                info_found = True
                source_info_tokens[i] = added_info

            if i == 0:
                self.source_info = source_info_tokens[i]
            else:
                self.source_info += "/" + source_info_tokens[i]

        if not info_found:
            self.source_info += "/" + added_info

    # ### processing functions ###

    def reduce_up_down(self, up_or_down_cast):

        if self.data.shape[1] == 0:
            return

        good_pts = (self.data[Dicts.idx['flag'], :] == 0)
        # find the max depth for good points
        max_depth = self.data[Dicts.idx['depth'], good_pts].max()

        # loop through using the max depth as a switch
        reached_max_depth = False
        for count in range(self.data.shape[1]):

            if self.data[Dicts.idx['depth'], count] == max_depth:
                reached_max_depth = True

            if (up_or_down_cast == Dicts.ssp_directions["up"] and not reached_max_depth) \
                    or (up_or_down_cast == Dicts.ssp_directions["down"] and reached_max_depth):
                self.data[Dicts.idx['flag'], count] = 1

        # purge points that were flagged
        self.data = SspAux.purge_flagged_samples(self.data)

    def extend(self, extender, ext_type):
        """ Use the extender samples to extend the profile """
        log.info("extension source type: %s" % ext_type)
        extender.data[Dicts.idx['source'], :] = ext_type

        # find the max valid depth in the current profile
        if self.data.shape[1] > 0:
            good_pts = (self.data[Dicts.idx['flag'], :] == 0)
            max_depth = self.data[Dicts.idx['depth'], good_pts].max()
        else:
            max_depth = 0

        # find the depth values in the extender that are deeper than the current (valid) max depth
        ind2 = (extender.data[Dicts.idx['depth'], :] > max_depth)
        if ind2.size <= 0:
            log.info("nothing to extend with")
            return

        self.data = np.hstack([self.data, extender.data[:, ind2]])

    def insert_sample(self, depth, speed, temperature, salinity, source, flag=0):
        """ used to insert a new sample into the cast """

        # create new empty arrays to store the new cast
        depth2 = np.zeros(self.data.shape[1] + 1)
        speed2 = np.zeros(self.data.shape[1] + 1)
        temperature2 = np.zeros(self.data.shape[1] + 1)
        salinity2 = np.zeros(self.data.shape[1] + 1)
        source2 = np.zeros(self.data.shape[1] + 1)
        flag2 = np.zeros(self.data.shape[1] + 1)

        done_insert = False

        # append at the end
        if depth >= self.data[Dicts.idx['depth'], self.data.shape[1] - 1]:
            # copy all the previous data
            for count in range(self.data.shape[1]):
                depth2[count] = self.data[Dicts.idx['depth'], count]
                speed2[count] = self.data[Dicts.idx['speed'], count]
                temperature2[count] = self.data[Dicts.idx['temperature'], count]
                salinity2[count] = self.data[Dicts.idx['salinity'], count]
                source2[count] = self.data[Dicts.idx['source'], count]
                flag2[count] = self.data[Dicts.idx['flag'], count]

            # add passed values
            depth2[-1] = depth
            if not speed:  # copy the previous value
                speed2[-1] = speed2[-2]
            else:
                speed2[-1] = speed
            if not temperature:  # copy the previous value
                temperature2[-1] = temperature2[-2]
            else:
                temperature2[-1] = temperature
            if not salinity:  # copy the previous value
                salinity2[-1] = salinity2[-2]
            else:
                salinity2[-1] = salinity
            source2[-1] = source
            flag2[-1] = flag

        # append at the beginning
        elif depth <= self.data[Dicts.idx['depth'], 0]:
            # move of 1 position all the previous data
            for count in range(self.data.shape[1]):
                depth2[count + 1] = self.data[Dicts.idx['depth'], count]
                speed2[count + 1] = self.data[Dicts.idx['speed'], count]
                temperature2[count + 1] = self.data[Dicts.idx['temperature'], count]
                salinity2[count + 1] = self.data[Dicts.idx['salinity'], count]
                source2[count + 1] = self.data[Dicts.idx['source'], count]
                flag2[count + 1] = self.data[Dicts.idx['flag'], count]

            # copy the passed value at the beginning
            depth2[0] = depth
            if not speed:  # copy the next value
                speed2[0] = speed2[1]
            else:
                speed2[0] = speed
            if not temperature:  # copy the next value
                temperature2[0] = temperature2[1]
            else:
                temperature2[0] = temperature
            if not salinity:  # copy the next value
                salinity2[0] = salinity2[1]
            else:
                salinity2[0] = salinity
            source2[0] = source
            flag2[0] = flag

        # the point to add is in the middle of the cast
        else:
            # prepare the input values in case absent (interpolated), in case first or last the same value is returned
            if not speed:
                speed = np.interp(depth, self.data[Dicts.idx['depth'], :], self.data[Dicts.idx['speed'], :])
            if not temperature:
                temperature = np.interp(depth, self.data[Dicts.idx['depth'], :], self.data[Dicts.idx['temperature'], :])
            if not salinity:
                salinity = np.interp(depth, self.data[Dicts.idx['depth'], :], self.data[Dicts.idx['salinity'], :])

            insert = 0
            for count in range(self.data.shape[1] + 1):
                # it is the case in which the passed point is inserted
                if (self.data[Dicts.idx['depth'], insert] >= depth) and (not done_insert):
                    depth2[count] = depth
                    speed2[count] = speed
                    temperature2[count] = temperature
                    salinity2[count] = salinity
                    source2[count] = source
                    flag2[count] = flag
                    done_insert = True

                else:  # copy all the other data
                    depth2[count] = self.data[Dicts.idx['depth'], insert]
                    speed2[count] = self.data[Dicts.idx['speed'], insert]
                    temperature2[count] = self.data[Dicts.idx['temperature'], insert]
                    salinity2[count] = self.data[Dicts.idx['salinity'], insert]
                    source2[count] = self.data[Dicts.idx['source'], insert]
                    flag2[count] = self.data[Dicts.idx['flag'], insert]
                    insert += 1

        # set the new cast
        self.set_samples(depth=depth2, speed=speed2, temperature=temperature2, salinity=salinity2,
                         source=source2, flag=flag2)

    def toggle_flag(self, y_range, x_range, data_key, flag_mode):

        if flag_mode == Dicts.inspections_mode['Flag']:
            reject = 1
        elif flag_mode == Dicts.inspections_mode['Unflag']:
            reject = 0
        else:
            log.error("invalid flag: %s" % flag_mode)
            return

        x_range.sort()
        y_range.sort()

        # How do I break this over a few lines?
        ind = (self.data[Dicts.idx[data_key], :] >= x_range[0]) & \
              (self.data[Dicts.idx[data_key], :] <= x_range[1]) & \
              (self.data[Dicts.idx['depth'], :] >= y_range[0]) & \
              (self.data[Dicts.idx['depth'], :] <= y_range[1])

        self.data[Dicts.idx['flag'], ind] = reject

    def replace_samples(self, source, data_key):

        new_data = np.interp(self.data[Dicts.idx['depth'], :], source.data[Dicts.idx['depth'], :],
                             source.data[Dicts.idx[data_key], :])

        self.data[Dicts.idx[data_key], :] = new_data

    def calc_salinity(self):
        if not self.latitude:
            latitude = 30.0
        else:
            latitude = self.latitude

        for count in range(self.data.shape[1]):
            self.data[Dicts.idx['salinity'], count] = oceanography.salinity(self.data[Dicts.idx['depth'], count],
                                                                            self.data[Dicts.idx['speed'], count],
                                                                            self.data[Dicts.idx['temperature'], count],
                                                                            latitude)
        self.modify_source_info("calc. salinity")

    def calc_speed(self):
        if not self.latitude:
            latitude = 30.0
        else:
            latitude = self.latitude

        for count in range(self.data.shape[1]):
            self.data[Dicts.idx['speed'], count] = oceanography.soundspeed(self.data[Dicts.idx['depth'], count],
                                                                           self.data[Dicts.idx['temperature'], count],
                                                                           self.data[Dicts.idx['salinity'], count],
                                                                           latitude)
        self.modify_source_info("calc. speed")

    def calc_attenuation(self, frequency, ph):
        depth = np.zeros(self.data.shape[1])
        attenuation = np.zeros(self.data.shape[1])
        for count in range(self.data.shape[1]):
            depth[count] = self.data[Dicts.idx['depth'], count]
            attenuation[count] = oceanography.attenuation(frequency, self.data[Dicts.idx['temperature'], count],
                                                          self.data[Dicts.idx['salinity'], count], depth[count], ph)

        return attenuation, depth

    def calc_cumulative_attenuation(self, frequency, ph):
        attenuation, depth = self.calc_attenuation(frequency, ph)
        cumulative_attenuation = np.zeros(len(attenuation))

        total_loss = 0
        for count in range(len(attenuation) - 1):
            layer_loss = attenuation[count] * (depth[count + 1] - depth[count]) / 1000.0
            total_loss += layer_loss
            cumulative_attenuation[count] = total_loss / (depth[count + 1] / 1000.0)

        cumulative_attenuation[-1] = cumulative_attenuation[-2]

        return cumulative_attenuation, depth

    def calc_depth(self):
        if not self.latitude:
            latitude = 30.0
        else:
            latitude = self.latitude

        for count in range(self.data.shape[1]):
            self.data[Dicts.idx['depth'], count] = oceanography.press2depth(self.data[Dicts.idx['depth'], count],
                                                                            latitude)

        self.modify_source_info("calc. depth")

    # #### output functions ###

    def _get_clean_sorted_data(self):
        """ Make a copy of the depth sorted good data only """
        good_pts = (self.data[Dicts.idx['flag'], :] == 0)
        tmp_data = self.data[:, self.data[Dicts.idx['depth'], good_pts].argsort()]
        data = np.empty_like(tmp_data)
        data[:] = tmp_data
        return data

    def prepare_sis_data(self, thin=True):
        """ copy the processed data and (optionally) apply thinning """

        self.sis_data = np.empty_like(self.data)
        self.sis_data[:] = self.data

        if thin:
            self.sis_data = SspAux.thin_ssp(0.1, self.sis_data)

    def convert_km(self, kng_fmt, thin=True):
        """ convert to Kongsberg formats """

        # Before doing whatever, copy the processed data to sis data so that we can modify it
        self.prepare_sis_data(thin)

        # Make a few copies of the depth sorted good data only
        good_pts = (self.sis_data[Dicts.idx['flag'], :] == 0)
        tmp_data = self.sis_data[:, self.sis_data[Dicts.idx['depth'], good_pts].argsort()]
        data = np.empty_like(tmp_data)
        data[:] = tmp_data
        data2 = np.empty_like(tmp_data)
        data2[:] = tmp_data
        num_kept = np.count_nonzero(good_pts)

        last_depth = -1.0
        num_really_kept = 0
        for smp in range(num_kept):

            depth = data2[Dicts.idx['depth'], smp]

            # ignoring samples with less than 0.02 m separation or with negative depth or greater than 12k
            if (depth - last_depth < 0.02) or \
                    (depth < 0.0) or \
                    (depth > 12000.0):
                continue

            data[:, num_really_kept] = data2[:, smp]
            last_depth = data2[Dicts.idx['depth'], smp]
            num_really_kept += 1

        num_output = num_really_kept
        num_kept = num_really_kept

        # case when first valid measurement is not at a depth of zero
        if data[Dicts.idx['depth'], 0] > 0:
            num_output += 1

        # case when last valid measurement is not at a depth of 12000 m
        if data[Dicts.idx['depth'], num_kept - 1] < 12000:
            num_output += 1

        if not self.latitude:
            latitude = 0.0
        else:
            latitude = self.latitude

        if not self.longitude:
            longitude = 0.0
        else:
            longitude = self.longitude

        output = SspAux.get_km_prefix(kng_fmt)  # start with the format prefix
        if kng_fmt != Dicts.kng_formats['ASVP']:
            output += "{0:04d},".format(num_output)
            output += self.date_time.strftime("%H%M%S,%d,%m,%Y,")

        else:
            # e.g., ( SoundVelocity  1.0 0 201203212242 22.50000000 -156.50000000 -1 0 0 MVS01_00000 P 0035 )
            output += "( SoundVelocity  1.0 0 "
            output += self.date_time.strftime("%Y%m%d%H%M%S ")
            output += "%.7f %.7f -1 0 0 OMS01_00000 P %4d )\n" % (latitude, longitude, num_output)

        # Pull the first valid measurement up to depth of zero to meet KM real-time requirement
        if data[Dicts.idx['depth'], 0] > 0:

            if (kng_fmt == Dicts.kng_formats['S00']) or (kng_fmt == Dicts.kng_formats['S10']):
                output += "0.00,{0:0.1f},,,\r\n".format(float(data[Dicts.idx['speed'], 0]))

            elif (kng_fmt == Dicts.kng_formats['S01']) or (kng_fmt == Dicts.kng_formats['S12']):
                output += "0.00,{0:0.1f},{1:0.2f},{2:0.2f},\r\n".format(float(data[Dicts.idx['speed'], 0]),
                                                                        float(data[Dicts.idx['temperature'], 0]),
                                                                        float(data[Dicts.idx['salinity'], 0]))

            elif (kng_fmt == Dicts.kng_formats['S02']) or (kng_fmt == Dicts.kng_formats['S22']):
                output += "0.00,,{0:0.2f},{1:0.2f},\r\n".format(float(data[Dicts.idx['temperature'], 0]),
                                                                float(data[Dicts.idx['salinity'], 0]))
            elif kng_fmt == Dicts.kng_formats['ASVP']:
                output += "0.00 {0:0.2f}\n".format(float(data[Dicts.idx['speed'], 0]))

        for count in range(num_kept):
            if (kng_fmt == Dicts.kng_formats['S00']) or (kng_fmt == Dicts.kng_formats['S10']):
                output += "{0:0.2f},{1:0.1f},,,\r\n".format(float(data[Dicts.idx['depth'], count]),
                                                            float(data[Dicts.idx['speed'], count]))
            elif (kng_fmt == Dicts.kng_formats['S01']) or (kng_fmt == Dicts.kng_formats['S12']):
                output += "{0:0.2f},{1:0.1f},{2:0.2f},{3:0.2f},\r\n".format(float(data[Dicts.idx['depth'], count]),
                                                                            float(data[Dicts.idx['speed'], count]),
                                                                            float(
                                                                                data[Dicts.idx['temperature'], count]),
                                                                            float(data[Dicts.idx['salinity'], count]))
            elif (kng_fmt == Dicts.kng_formats['S02']) or (kng_fmt == Dicts.kng_formats['S22']):
                output += "{0:0.2f},,{1:0.2f},{2:0.2f},\r\n".format(float(data[Dicts.idx['depth'], count]),
                                                                    float(data[Dicts.idx['temperature'], count]),
                                                                    float(data[Dicts.idx['salinity'], count]))
            elif kng_fmt == Dicts.kng_formats['ASVP']:
                output += "{0:0.2f} {1:0.1f}\n".format(float(data[Dicts.idx['depth'], count]),
                                                       float(data[Dicts.idx['speed'], count]))

        # Add a final value at 12000m, from: Taira, K., Yanagimoto, D. and Kitagawa, S. (2005).,
        #  "Deep CTD Casts in the Challenger Deep, Mariana Trench", Journal of Oceanography, Vol. 61, pp. 447 t 454
        # TODO: add T/S at location of max depth in the current basin in between last observation and 12000m sample
        if data[Dicts.idx['depth'], num_kept - 1] < 12000:

            if (kng_fmt == Dicts.kng_formats['S00']) or (kng_fmt == Dicts.kng_formats['S10']):
                output += "12000.00,1675.8,,,\r\n"

            elif (kng_fmt == Dicts.kng_formats['S01']) or (kng_fmt == Dicts.kng_formats['S12']):
                output += "12000.00,1675.8,2.46,34.70,\r\n"

            elif (kng_fmt == Dicts.kng_formats['S02']) or (kng_fmt == Dicts.kng_formats['S22']):
                output += "12000.00,,2.46,34.70,\r\n"

            elif kng_fmt == Dicts.kng_formats['ASVP']:
                output += "12000.00 1675.8\n"

        if latitude >= 0:
            hem = "N"
        else:
            hem = "S"
        lat_min = int(60 * math.fabs(latitude - int(latitude)))
        lat_decimal_min = int(100 * (60 * math.fabs(latitude - int(latitude)) - lat_min))
        if kng_fmt != Dicts.kng_formats['ASVP']:
            output += "{0:02d}{1:02d}.{2:02d},{3:s},".format(int(math.fabs(latitude)), lat_min, lat_decimal_min, hem)

        if longitude > 180:  # We need our longitudes to span -180 to 180
            longitude -= 360
        if longitude < 0:
            hem = "W"
        else:
            hem = "E"
        lon_min = int(60 * math.fabs(longitude - int(longitude)))
        lon_decimal_min = int(100 * (60 * math.fabs(longitude - int(longitude)) - lon_min))
        if kng_fmt != Dicts.kng_formats['ASVP']:
            output += "{0:02d}{1:02d}.{2:02d},{3:s},".format(int(math.fabs(longitude)), lon_min, lon_decimal_min,
                                                             hem)
            output += "0.0,"
            output += "Source: " + self.source_info

        # calculate checksum, XOR of all bytes after the $
        checksum = functools.reduce(operator.xor, map(ord, output[1:len(output)]))
        if kng_fmt != Dicts.kng_formats['ASVP']:
            output += "*{0:02x}".format(checksum)
            output += "\\\r\n"

        return output

    def convert_elac(self):
        data = self._get_clean_sorted_data()
        num_samples = data.shape[1]

        if self.latitude:
            latitude = self.latitude
        else:
            latitude = 30.0

        output = '# depth   veloc.    temp.     salin.    cond.\n'
        output += '# [m]     [m/s]     [?C]      [o/oo]    [mmho/cm]\n'
        output += '\n'
        output += '.profile 0\n'

        for count in range(num_samples):
            if data[Dicts.idx['depth'], count] < 0.0:
                continue
            # 1.07   1809.87      0.00      0.00      0.00
            depth = self.data[Dicts.idx['depth'], count]
            if depth < 10.0:
                pad = "    "
            elif depth < 100.0:
                pad = "   "
            elif depth < 1000.0:
                pad = "  "
            elif depth < 10000.0:
                pad = " "
            else:
                pad = ""
            depth_str = "%s%.2f" % (pad, depth)

            speed = self.data[Dicts.idx['speed'], count]
            speed_str = "   %.2f" % speed

            temperature = self.data[Dicts.idx['temperature'], count]
            if temperature < 10.0:
                pad = "      "
            elif temperature < 100.0:
                pad = "     "
            temperature_str = "%s%.2f" % (pad, temperature)

            salinity = self.data[Dicts.idx['salinity'], count]
            if salinity < 10.0:
                pad = "      "
            elif salinity < 100.0:
                pad = "     "
            salinity_str = "%s%.2f" % (pad, salinity)

            pressure = oceanography.depth2press(depth, latitude)
            conductivity = oceanography.salinity2conductivity(salinity, pressure, temperature)
            if conductivity < 10.0:
                pad = "      "
            elif conductivity < 100.0:
                pad = "     "
            elif conductivity < 1000.0:
                pad = "    "
            conductivity_str = "%s%.2f" % (pad, conductivity)

            output += "%s%s%s%s%s\n" % (depth_str, speed_str, temperature_str, salinity_str, conductivity_str)

        return output

    def convert_unb(self):
        output = '2  # JWC watercolumn file Version\n'
        date_string = self.date_time.strftime("%Y %j %H:%M:%S") + " # date and time of observation\n"
        output += date_string
        output += "0000 000 00:00:00 # date and time of logging (when inserted into MB logging stream)\n"
        if self.latitude and self.longitude:
            output += "{0:0.7f} {1:0.7f} # lat and long of observation\n".format(float(self.latitude),
                                                                                 float(self.longitude))
        else:
            output += "0.000000 0.000000 # lat and long of observation\n"
        output += "0.000000 0.000000 # lat and long of ship when inserted\n"
        output += "{0:d} # no. of raw observations\n".format(self.data.shape[1])
        for i in range(10):
            output += "# blank line for future parameter {0:d} of 10\n".format(i + 1)

        for count in range(self.data.shape[1]):
            output += "{0:d} {1:0.4f} {2:0.2f} {3:0.4f} {4:0.4f} 0.0 {5:d}\n" \
                      "".format(count,
                                float(self.data[Dicts.idx['depth'], count]),
                                float(self.data[Dicts.idx['speed'], count]),
                                float(self.data[Dicts.idx['temperature'], count]),
                                float(self.data[Dicts.idx['salinity'], count]),
                                int(self.data[Dicts.idx['flag'], count]))
        return output

    def convert_pro(self):
        data = self._get_clean_sorted_data()
        num_samples = data.shape[1]

        # The first five lines are for comments it seems
        output = self.date_time.strftime("Date and time of observation:  %Y-%m-%d %H:%M:%S\n")
        if self.latitude and self.longitude:
            output += "Latitude/Longitude of observation: {0:0.7f} {1:0.7f}\n".format(float(self.latitude),
                                                                                      float(self.longitude))
        else:
            output += "Latitude/Longitude of observation: unknown\n"
        output += "\n"
        output += "\n"
        output += "\n"

        for count in range(num_samples):
            if data[Dicts.idx['depth'], count] < 0.0:
                continue
            output += "{0:0.2f} {1:0.2f} 0.000 0.000\n".format(float(data[Dicts.idx['depth'], count]),
                                                               float(data[Dicts.idx['speed'], count]))

        return output

    def convert_calc(self):

        last_depth = None
        data = self._get_clean_sorted_data()

        output = self.date_time.strftime("CALC,0001,%d-%m-%Y,1,meters\n")
        output += "AML SOUND VELOCITY PROFILER S/N:00000\n"
        output += self.date_time.strftime("DATE:%y%j TIME:%H:%M\n")
        output += "DEPTH OFFSET (M):00000.0\n"
        output += "DEPTH (M) VELOCITY (M/S) TEMP (C)\n"

        for count in range(data.shape[1]):
            if data[Dicts.idx['depth'], count] < 0.0:
                continue
            output += "{0:5.1f} {1:4.2f} {2:1.3f}\n".format(float(data[Dicts.idx['depth'], count]),
                                                            float(data[Dicts.idx['speed'], count]),
                                                            float(data[Dicts.idx['temperature'], count]))
            last_depth = data[Dicts.idx['depth'], count]

        output += " 0  0  0\n"
        output += "*** NAV ****\n"
        output += "Bottom Depth (m): %.1f\n" % last_depth
        output += "Ship's Log (N): 0.0\n"

        deg = abs(int(self.latitude))
        min_value = abs((self.latitude - deg) * 60.0)
        min_whole = int(min_value)
        min_frac = min_value - min_whole
        if self.latitude < 0.0:
            hemi = "S"
        else:
            hemi = "N"

        output += "# LAT ( ddmm.mmmmmmm,N): %d%0.2d.%0.7d,%c\n" % (deg, min_whole, min_frac, hemi)

        # LON (dddmm.mmmmmmm,N):  4105.3385200,N
        deg = abs(int(self.longitude))
        min_value = abs((abs(self.longitude) - deg) * 60.0)
        if deg > 180:
            deg -= 360
        min_whole = int(min_value)
        min_frac = min_value - min_whole
        if self.longitude < 0.0:
            hemi = "W"
        else:
            hemi = "E"

        # self.print_info("Lon:", self.longitude, deg, min_value, min_whole, min_frac, hemi)

        output += "# LON (dddmm.mmmmmmm,N): %d%0.2d.%0.7d,%c\n" % (deg, min_whole, min_frac, hemi)

        output += self.date_time.strftime("Time [hh:mm:ss.ss]: %H:%M:%S.00\n")
        output += self.date_time.strftime("Date [dd/mm/yyyy]: %d:%m:%Y\n")

        return output

    def convert_vel(self):
        data = self._get_clean_sorted_data()
        num_samples = data.shape[1]

        output = "FTP NEW 2\n"

        for count in range(num_samples):
            if data[Dicts.idx['depth'], count] < 0.0:
                continue
            output += "{0:0.1f} {1:0.1f}\n".format(float(data[Dicts.idx['depth'], count]),
                                                   float(data[Dicts.idx['speed'], count]))

        return output

    def convert_ixblue(self):
        data = self._get_clean_sorted_data()
        num_samples = data.shape[1]

        output = ""
        for count in range(num_samples):
            if data[Dicts.idx['depth'], count] < 0.0:
                continue
            output += "{0:0.2f} {1:0.2f}\n".format(float(data[Dicts.idx['depth'], count]),
                                                   float(data[Dicts.idx['speed'], count]))

        return output

    def convert_csv(self):
        data = self._get_clean_sorted_data()
        num_samples = data.shape[1]

        if self.date_time:
            output = self.date_time.strftime("Date, %Y-%m-%d\n")
            output += self.date_time.strftime("Time, %H:%M:%S\n")
        else:
            output = "Date, unknown\n"
            output += "Time, unknown\n"

        if self.latitude and self.longitude:
            output += "Latitude, {0:0.7f}\n".format(float(self.latitude))
            output += "Longitude, {0:0.7f}\n".format(float(self.longitude))
        else:
            output += "Latitude, unknown\n"
            output += "Longitude, unknown\n"
        output += "depth (m), sound speed (m/s)\n"

        for count in range(num_samples):
            if data[Dicts.idx['depth'], count] < 0.0:
                continue
            output += "{0:0.2f},{1:0.2f}\n".format(float(data[Dicts.idx['depth'], count]),
                                                   float(data[Dicts.idx['speed'], count]))

        return output

    def convert_hips(self):
        data = self._get_clean_sorted_data()
        num_samples = data.shape[1]

        output = "[SVP_VERSION_2]\n"
        output += "file.svp\n"
        date_string = self.date_time.strftime("%Y-%j %H:%M:%S")

        if not self.latitude or not self.longitude:
            latitude = 0.0
            longitude = 0.0
        else:
            latitude = self.latitude
            longitude = self.longitude

        while longitude > 180.0:
            longitude -= 360.0

        lat_min = int(60 * math.fabs(latitude - int(latitude)))
        lat_sec = int(60 * int(100 * (60 * math.fabs(latitude - int(latitude)) - lat_min)))

        lon_min = int(60 * math.fabs(longitude - int(longitude)))
        lon_sec = int(60 * int(100 * (60 * math.fabs(longitude - int(longitude)) - lon_min)))

        position_string = "{0:02d}:{1:02d}:{2:02d} {3:02d}:{4:02d}:{5:02d}".format(int(latitude), lat_min, lat_sec,
                                                                                   int(longitude), lon_min, lon_sec)
        output += "Section " + date_string + " " + position_string + "\n"

        for count in range(num_samples):
            if data[Dicts.idx['depth'], count] < 0.0:
                continue
            output += "{0:0.7f} {1:0.7f}\n".format(float(data[Dicts.idx['depth'], count]),
                                                   float(data[Dicts.idx['speed'], count]))

        return output

    def convert(self, fmt):
        if fmt == "ASVP":
            return self.convert_km(Dicts.kng_formats["ASVP"])
        elif fmt == "UNB":
            return self.convert_unb()
        elif fmt == "PRO":
            return self.convert_pro()
        elif fmt == "VEL":
            return self.convert_vel()
        elif fmt == "HIPS":
            return self.convert_hips()
        elif fmt == "CSV":
            return self.convert_csv()
        elif fmt == "ELAC":
            return self.convert_elac()
        elif fmt == "IXBLUE":
            return self.convert_ixblue()
        else:
            return None

    def send_km(self, recipient_ip, recipient_port, fmt):

        self.tx_data = self.convert_km(fmt)

        sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            sock_out.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2 ** 16)
            sock_out.sendto(self.tx_data, (recipient_ip, recipient_port))

        except socket.error:
            sock_out.close()
            return False

        sock_out.close()
        return True

    def send_hypack(self, recipient_ip, recipient_port):
        """send to hypack, but before create a local self-clone"""

        self.tx_data = self.convert_calc()

        sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Now send the packet
            sock_out.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2 ** 16)
            sock_out.sendto(self.tx_data, (recipient_ip, recipient_port))

        except socket.error:
            sock_out.close()
            self.tx_data = None
            return False

        sock_out.close()
        return True

    # ### DEBUGGING ###

    def __str__(self):

        output = '- Date Time: %s\n' % self.date_time
        output += '- Position: %s, %s\n' % (self.longitude, self.latitude)
        output += '- Survey Name: %s\n' % self.survey_name
        output += '- Original Path: %s\n' % self.original_path
        output += '- Sensor Type: %s\n' % self.sensor_type
        output += '- Source String: %s\n' % self.source_info
        output += '- Driver: %s\n' % self.driver
        output += '- Samples: (%d, %d)\n' % self.data.shape
        if self.raw_data is not None:
            output += '- Raw data: (%d, %d)\n' % self.raw_data.shape
        if self.sis_data is not None:
            output += '- Sis data: (%d, %d)\n' % self.sis_data.shape

        if self.data.shape[1] < 10:
            for count in range(self.data.shape[1]):
                output += '%.2f %.2f %.2f %.2f %d %d\n' \
                          % (self.data[Dicts.idx['depth'], count], self.data[Dicts.idx['speed'], count],
                             self.data[Dicts.idx['temperature'], count], self.data[Dicts.idx['salinity'], count],
                             self.data[Dicts.idx['source'], count], self.data[Dicts.idx['flag'], count])
        else:
            # first 5 values
            for count in range(5):
                output += '%.2f %.2f %.2f %.2f %d %d\n' \
                          % (self.data[Dicts.idx['depth'], count],
                             self.data[Dicts.idx['speed'], count],
                             self.data[Dicts.idx['temperature'], count],
                             self.data[Dicts.idx['salinity'], count],
                             self.data[Dicts.idx['source'], count],
                             self.data[Dicts.idx['flag'], count])

            output += '.... .... .... .... ....\n'
            output += '%.2f %.2f %.2f %.2f %d %d\n' \
                      % (self.data[Dicts.idx['depth'], -1],
                         self.data[Dicts.idx['speed'], -1],
                         self.data[Dicts.idx['temperature'], -1],
                         self.data[Dicts.idx['salinity'], -1],
                         self.data[Dicts.idx['source'], -1],
                         self.data[Dicts.idx['flag'], -1])

        return output

    # FIXME: UNUSED CODE
    # def build_lookup_table(self, draft, max_depth):
    #     print("Going to build LUT")
    #
    #     sv_orig_data = self.data.copy()
    #     sv_orig_num_samples = self.num_samples
    #
    #     print("Using draft", draft)
    #
    #     # The sound speed profile gets resampled to "depth_interval"
    #     # prior to ray tracing.
    #     depth_interval = 1.0
    #     angular_interval = 0.1
    #
    #     # This is roughly equivalent to 0.375 m spacing along the ray
    #     twtt_interval = 0.0005
    #
    #     goodpts = (self.data[Dicts.idx['flag'], :] == 0)
    #
    #     min_profile_depth = min(self.data[Dicts.idx['depth'], goodpts])
    #     print("Got min profile depth", min_profile_depth)
    #     if min_profile_depth > draft or min_profile_depth > depth_interval:
    #         print("Going to insert sample at beginning since draft < shallowest measurement")
    #         idx = (self.data[Dicts.idx['depth'], :] == min_profile_depth) & (self.data[Dicts.idx['flag'], :] == 0)
    #         first_speed = np.mean(self.data[Dicts.idx['speed'], idx])
    #
    #         print("Found min sample at index", idx)
    #         print("Got first speed", first_speed)
    #
    #         self.insert_sample(0, first_speed, 0.0, 0.0, 0)
    #
    #     # Make sure the profile is deep enough.
    #     goodpts = (self.data[Dicts.idx['flag'], :] == 0)
    #     max_profile_depth = max(self.data[Dicts.idx['depth'], goodpts])
    #     print("Got max profile depth", max_profile_depth)
    #
    #     if max_profile_depth < max_depth:
    #         print("Going to insert sample at end since max cast depth < max desired depth")
    #         idx = (self.data[Dicts.idx['depth'], :] == max_profile_depth) & (self.data[Dicts.idx['flag'], :] == 0)
    #         last_speed = np.mean(self.data[Dicts.idx['speed'], idx])
    #
    #         print("Found max sample at index", idx)
    #         print("Got last speed", last_speed)
    #
    #         self.insert_sample(max_depth, last_speed, 0.0, 0.0, 0)
    #
    #     self.resample(depth_interval)
    #
    #     angles = np.arange(25, 90, angular_interval)
    #
    #     ray_distances = {}
    #     ray_depths = {}
    #     ray_twtts = {}
    #     max_twtt = 0
    #     max_distance = 0
    #     for angle in angles:
    #         if self.verbose and False:
    #             print("Doing angle", angle)
    #         [distance, depth, twtt] = self.calc_raypath(draft, angle, 0.0)
    #         ray_distances[angle] = distance
    #         ray_depths[angle] = depth
    #         ray_twtts[angle] = twtt
    #         max_twtt = max(max_twtt, max(twtt[:]))
    #         max_distance = max(max_distance, max(distance[:]))
    #
    #     print("Got max twtt/distance", max_twtt, max_distance)
    #
    #     num_twtt_bins = int(max_twtt / twtt_interval) + 1
    #     num_angle_bins = len(angles)
    #     memory_required = num_twtt_bins * num_angle_bins * 4 / (1024 * 1024)
    #
    #     self.forward_depth_LUT = np.zeros((num_angle_bins, num_twtt_bins))
    #     self.forward_distance_LUT = np.zeros((num_angle_bins, num_twtt_bins))
    #
    #     print("We're going to need", num_twtt_bins, "twtt bins and", num_angle_bins, "angle bins...",
    #           memory_required, "MB")
    #
    #     twtts = np.arange(0, num_twtt_bins * twtt_interval, twtt_interval)
    #     count = 0
    #     for angle in angles:
    #         depth_interp = np.interp(twtts, ray_twtts[angle], ray_depths[angle])
    #         distance_interp = np.interp(twtts, ray_twtts[angle], ray_distances[angle])
    #
    #         # np.interp will hold use the last first/last values of the
    #         # interpolant when requested to provide values beyond the range
    #         # of the interpolant's independent variable.  Need to remove these
    #         # values and replace with np.nan
    #         excessive_twtts = (twtts[:] > max(ray_twtts[angle]))
    #         depth_interp[excessive_twtts] = np.nan
    #         distance_interp[excessive_twtts] = np.nan
    #
    #         self.forward_depth_LUT[count][:] = depth_interp[:]
    #         self.forward_distance_LUT[count][:] = distance_interp[:]
    #
    #         count += 1
    #
    #     # clim sets the image limits
    #     fig = pl.figure()
    #     pl.imshow(self.forward_depth_LUT, clim=(0, 550))
    #     pl.colorbar()
    #
    #     fig = pl.figure()
    #     pl.imshow(self.forward_distance_LUT, clim=(0, 1000))
    #     pl.colorbar()
    #
    #     pl.show()
    #
    #     self.data = sv_orig_data
    #     # self.num_samples = sv_orig_num_samples
    #
    #    def calc_raypath(self, draft, angle, surface_sound_speed):
    #     good_pts = (self.data[Dicts.idx['flag'], :] == 0)
    #     sv1 = np.interp(draft, self.data[Dicts.idx['depth'], good_pts], self.data[Dicts.idx['speed'], good_pts])
    #
    #     if self.verbose:
    #         print("Got start sv: %s", sv1)
    #
    #     # we're now in radians
    #     angle = angle * math.pi / 180.0
    #
    #     if surface_sound_speed != 0.0:
    #         # adjust angle for surface sound speed measurement, if non-zero
    #         if self.verbose:
    #             print("Adjusting angle: %s" % (angle * 180.0 / math.pi))
    #         angle = math.acos(sv1 / surface_sound_speed * math.cos(angle))
    #         if self.verbose:
    #             print("Adjusted angle: %s" % (angle * 180.0 / math.pi))
    #
    #     # find all non-flagged samples greater than the draft
    #     good_pts = (self.data[Dicts.idx['depth'], :] > draft) & (self.data[Dicts.idx['flag'], :] == 0)
    #
    #     num_values = self.data[Dicts.idx['depth'], good_pts].size + 1
    #     depth = np.zeros(num_values)
    #     speed = np.zeros(num_values)
    #     depth[0] = draft
    #     depth[1:num_values] = self.data[Dicts.idx['depth'], good_pts]
    #     speed[0] = sv1
    #     speed[1:num_values] = self.data[Dicts.idx['speed'], good_pts]
    #
    #     total_depth = np.zeros(num_values)
    #     total_distance = np.zeros(num_values)
    #     total_time = np.zeros(num_values)
    #
    #     total_depth[0] = draft
    #     total_distance[0] = 0
    #     total_time[0] = 0
    #     num_valid = 0
    #     for layer in range(num_values - 1):
    #
    #         # Skip samples layers with the same depth
    #         if depth[layer + 1] == depth[layer]:
    #             continue
    #
    #         if self.verbose:
    #             print(layer, "of", num_values, ": visiting this layer (", depth[layer + 1], speed[layer + 1],
    #                   ") ... accumulated ", total_depth[num_valid], total_distance[num_valid], total_time[num_valid])
    #
    #         last_angle = angle
    #
    #         try:
    #             angle = math.acos(speed[layer + 1] / speed[layer] * math.cos(angle))
    #         except ValueError:
    #             print("Ray went horizontal!!")
    #             break
    #
    #         if speed[layer + 1] != speed[layer]:
    #             gradient = (speed[layer + 1] - speed[layer]) / (depth[layer + 1] - depth[layer])
    #
    #             if self.verbose:
    #                 print(layer, "of", num_values, ": got dC/dD", speed[layer + 1] - speed[layer],
    #                       depth[layer + 1] - depth[layer])
    #             delta_depth = depth[layer + 1] - depth[layer]
    #             delta_distance = speed[layer] / (gradient * math.cos(last_angle)) * (math.sin(last_angle) -
    #                                                                                  math.sin(angle))
    #             delta_time = 1.0 / gradient * math.log(
    #                 math.tan(last_angle / 2.0 + math.pi / 4.0) / math.tan(angle / 2.0 + math.pi / 4.0))
    #
    #             if self.verbose:
    #                 print(layer, "of", num_values, ": got gradient of", gradient)
    #                 print(layer, "of", num_values, ": refracted to", angle * 180.0 / math.pi,
    #                       ", travelled", delta_distance, "m horiz over", delta_time, "sec")
    #         else:
    #             delta_depth = depth[layer + 1] - depth[layer]
    #             delta_distance = delta_depth / math.tan(last_angle)
    #             delta_time = (delta_depth / math.sin(last_angle)) / speed[layer]
    #
    #         num_valid += 1
    #
    #         total_depth[num_valid] = total_depth[num_valid - 1] + delta_depth
    #         total_distance[num_valid] = total_distance[num_valid - 1] + delta_distance
    #
    #         # We accumulate TWTT so multiply delta time by 2.0
    #         total_time[num_valid] = total_time[num_valid - 1] + 2.0 * delta_time
    #
    #     # This is now a count and no longer an index
    #     num_valid += 1
    #
    #     # Resize these to accommodate actual size which may be smaller than
    #     # expected due to skipped samples
    #     total_depth.resize(num_valid)
    #     total_distance.resize(num_valid)
    #     total_time.resize(num_valid)
    #
    #     data = np.vstack([total_distance, total_depth, total_time])
    #
    #     return data
    #
    # def raytrace(self, draft, angle, surface_sound_speed, twtt):
    #
    #     if twtt == 0.0:
    #         return 0, draft
    #
    #     previous_sv = None
    #     gradient = None
    #     last_sv = None
    #
    #     good_pts = (self.data[Dicts.idx['flag'], :] == 0)
    #     sv1 = np.interp(draft, self.data[Dicts.idx['depth'], good_pts], self.data[Dicts.idx['speed'], good_pts])
    #
    #     # we're now in radians
    #     angle = angle * math.pi / 180.0
    #
    #     if surface_sound_speed != 0.0:
    #         # adjust angle for surface sound speed measurement, if non-zero
    #         # print "Adjusting angle!!", angle*180.0/math.pi
    #         angle = math.acos(sv1 / surface_sound_speed * math.cos(angle))
    #         #snells_constant = math.cos(angle) / surface_sound_speed
    #         #print "Adjusted angle!!", angle*180.0/math.pi
    #     else:
    #         pass
    #         #snells_constant = math.cos(angle) / sv1
    #
    #     # find all non-flagged samples greater than the draft
    #     good_pts = (self.data[Dicts.idx['depth'], :] > draft) & (self.data[Dicts.idx['flag'], :] == 0)
    #
    #     num_values = self.data[Dicts.idx['depth'], good_pts].size + 1
    #     depth = np.zeros(num_values)
    #     speed = np.zeros(num_values)
    #     depth[0] = draft
    #     depth[1:num_values] = self.data[Dicts.idx['depth'], good_pts]
    #     speed[0] = sv1
    #     speed[1:num_values] = self.data[Dicts.idx['speed'], good_pts]
    #
    #     total_depth = np.zeros(num_values)
    #     total_distance = np.zeros(num_values)
    #     total_time = np.zeros(num_values)
    #
    #     total_depth[0] = draft
    #     total_distance[0] = 0
    #     total_time[0] = 0
    #     num_valid = 0
    #     beyond_end = True
    #     for layer in range(num_values - 1):
    #
    #         # Skip samples layers with the same depth
    #         if depth[layer + 1] == depth[layer]:
    #             continue
    #
    #         # print layer, "of", num_values,": visiting this layer (", depth[layer+1], speed[layer+1], ") ...
    #         # accumulated ", total_depth[num_valid], total_distance[num_valid], total_time[num_valid]
    #
    #         num_valid += 1
    #
    #         last_angle = angle
    #         angle = math.acos(speed[layer + 1] / speed[layer] * math.cos(angle))
    #
    #         if speed[layer + 1] != speed[layer]:
    #             gradient = (speed[layer + 1] - speed[layer]) / (depth[layer + 1] - depth[layer])
    #             #print layer, "of", num_values,": got dC/dD", speed[layer+1] - speed[layer],
    #             # depth[layer+1] - depth[layer]
    #             delta_depth = speed[layer] / (gradient * math.cos(last_angle)) * (math.cos(angle) -
    #                                                                               math.cos(last_angle))
    #             delta_distance = speed[layer] / (gradient * math.cos(last_angle)) * (math.sin(last_angle) -
    #                                                                                  math.sin(angle))
    #             delta_time = 1.0 / gradient * math.log(math.tan(last_angle / 2.0 + math.pi / 4.0) /
    #                                                    math.tan(angle / 2.0 + math.pi / 4.0))
    #             #print layer, "of", num_values,": got gradient of", gradient
    #             #print layer, "of", num_values,": refracted to", angle*180.0/math.pi,", travelled", delta_distance,
    #             # "m horiz over",delta_time,"sec"
    #         else:
    #             gradient = None
    #             delta_depth = depth[layer + 1] - depth[layer]
    #             delta_distance = delta_depth / math.tan(last_angle)
    #             delta_time = (delta_depth / math.sin(last_angle)) / speed[layer]
    #
    #         total_depth[num_valid] = total_depth[num_valid - 1] + delta_depth
    #         total_distance[num_valid] = total_distance[num_valid - 1] + delta_distance
    #
    #         # We accummulate TWTT
    #         total_time[num_valid] = total_time[num_valid - 1] + 2.0 * delta_time
    #         last_sv = speed[layer + 1]
    #         previous_sv = speed[layer]
    #
    #         #print "Seeking TWTT of", twtt, ", accumulated", total_time[num_valid]," so far..."
    #
    #         if total_time[num_valid] == twtt:
    #             #print "WOW...exactly equal"
    #             return total_distance[num_valid], total_depth[num_valid]
    #
    #         if total_time[num_valid] > twtt:
    #             #print "Went too far in the layer!"
    #             beyond_end = False
    #             break
    #
    #     if beyond_end:
    #         # print "Went beyond end of profile!"
    #         twtt_remaining = twtt - total_time[num_valid]
    #         #print "Got last TWTTs", total_time[num_valid], twtt
    #         #print "Last SV is", last_sv, "and last angle is", angle * 180.0/math.pi ,
    #         # "and remaining TWTT is", twtt_remaining
    #         delta_depth = twtt_remaining * last_sv * math.sin(angle) / 2.0
    #         delta_distance = twtt_remaining * last_sv * math.cos(angle) / 2.0
    #     else:
    #         # print "Stopped within profile", total_time[num_valid-1], twtt, total_time[num_valid],
    #         # "gradient is", gradient
    #         # delta_depth = 0.0
    #         # delta_distance = 0.0
    #         if not gradient:
    #             #print "Got case of no gradient"
    #             #print "Got last TWTTs", total_time[num_valid-1], twtt, total_time[num_valid]
    #             twtt_excess = total_time[num_valid] - twtt
    #             #print "Got excess TWTT of", twtt_excess
    #             delta_depth = -1.0 * twtt_excess * last_sv * math.sin(angle) / 2.0
    #             delta_distance = -1.0 * twtt_excess * last_sv * math.cos(angle) / 2.0
    #         else:
    #             #print "Got case of gradient", gradient
    #             #print "Got last TWTTs", total_time[num_valid-1], twtt, total_time[num_valid]
    #
    #             # interpolated_time = total_time[num_valid] - total_time[num_valid - 1]
    #             # interpolated_distance = total_distance[num_valid] - total_distance[num_valid - 1]
    #             # interpolated_depth = total_depth[num_valid] - total_depth[num_valid - 1]
    #
    #             accumulated_time = total_time[num_valid - 1]
    #             accumulated_distance = total_distance[num_valid - 1]
    #             accumulated_depth = total_depth[num_valid - 1]
    #
    #             #print "Jumping to last good OWTT, depth and radial:", accumulated_time/2.0, accumulated_distance,
    #             # accumulated_depth
    #
    #             layer_thickness = total_depth[num_valid] - total_depth[num_valid - 1]
    #
    #             prev_depth = total_depth[num_valid - 1]
    #             next_depth = total_depth[num_valid]
    #             prev_velocity = previous_sv
    #             next_velocity = last_sv
    #
    #             #print "Got interp'd time/distance/depth", interpolated_time, interpolated_distance,
    #                    interpolated_depth
    #             #print "Got accumulated time/distance/depth", accumulated_time, accumulated_distance,
    #                     accumulated_depth
    #             #print "Got layer thickness", layer_thickness
    #             #print "Snell's constant", snells_constant
    #             #print "Starting with last angle", last_angle * 180.0/math.pi
    #
    #             iteration = 0
    #             # 0.0005 is the tolerable depth difference we're willing to accept
    #             while layer_thickness > 0.0005:
    #                 middle_depth = (next_depth - prev_depth) / 2.0 + prev_depth
    #                 middle_velocity = (next_velocity - prev_velocity) / 2.0 + prev_velocity
    #
    #                 #print iteration, ": Splitting layers...", middle_depth, middle_velocity
    #
    #                 d1 = prev_depth
    #                 d2 = middle_depth
    #                 v1 = prev_velocity
    #                 v2 = middle_velocity
    #
    #                 angle = math.acos(v2 / v1 * math.cos(last_angle))
    #                 #print "new angle is", angle * 180.0/math.pi
    #
    #                 layer_thickness = abs(d2 - d1)
    #
    #                 #print "Layer thickness is", layer_thickness
    #                 #print "d1/v1, d2/v2", d1, v1, d2, v2
    #
    #                 interpolated_distance = v1 / (gradient *
    #                                               math.cos(last_angle)) * (math.sin(last_angle) - math.sin(angle))
    #                 interpolated_time = 1.0 / gradient * math.log(
    #                     math.tan(last_angle / 2.0 + math.pi / 4.0) / math.tan(angle / 2.0 + math.pi / 4.0))
    #
    #                 #print "Got interpolated radial and OWTT", interpolated_distance, interpolated_time
    #
    #                 if accumulated_time + 2.0 * interpolated_time > twtt:
    #                     #print "Split is still too far!!!"
    #                     next_depth = d2
    #                     next_velocity = v2
    #                 else:
    #                     #print "Split wasn't far enough!!!"
    #                     prev_depth = d2
    #                     prev_velocity = v2
    #                     last_angle = angle
    #                     accumulated_time += 2.0 * interpolated_time
    #                     accumulated_distance += interpolated_distance
    #                     accumulated_depth += layer_thickness
    #
    #                 #print "Okay, accumulated dist/depth/time is now", accumulated_distance, accumulated_depth,
    #                 # accumulated_time, "\n"
    #                 iteration += 1
    #
    #                 #print "Checking between", prev_depth, "and", next_depth
    #
    #             return accumulated_distance, accumulated_depth
    #
    #     # Return the end of the ray for now
    #     final_distance = total_distance[num_valid] + delta_distance
    #     final_depth = total_depth[num_valid] + delta_depth
    #
    #     return final_distance, final_depth
    #
    # def resample(self, interval):
    #
    #     good_pts = (self.data[Dicts.idx['flag'], :] == 0)
    #     max_depth = self.data[Dicts.idx['depth'], -1]
    #     num_samples = int(max_depth / interval)
    #     depths = np.linspace(0, num_samples * interval, num_samples + 1)
    #     speeds = np.interp(depths, self.data[Dicts.idx['depth'], good_pts], self.data[Dicts.idx['speed'], good_pts])
    #     temperatures = np.interp(depths, self.data[Dicts.idx['depth'], good_pts],
    #                              self.data[Dicts.idx['temperature'], good_pts])
    #     salinities = np.interp(depths, self.data[Dicts.idx['depth'], good_pts], self.data[Dicts.idx['salinity'],
    #                                                                                       good_pts])
    #
    #     self.set_samples(depth=depths, speed=speeds,
    #                      temperature=temperatures, salinity=salinities,
    #                      source=np.zeros(num_samples + 1), flag=np.zeros(num_samples + 1))
    #
    # def get_sample_intervals(self):
    #     min_interval = 20000
    #     max_interval = 0
    #     for level in range(self.data.shape[1] - 1):
    #         interval = abs(self.data[Dicts.idx['depth'], level + 1] - self.data[Dicts.idx['depth'], level])
    #         min_interval = min(min_interval, interval)
    #         max_interval = max(max_interval, interval)
    #
    #     return min_interval, max_interval
    #
    # @classmethod
    # def cross_product(cls, a, b):
    #     c = np.zeros(3)
    #     c[0] = a[1] * b[2] - a[2] * b[1]
    #     c[1] = -1.0 * (a[0] * b[2] - a[2] * b[0])
    #     c[2] = a[0] * b[1] - a[1] * b[0]
    #     return c
    #
    # def interpolate_spatial(self, sv_node1, sv_node2, sv_node3):
    #
    #     sv_node1_orig_data = sv_node1.data.copy()
    #     sv_node1_orig_num_samples = sv_node1.num_samples
    #     sv_node2_orig_data = sv_node2.data.copy()
    #     sv_node2_orig_num_samples = sv_node2.num_samples
    #     sv_node3_orig_data = sv_node3.data.copy()
    #     sv_node3_orig_num_samples = sv_node3.num_samples
    #
    #     [min1, _] = sv_node1.get_sample_intervals()
    #     [min2, _] = sv_node2.get_sample_intervals()
    #     [min3, _] = sv_node3.get_sample_intervals()
    #
    #     interval = min(min1, min2, min3)
    #
    #     sv_node1.resample(interval)
    #     sv_node2.resample(interval)
    #     sv_node3.resample(interval)
    #
    #     max_depth = min(sv_node1.data[sv_node1.idx['depth'], -1], sv_node2.data[sv_node2.idx['depth'], -1],
    #                     sv_node3.data[sv_node3.idx['depth'], -1])
    #
    #     num_samples = int(max_depth / interval)
    #
    #     depths = np.zeros(num_samples + 1)
    #     speeds = np.zeros(num_samples + 1)
    #     temperatures = np.zeros(num_samples + 1)
    #     salinities = np.zeros(num_samples + 1)
    #     sources = np.zeros(num_samples + 1)
    #     flags = np.zeros(num_samples + 1)
    #
    #     node1 = np.zeros(3)
    #     node2 = np.zeros(3)
    #     node3 = np.zeros(3)
    #
    #     node1[0] = sv_node1.longitude
    #     node1[1] = sv_node1.latitude
    #     node2[0] = sv_node2.longitude
    #     node2[1] = sv_node2.latitude
    #     node3[0] = sv_node3.longitude
    #     node3[1] = sv_node3.latitude
    #
    #     for level in range(len(depths)):
    #         depths[level] = sv_node1.data[sv_node1.idx['depth'], level]
    #
    #         node1[2] = sv_node1.data[sv_node1.idx['speed'], level]
    #         node2[2] = sv_node2.data[sv_node2.idx['speed'], level]
    #         node3[2] = sv_node3.data[sv_node3.idx['speed'], level]
    #
    #         normal_vector = self.cross_product(node3 - node1, node2 - node1)
    #
    #         # Equation for a plane with normal vector (a,b,c) and point (x0,y0,z0)
    #         # a * (x - x0) + b * (y - y0) + c * (z - z0) = 0
    #         # a * (x - x0) + b * (y - y0) = -c * (z - z0)
    #         # -1.0/c * (a * (x - x0) + b * (y - y0)) = (z - z0)
    #         # -1.0/c * (a * (x - x0) + b * (y - y0)) + z0 = z
    #         speeds[level] = -1.0 / normal_vector[2] * (normal_vector[0] *
    #                                                    (self.longitude - node1[0]) +
    #                                                    normal_vector[1] * (self.latitude - node1[1])) + node1[2]
    #
    #         node1[2] = sv_node1.data[sv_node1.idx['temperature'], level]
    #         node2[2] = sv_node2.data[sv_node2.idx['temperature'], level]
    #         node3[2] = sv_node3.data[sv_node3.idx['temperature'], level]
    #
    #         normal_vector = self.cross_product(node3 - node1, node2 - node1)
    #
    #         # Same as was done for speeds
    #         temperatures[level] = -1.0 / normal_vector[2] * (normal_vector[0] *
    #                                                          (self.longitude - node1[0]) + normal_vector[1] *
    #                                                          (self.latitude - node1[1])) + node1[2]
    #
    #         node1[2] = sv_node1.data[sv_node1.idx['salinity'], level]
    #         node2[2] = sv_node2.data[sv_node2.idx['salinity'], level]
    #         node3[2] = sv_node3.data[sv_node3.idx['salinity'], level]
    #
    #         normal_vector = self.cross_product(node3 - node1, node2 - node1)
    #
    #         # Same as was done for speeds and temperatures
    #         salinities[level] = -1.0 / normal_vector[2] * (normal_vector[0] * (self.longitude - node1[0]) +
    #                                                        normal_vector[1] * (self.latitude - node1[1])) + node1[2]
    #
    #     self.set_samples(depth=depths, speed=speeds,
    #                      temperature=temperatures, salinity=salinities,
    #                      source=sources, flag=flags)
    #
    #     # Put back the original data so that the input profiles remain unmodified
    #     sv_node1.data = sv_node1_orig_data
    #     sv_node1.num_samples = sv_node1_orig_num_samples
    #     sv_node2.data = sv_node2_orig_data
    #     sv_node2.num_samples = sv_node2_orig_num_samples
    #     sv_node3.data = sv_node3_orig_data
    #     sv_node3.num_samples = sv_node3_orig_num_samples
    #
    # def interpolate_temporal(self, sv_before, sv_after):
    #     sv_before_orig_data = sv_before.data.copy()
    #     sv_before_orig_num_samples = sv_before.num_samples
    #     sv_after_orig_data = sv_after.data.copy()
    #     sv_after_orig_num_samples = sv_after.num_samples
    #
    #     [min1, _] = sv_before.get_sample_intervals()
    #     [min2, _] = sv_after.get_sample_intervals()
    #
    #     interval = min(min1, min2)
    #
    #     sv_before.resample(interval)
    #     sv_after.resample(interval)
    #
    #     max_depth = min(sv_before.data[sv_before.idx['depth'], -1], sv_after.data[sv_after.idx['depth'], -1])
    #
    #     num_samples = int(max_depth / interval)
    #
    #     depths = np.zeros(num_samples + 1)
    #     speeds = np.zeros(num_samples + 1)
    #     temperatures = np.zeros(num_samples + 1)
    #     salinities = np.zeros(num_samples + 1)
    #     sources = np.zeros(num_samples + 1)
    #     flags = np.zeros(num_samples + 1)
    #
    #     if sv_before.date_time < sv_after.date_time:
    #         t = self.date_time - sv_before.date_time
    #         dt = sv_after.date_time - sv_before.date_time
    #         # got_backwards = False
    #     else:
    #         t = self.date_time - sv_after.date_time
    #         dt = sv_before.date_time - sv_after.date_time
    #         # got_backwards = True
    #
    #     seconds_requested = (t.microseconds + (t.seconds + t.days * 24 * 3600) * 10 ** 6) / 10 ** 6
    #     delta_time = (dt.microseconds + (dt.seconds + dt.days * 24 * 3600) * 10 ** 6) / 10 ** 6
    #
    #     for level in range(len(depths)):
    #         depths[level] = sv_before.data[sv_before.idx['depth'], level]
    #
    #         speed1 = sv_before.data[sv_before.idx['speed'], level]
    #         speed2 = sv_after.data[sv_after.idx['speed'], level]
    #         speeds[level] = speed1 + (speed2 - speed1) / delta_time * seconds_requested
    #
    #         temp1 = sv_before.data[sv_before.idx['temperature'], level]
    #         temp2 = sv_after.data[sv_after.idx['temperature'], level]
    #         temperatures[level] = temp1 + (temp2 - temp1) / delta_time * seconds_requested
    #
    #         sal1 = sv_before.data[sv_before.idx['salinity'], level]
    #         sal2 = sv_after.data[sv_after.idx['salinity'], level]
    #         salinities[level] = sal1 + (sal2 - sal1) / delta_time * seconds_requested
    #
    #     self.set_samples(depth=depths, speed=speeds, temperature=temperatures, salinity=salinities,
    #                      source=sources, flag=flags)
    #
    #     # Put back the original data so that the input profiles remain unmodified
    #     sv_before.data = sv_before_orig_data
    #     sv_before.num_samples = sv_before_orig_num_samples
    #     sv_after.data = sv_after_orig_data
    #     sv_after.num_samples = sv_after_orig_num_samples
    #
    # def thin_by_points(self, max_points):
    #
    #     if self.data.shape[1] < max_points:
    #         return
    #
    #     # purge flagged points first
    #     self.data = SspAux.purge_flagged_samples(self.data)
    #
    #     good_pts = (self.data[Dicts.idx['flag'], :] == 0)
    #     num_kept = np.count_nonzero(good_pts)
    #
    #     # start with a tolerance of zero
    #     tolerance = 0.0
    #
    #     while num_kept > max_points:
    #         # slowly raise the tolerance
    #         tolerance += 0.001
    #
    #         # Unflag all data
    #         self.data[Dicts.idx['flag'], :] = 0
    #
    #         # Now _thin_ssp it
    #         self._douglas_peucker_1d(0, self.data.shape[1] - 1, tolerance)
    #
    #         # find the points that have survived the thinning
    #         good_pts = (self.data[Dicts.idx['flag'], :] == 1)
    #         num_kept = np.count_nonzero(good_pts)
    #
    #     # set flag to '1' for all points
    #     self.data[Dicts.idx['flag'], :] = 1
    #
    #     # now unflag the points we want to keep, those that survived thinning
    #     self.data[Dicts.idx['flag'], good_pts] = 0
    #
    #     # and purge those that were tossed out
    #     self.data = SspAux.purge_flagged_samples(self.data)
