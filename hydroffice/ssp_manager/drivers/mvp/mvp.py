from __future__ import absolute_import, division, print_function, unicode_literals

import datetime as dt
import struct
import numpy as np
import logging

log = logging.getLogger(__name__)

from ..base_format import BaseFormat, FormatError
from ...ssp_dicts import Dicts
from ... import __version__


class Mvp(BaseFormat):

    protocols = {
        "NAVO_ISS60": 0,
        "UNDEFINED": 1
    }

    formats = {
        "ASVP": 0,
        "CALC": 1,
        "S12": 2
    }

    def __init__(self, header, data_blocks, footer, protocol, fmt):
        super(Mvp, self).__init__(data_blocks)
        self.name = "MVP"
        self.driver = self.name + (".%s" % __version__)

        self.header = header
        self.footer = footer
        self.protocol = protocol
        self.format = fmt

        log.info("reading ...")
        log.info("data blocks: %s" % len(self.file_content))

        self.total_data = str()
        self._unify_packets()

        try:
            # log.info("got data:\n%s" % self.total_data)
            self._read_header(None)
            self._read_body(None)
        except FormatError as e:
            log.error("error in data parsing, did you select the correct data format?")
            raise e

    def _read_header(self, lines):

        log.info("reading > header")

        if lines:
            raise FormatError("passed lines, expected None")

        if self.format == self.formats["ASVP"]:
            log.info("parsing header [ASVP]")
            self._parse_asvp_header()

        elif self.format == self.formats["CALC"]:
            log.info("parsing header [CALC]")
            self._parse_calc_header()

        elif self.format == self.formats["S12"]:
            log.info("parsing header [S12]")
            self._parse_s12_header()

        self.probe_type = Dicts.probe_types["MVP"]
        self.sensor_type = Dicts.sensor_types["MVP"]

    def _read_body(self, lines):
        log.info("reading > body")

        if lines:
            raise FormatError("passed lines, expected None")

        # this assume that the user configured the correct format.
        if self.format == self.formats["ASVP"]:
            log.info("parsing body [ASVP]")
            count = self._parse_asvp_body()

        elif self.format == self.formats["CALC"]:
            log.info("parsing body [CALC]")
            count = self._parse_calc_body()

        elif self.format == self.formats["S12"]:
            log.info("parsing body [S12]")
            count = self._parse_s12_body()

        else:
            raise FormatError("unknown format: %s" % self.format)

        log.info("read %s samples" % count)

        # Now resize all of them based on how many samples were actually found.
        if self.num_samples != count:
            self.depth.resize(count)
            self.speed.resize(count)
            self.temperature.resize(count)
            self.salinity.resize(count)
            self.num_samples = count

    def _unify_packets(self):
        """unify all the received blocks"""

        for block_count in range(len(self.file_content)):
            log.info("%s block has length %.1f KB"
                     % (block_count, len(self.file_content[block_count]) / 1024))

            if self.protocol == self.protocols["NAVO_ISS60"]:
                block_header = struct.unpack('4s4sIIII20000s4s4s', self.file_content[block_count])
                packet_number = block_header[2]
                total_num_packets = block_header[3]
                num_bytes = block_header[4]
                total_num_bytes = block_header[5]
                packet_data = self.file_content[block_count][24:24+num_bytes]
                self.total_data += packet_data
                log.info("packet %s/%s [%.1f KB]"
                         % (packet_number + 1, total_num_packets, total_num_bytes / 1024))
            elif self.protocol == self.protocols["UNDEFINED"]:
                self.total_data += self.file_content[block_count]
            else:
                raise FormatError("unknown protocol %s" % self.protocol)

    def _parse_asvp_header(self):
        try:
            head_line = self.total_data.splitlines()[0]
            fields = head_line.split()
        except (ValueError, IndexError):
            raise FormatError("unable to parse header")

        try:
            timestamp = fields[4]
            year = int(timestamp[0:4])
            month = int(timestamp[4:6])
            day = int(timestamp[6:8])
            hour = int(timestamp[8:10])
            minute = int(timestamp[10:12])
            second = 0
            if (year is not None) and (hour is not None):
                self.dg_time = dt.datetime(year, month, day, hour, minute, second)
                log.info("date/time: %s" % self.dg_time)
        except (ValueError, IndexError):
            raise FormatError("unable to parse date/time")

        try:
            self.num_samples = int(fields[12])
            log.info("number of samples: %s" % self.num_samples)
        except (ValueError, IndexError):
            raise FormatError("unable to parse the number of samples")

        try:
            self.latitude = float(fields[5])
            log.info("latitude: %s" % self.latitude)
        except (ValueError, IndexError):
            raise FormatError("unable to parse the latitude")

        try:
            self.longitude = float(fields[6])
            log.info("longitude: %s" % self.longitude)
        except (ValueError, IndexError):
            raise FormatError("unable to parse the longitude")

        self.depth = np.zeros(self.num_samples)
        self.speed = np.zeros(self.num_samples)
        self.temperature = np.zeros(self.num_samples)
        self.salinity = np.zeros(self.num_samples)

        self.samples_offset = len(head_line)
        log.info("samples offset: %s" % self.samples_offset)

    def _parse_asvp_body(self):
        count = 0
        for line in self.total_data[self.samples_offset:len(self.total_data)].splitlines():
            try:
                self.depth[count], self.speed[count] = line.split()
            except ValueError:
                if not line:
                    log.info("skipping empty line (count %s)" % count)
                else:
                    log.error("skipping line: %s" % line)
                continue
            count += 1
        return count

    def _parse_calc_header(self):
        try:
            # Date [dd/mm/yyyy]:  09/04/2013
            date_field = self.total_data.splitlines()[-1].split()[-1]
            day = int(date_field.split("/")[0])
            month = int(date_field.split("/")[1])
            year = int(date_field.split("/")[2])
            log.info("date: %s %s %s" % (year, month, day))
        except (ValueError, IndexError):
            raise FormatError("unable to parse the date")

        try:
            # Time [hh:mm:ss.ss]: 13:24:09.39
            time_field = self.total_data.splitlines()[-2].split()[-1]
            hour = int(time_field.split(":")[0])
            minute = int(time_field.split(":")[1])
            second = float(time_field.split(":")[2])
            log.info("time: %s %s %s" % (hour, minute, second))
        except (ValueError, IndexError):
            raise FormatError("unable to parse the time")

        try:
            if (year is not None) and (hour is not None):
                # second truncation applied
                self.dg_time = dt.datetime(year, month, day, hour, minute, int(second))
                log.info("datetime: %s" % self.dg_time)
        except (ValueError, IndexError, TypeError) as e:
            raise FormatError("unable to convert to datetime: %s" % e)

        try:
            # LON (dddmm.mmmmmmm,E): 05557.4253510,W
            lon_field = self.total_data.splitlines()[-3].split()[-1].split(",")[0]
            lon_deg = int(lon_field[0:3])
            lon_min = float(lon_field[3:-1])
            lon_hemi = self.total_data.splitlines()[-3].split()[-1].split(",")[-1]
            self.longitude = lon_deg + lon_min/60.0
            if lon_hemi == "W" or lon_hemi == "w":
                self.longitude *= -1
            log.info("longitude: %s" % self.longitude)
        except (ValueError, IndexError, TypeError) as e:
            raise FormatError("unable to convert to longitude: %s" % e)

        try:
            # LAT ( ddmm.mmmmmmm,N):  4249.4583290,N
            lat_field = self.total_data.splitlines()[-4].split()[-1].split(",")[0]
            lat_deg = int(lat_field[0:2])
            lat_min = float(lat_field[2:-1])
            lat_hemi = self.total_data.splitlines()[-4].split()[-1].split(",")[-1]
            self.latitude = lat_deg + lat_min/60.0
            if lat_hemi == "S" or lat_hemi == "s":
                self.latitude *= -1
            log.info("latitude: %s" % self.latitude)
        except (ValueError, IndexError, TypeError) as e:
            raise FormatError("unable to convert to longitude: %s" % e)

        self.num_samples = len(self.total_data.splitlines())
        self.depth = np.zeros(self.num_samples)
        self.speed = np.zeros(self.num_samples)
        self.temperature = np.zeros(self.num_samples)
        self.salinity = np.zeros(self.num_samples)

    def _parse_calc_body(self):

        count = 0
        for line in self.total_data.splitlines()[5:-9]:
            fields = line.split()
            if len(fields) != 3:
                log.info("skipping %s row" % count)
                continue

            try:
                self.depth[count] = float(fields[0])
                self.speed[count] = float(fields[1])
                self.temperature[count] = float(fields[2])
            except (ValueError, IndexError, TypeError) as e:
                log.error("skipping %s row: %s" % (count, e))
                continue
            count += 1

        return count

    def _parse_s12_header(self):
        try:
            # $MVS12,00002,0095,132409,09,04,2013,6.75,1514.76,18.795,31.9262,
            header_fields = self.total_data.splitlines()[0].split(",")
        except (ValueError, IndexError, TypeError) as e:
            raise FormatError("unable to parse header fields: %s" % e)

        try:
            year = int(header_fields[6])
            month = int(header_fields[5])
            day = int(header_fields[4])
            hour = int(header_fields[3][0:2])
            minute = int(header_fields[3][2:4])
            second = int(header_fields[3][4:6])
            if (year is not None) and (hour is not None):
                self.dg_time = dt.datetime(year, month, day, hour, minute, second)
                log.info("date/time: %s" % self.dg_time)
        except (ValueError, IndexError, TypeError) as e:
            raise FormatError("unable to parse header fields: %s" % e)

        try:
            # 4249.46,N,05557.43,W,0.0,AML_uSVPT*15\
            footer_fields = self.total_data.splitlines()[-1].split(",")
        except (ValueError, IndexError, TypeError) as e:
            raise FormatError("unable to parse footer_fields: %s" % e)

        try:
            lat_field = footer_fields[0]
            lat_deg = int(lat_field[0:2])
            lat_min = float(lat_field[2:-1])
            lat_hemi = footer_fields[1]
            self.latitude = lat_deg + lat_min/60.0
            if lat_hemi == "S" or lat_hemi == "s":
                self.latitude *= -1
            log.info("latitude: %s" % self.latitude)
        except (ValueError, IndexError, TypeError) as e:
            raise FormatError("unable to parse latitude: %s" % e)

        try:
            lon_field = footer_fields[2]
            lon_deg = int(lon_field[0:3])
            lon_min = float(lon_field[3:-1])
            lon_hemi = footer_fields[3]
            self.longitude = lon_deg + lon_min/60.0
            if lon_hemi == "W" or lon_hemi == "w":
                self.longitude *= -1
            log.info("longitude: %s" % self.longitude)
        except (ValueError, IndexError, TypeError) as e:
            raise FormatError("unable to parse longitude: %s" % e)

        try:
            self.num_samples = len(self.total_data.splitlines())
            log.info("number of samples: %s" % self.num_samples)
        except (ValueError, IndexError, TypeError) as e:
            raise FormatError("unable to parse the number of samples: %s" % e)

        self.depth = np.zeros(self.num_samples)
        self.speed = np.zeros(self.num_samples)
        self.temperature = np.zeros(self.num_samples)
        self.salinity = np.zeros(self.num_samples)

        count = 0
        try:
            self.depth[count] = float(header_fields[-5])
            self.speed[count] = float(header_fields[-4])
            self.temperature[count] = float(header_fields[-3])
            self.salinity[count] = float(header_fields[-2])
        except (ValueError, IndexError, TypeError) as e:
            log.error("skipping first line: %s" % e)

    def _parse_s12_body(self):
        count = 1  # given the first data are on the header
        for line in self.total_data.splitlines()[1:-1]:

            try:
                fields = line.split(",")
                self.depth[count] = float(fields[-5])
                self.speed[count] = float(fields[-4])
                self.temperature[count] = float(fields[-3])
                self.salinity[count] = float(fields[-2])
            except (ValueError, IndexError, TypeError) as e:
                log.error("skipping line %s: %s" % (count, e))
                continue
            count += 1
        return count


