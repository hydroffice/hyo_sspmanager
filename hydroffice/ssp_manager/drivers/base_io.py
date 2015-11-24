from __future__ import absolute_import, division, print_function, unicode_literals

from abc import ABCMeta, abstractmethod
import logging

log = logging.getLogger(__name__)

from hydroffice.base.base_objects import BaseObject
from ..helper import SspError


class IoError(SspError):
    """ Error raised for atlas issues """
    def __init__(self, message, *args):
        self.message = message
        # allow users initialize misc. arguments as any other builtin Error
        super(IoError, self).__init__(message, *args)


class BaseIo(BaseObject):
    """ Common IO base class """

    __metaclass__ = ABCMeta

    def __init__(self):
        super(BaseIo, self).__init__()
        self.name = "BAS"

    @abstractmethod
    def listen(self):
        log.error("to be overloaded")
