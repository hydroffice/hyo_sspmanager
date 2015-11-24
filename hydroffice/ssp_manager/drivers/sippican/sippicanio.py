from __future__ import absolute_import, division, print_function, unicode_literals

from ..udpio import UdpIO
from . import sippican
import logging

log = logging.getLogger(__name__)


class SippicanIO(UdpIO):

    def __init__(self, listen_port, desired_datagrams, timeout):
        UdpIO.__init__(self, listen_port, desired_datagrams, timeout)
        self.name = "SIP"
        self.cast = None

    def parse(self):
        self.cast = sippican.Sippican(self.data)