# # TODO: ask Jonathan about this unused function
# # This is the documentation provided by Steve Smyth of Rolls Royce (ODIM Brooke Ocean)
# # as per an email communication with Shannon Byrne of SAIC, dated February 03, 2009
# # to facilitate data transfer from MVP to ISS60.
# #
# # Header (536 bytes)
# #
# #	 4 byte header (STX + msgID)
# #    4 byte pad
# #    512 byte character buffer containing file name
# #    4 byte uint for fileSize
# #    4 byte uint for data packet size (20,000 bytes)
# #    4 bytes pad
# #    4 byte footer (Checksum + ETX)
# #
# # Data block (20,032 bytes)
# #
# #    4 byte header (STX + msgID)
# #    4 byte pad
# #    4 byte uint for packetNo              (0,1,2,3,...)
# #    4 byte uint for totalPackets
# #    4 byte uint for numBytesInPacket (actual number of points in this message)
# #    4 byte uint for totalBytes             (4,294,967,295 bytes maximum file size)
# #    20000 byte data[20000];
# #    4 bytes pad
# #    4 byte footer (Checksum + ETX)
# #
# # Footer (8 bytes)
# #
# #    4 byte header (STX + msgID)
# #    4 byte footer (Checksum + ETX)
#
# udp_def_odim_stx = 0x4F44
# udp_def_odim_etx = 0x494D
# udp_msgno_odim_nftp_new_profile = 0x10
# udp_msgno_nftp_start = 0x11
# udp_msgno_odim_nftp_data_packet = 0x12
# udp_msgno_nftp_stop = 0x13
# udp_msgno_odim_nftp_abort = 0x1C
# udp_msgno_odim_nftp_send_last = 0x1D
# udp_msgno_odim_nftp_ack = 0x1E
# udo_msgno_odim_nftp_nack = 0x1F
# navo_header_size = 536
# navo_block_size = 20032
# navo_data_size = 20000
# navo_footer_size = 8
#
#
# def convert_navo(data):
#     footer = bytearray(8)
#     data_blocks = []
#
#     # Header (532 bytes)
#     #    4 byte header (STX + msgID)
#     #    4 byte pad
#     #    512 byte character buffer containing file name
#     #    4 byte uint for fileSize
#     #    4 byte uint for data packet size (20,000 bytes)
#     #    4 bytes pad
#     #    4 byte footer (Checksum + ETX)
#     # missing, calculate checksum
#     checksum = 0
#     values = (udp_def_odim_stx,udp_msgno_nftp_start,len(data),navo_block_size,checksum,udp_def_odim_etx)
#     header = struct.pack('HH512xII4xHH', *values)
#
#     # Data gets packetized into chunks with size NAVO_DATA_SIZE
#     num_blocks = int(len(data) / navo_data_size) + 1
#
#     print("> will require", num_blocks, "blocks for data of size", len(data))
#     chunk_offset = 0
#     for block in range(num_blocks):
#         print("> doing block", block)
#         chunk_size = min(navo_data_size, len(data[chunk_offset:]))
#         print("> chunk size will be", chunk_size)
#
#         # Data block (20,032 bytes)
#         #    4 byte header (STX + msgID)
#         #    4 byte pad
#         #    4 byte uint for packetNo              (0,1,2,3,...)
#         #    4 byte uint for totalPackets
#         #    4 byte uint for numBytesInPacket (actual number of points in this message)
#         #    4 byte uint for totalBytes             (4,294,967,295 bytes maximum file size)
#         #    20000 byte data[20000];
#         #    4 bytes pad
#         #    4 byte footer (Checksum + ETX)
#
#         data_block = bytearray(navo_block_size)
#
#         values = (udp_def_odim_stx, udp_msgno_odim_nftp_data_packet, block, num_blocks, chunk_size, len(data),
#                   checksum, udp_def_odim_etx)
#
#         struct.pack_into('HH4xIIII%dx4xHH' % navo_data_size, data_block, 0, *values)
#         struct.pack_into('%ds' % chunk_size, data_block, 24, data[chunk_offset:chunk_offset+chunk_size])
#
#         #data_block[24:24+chunk_size] = data[chunk_offset:chunk_offset+chunk_size]
#
#         #print "Final packed block is", data_block
#
#         # Still need to the chunk into the data block
#         data_blocks.append(data_block)
#
#         chunk_offset = chunk_offset + chunk_size
#
#     # Footer (8 bytes)
#     #    4 byte header (STX + msgID)
#     #    4 byte footer (Checksum + ETX)
#     # missing, calculate checksum
#     checksum = 0
#     values = (udp_def_odim_stx, udp_msgno_nftp_stop, checksum, udp_def_odim_etx)
#     footer = struct.pack('HHHH', *values)
#
#     return header, data_blocks, footer
