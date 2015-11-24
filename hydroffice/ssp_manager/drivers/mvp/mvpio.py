from __future__ import absolute_import, division, print_function, unicode_literals

import logging

log = logging.getLogger(__name__)

from ..udpio import UdpIO
from . import mvp
from ...helper import SspError


class MvpCastIO(UdpIO):
    def __init__(self, listen_port, desired_datagrams, timeout, protocol, fmt):
        UdpIO.__init__(self, listen_port, desired_datagrams, timeout)
        self.name = "MVP"
        self.cast = None

        try:
            self.protocol = mvp.Mvp.protocols[protocol]
        except KeyError:
            raise SspError("passed unknown protocol: %s" % protocol)
        try:
            self.format = mvp.Mvp.formats[fmt]
        except KeyError:
            raise SspError("passed unknown format: %s" % fmt)

        self.header = str()
        self.footer = str()
        self.data_blocks = []

        self.num_data_blocks = 0

        self.got_header = False
        self.got_data = False
        self.got_footer = False

    def parse(self):
        log.info("Going to parse data of length %s using protocol %s" % (len(self.data), self.protocol))

        if self.protocol == mvp.Mvp.protocols["NAVO_ISS60"]:

            if len(self.data) == 536:
                log.info("got header")
                self.header = self.data
                self.got_header = True
                self.got_footer = False
                self.got_data = False
                self.num_data_blocks = 0

            elif len(self.data) == 20032:
                log.info(" got data block")
                self.got_data = True
                self.data_blocks.append(self.data)
                self.num_data_blocks += 1

            elif len(self.data) == 8:
                log.info("got footer")
                self.footer = self.data
                self.got_footer = True

            if self.got_header and self.got_data and self.got_footer:
                log.info("going to assemble cast!")
                log.info("got lengths: %s %s %s"
                         % (len(self.header), len(self.data_blocks), len(self.footer)))
                log.info("got num data blocks: %s" % self.num_data_blocks)

                self.cast = mvp.Mvp(self.header, self.data_blocks, self.footer, self.protocol, self.format)

                self.got_header = False
                self.header = None
                self.got_data = False
                self.data_blocks = []
                self.num_data_blocks = 0
                self.got_footer = False
                self.footer = None

        elif self.protocol == mvp.Mvp.protocols["UNDEFINED"]:
            log.info("going to parse with UNDEFINED protocol!!")
            log.info("the data is %s" % self.data)
            self.data_blocks.append(self.data)
            self.num_data_blocks += 1
            self.cast = mvp.Mvp(self.header, self.data_blocks, self.footer, self.protocol, self.format)
