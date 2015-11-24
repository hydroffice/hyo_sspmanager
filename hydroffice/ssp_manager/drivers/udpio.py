from __future__ import absolute_import, division, print_function, unicode_literals

from abc import ABCMeta, abstractmethod
import socket
import threading
import logging

log = logging.getLogger(__name__)

from .base_io import BaseIo, IoError


class UdpIO(BaseIo):

    __metaclass__ = ABCMeta

    def __init__(self, listen_port, desired_datagrams, timeout):
        super(UdpIO, self).__init__()
        self.listen_port = listen_port
        self.desired_datagrams = desired_datagrams
        self.timeout = timeout
        self.data = None
        self.sender = None
        self.sock_in = None

        # A few controls on behaviour
        self.do_listen = False
        self.listening = False

        # Goodies for logging to memory
        self.logging_to_memory = False
        self.logged_data = []

        # Goodies for logging to file
        self.logging_to_file = False
        self.logfile = None
        self.logfile_name = None

    def start_logging(self):
        """ This method is meant to be over-ridden """
        log.error("to be overloaded")

    def stop_logging(self):
        """ This method is meant to be over-ridden """
        log.error("to be overloaded")

    def clear_logged_data(self):
        self.logged_data = []

    def open_log_file(self, fname):
        self.logfile_name = fname
        self.logfile = open(fname, "wb")
        return

    def close_log_file(self):
        self.logfile.close()
        self.logfile = None
        self.logfile_name = None
        return

    def start_listen(self, logfilename=''):
        if logfilename != '':
            self.open_log_file(logfilename)
            self.logging_to_file = True

        self.listening = True
        log.info("starting listen thread")
        threading.Thread(target=self.listen).start()
        log.info("started listen thread")

    def listen(self):

        self.sock_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_in.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2 ** 16)

        if self.timeout > 0:
            self.sock_in.settimeout(self.timeout)

        try:
            self.sock_in.bind(("0.0.0.0", self.listen_port))

        except socket.error as e:
            self.listening = False
            self.sock_in.close()
            log.info("port %d already bound? Not listening anymore. Error: %s" % (self.listen_port, e))
            return

        log.info("going to listen on port %s for datagrams %s" % (self.listen_port, self.desired_datagrams))
        self.do_listen = True
        self.listening = True

        while self.do_listen:
            try:
                self.data, self.sender = self.sock_in.recvfrom(2 ** 16)

            except socket.timeout:
                # log.info("socket timeout")
                continue

            if self.logging_to_file and self.logfile:
                log.info("going to write to output file %s length is %s bytes"
                         % (self.logfile_name, len(self.data)))

                self.log_to_file(self.data)

            if self.logging_to_memory:
                self.logged_data.append(self.data)

            self.parse()

        self.sock_in.close()

        log.info("done listening!")

    def stop_listen(self):
        self.do_listen = False

    def parse(self):
        return

    def log_to_file(self, data):
        self.logfile.write(data)
