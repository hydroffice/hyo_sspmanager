from __future__ import absolute_import, division, print_function, unicode_literals

import socket
import struct
import operator
import time
import logging

log = logging.getLogger(__name__)

from . import km
from ..udpio import UdpIO


class KmIO(UdpIO):
    def __init__(self, listen_port, desired_datagrams, timeout):

        UdpIO.__init__(self, listen_port, desired_datagrams, timeout)
        self.name = "KNG"

        # A few Nones to accommodate the potential types of datagrams that are currently supported
        self.id = None
        self.surface_ssp = None
        self.nav = None
        self.ssp = None
        self.installation = None
        self.runtime = None
        self.svp_input = None
        self.xyz88 = None
        self.range_angle78 = None
        self.seabed_image89 = None
        self.watercolumn = None
        self.bist = None

        self.dg_names = {
            48: 'PU Id output',
            49: 'PU Status',
            65: 'Attitude',
            66: 'BIST Output',
            67: 'Clock',
            68: 'Depth',
            71: 'Surface Sound Speed',
            72: 'Heading',
            73: 'Installation Parameters (start)',
            78: 'Raw Range and Angle (78)',
            80: 'Position',
            82: 'Runtime Parameters',
            83: 'Seabed Image',
            85: 'Sound Speed Profile (new)',
            88: 'XYZ (88)',
            89: 'Seabed Imagery (89)',
            102: 'Raw Beam and Angle (new)',
            105: 'Installation Parameters (stop)',
            107: 'Watercolumn',
            110: 'Network Attitude Velocity'
        }

    @classmethod
    def request_iur(cls, remote_ip):
        sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # We try all of them in the hopes that one works.
        codes = ["710", "122", "302", "3020", "2040"]
        for sensor in codes:
            # Leaving this statement on until I have a chance to test with all systems.
            log.info("Requesting SVP from sensor %s" % sensor)

            # talker ID, Roger Davis (HMRG) suggested SM based on something KM told him
            output = '$SMR20,EMX=%s,' % sensor

            # calculate checksum, XOR of all bytes after the $
            import functools
            checksum = functools.reduce(operator.xor, map(ord, output[1:len(output)]))

            # append the checksum and end of datagram identifier
            output += "*{0:02x}".format(checksum)
            output += "\\\r\n"

            sock_out.sendto(output.encode('utf-8'), (remote_ip, 4001))

            # Adding a bit of a pause
            time.sleep(1)

        sock_out.close()

    def parse(self):

        this_data = self.data[:]
        self.id = struct.unpack("<BB", this_data[0:2])[1]

        try:
            name = self.dg_names[self.id]
        except KeyError:
            name = "Unknown name"

        # log.info("%s > DG %d/0x%x/%c [%s] > sz: %.1f KB"
        #                 % (self.sender, self.id, self.id, self.id, name, len(this_data)/1024))

        if not (self.id in self.desired_datagrams):
            return

        if self.id == 0x42:
            self.bist = km.KmBist(this_data)

        elif self.id == 0x47:
            self.surface_ssp = km.KmSsp(this_data)

        elif self.id == 0x49:
            self.installation = km.KmInstallation(this_data)

        elif self.id == 0x4e:
            self.range_angle78 = km.KmRangeAngle78(this_data)

        elif self.id == 0x50:
            self.nav = km.KmNav(this_data)

        elif self.id == 0x52:
            self.runtime = km.KmRuntime(this_data)

        elif self.id == 0x55:
            self.ssp = km.KmSvp(this_data)

        elif self.id == 0x57:
            self.svp_input = km.KmSvpInput(this_data)

        elif self.id == 0x58:
            self.xyz88 = km.KmXyz88(this_data)

        elif self.id == 0x59:
            self.seabed_image89 = km.KmSeabedImage89(this_data)

        elif self.id == 0x6b:
            self.watercolumn = km.KmWatercolumn(this_data)

        else:
            log.error("Missing parser for datagram type: %s" % self.id)

    def log_to_file(self, data):
        # This currently writes data in a Kongsberg .all format.
        # This involves writing the length of each datagram as a 4-byte
        # unsigned integer prior to writing out the datagram.
        # This is currently hard-wired for little-endian byte-ordering.
        l = struct.pack("<I", len(data))
        self.logfile.write(l)
        self.logfile.write(data)
