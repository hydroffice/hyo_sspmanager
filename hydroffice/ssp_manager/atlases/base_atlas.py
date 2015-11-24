from __future__ import absolute_import, division, print_function, unicode_literals

from abc import ABCMeta, abstractmethod
import logging

log = logging.getLogger(__name__)

from ..helper import SspError
from hydroffice.base.geodesy import Geodesy


class AtlasError(SspError):
    """ Error raised for atlas issues """
    def __init__(self, message, *args):
        self.message = message
        # allow users initialize misc. arguments as any other builtin Error
        super(AtlasError, self).__init__(message, *args)


class Atlas(object):
    """ Common atlas base class """

    __metaclass__ = ABCMeta

    def __init__(self):
        super(Atlas, self).__init__()
        self.name = "UNK"
        self.source_info = "Unknown Atlas"

        self.g = Geodesy()

    @abstractmethod
    def query(self, latitude, longitude, date_time):
        log.error("to be overloaded")
