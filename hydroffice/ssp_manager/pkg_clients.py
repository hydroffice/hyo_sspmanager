from __future__ import absolute_import, division, print_function, unicode_literals

import logging

log = logging.getLogger(__name__)

from .ssp_dicts import Dicts


class PkgClient(object):
    def __init__(self, client):

        self.name = client.split(":")[0]
        self.IP = client.split(":")[1]
        self.port = int(client.split(":")[2])
        self.protocol = client.split(":")[3]
        self.alive = True
        log.info("new client: %s(%s:%s) %s" % (self.name, self.IP, self.port, self.protocol))

    def send_cast(self, ssp_data, fmt):

        if (self.protocol == "QINSY") or (self.protocol == "PDS2000"):
            fmt = Dicts.kng_formats['S12']
            log.info("forcing S12 format")

        if (self.protocol == "QINSY") or (self.protocol == "SIS") or (self.protocol == "PDS2000"):
            log.info("sending by km function")
            ssp_data.send_km(self.IP, self.port, fmt)

        elif self.protocol == "HYPACK":
            log.info("sending by hypack function")
            ssp_data.send_hypack(self.IP, self.port)


class PkgClientList(object):
    def __init__(self):
        self.num_clients = 0
        self.clients = []

    def add_client(self, client):
        client = PkgClient(client)
        self.clients.append(client)
        self.num_clients += 1
