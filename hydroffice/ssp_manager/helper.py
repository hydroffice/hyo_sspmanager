from __future__ import absolute_import, division, print_function, unicode_literals

import os
import logging

log = logging.getLogger(__name__)

from hydroffice.base import helper


class SspError(helper.HyOError):
    """ Error raised for SSP issues """
    def __init__(self, message, *args):
        self.message = message
        # allow users initialize misc. arguments as any other builtin Error
        super(SspError, self).__init__(message, *args)


class Helper(helper.Helper):
    """ A collection class with many helper functions """

    def __init__(self):
        super(Helper, self).__init__()

    @staticmethod
    def default_projects_folder():
        """ Overloaded function that calls the parent function and adds package specific directory """
        from . import __doc__
        from . import __version__

        hyo_folder = helper.Helper.default_projects_folder()

        projects_folder = os.path.join(hyo_folder, "%s %s" % (__doc__, __version__))

        if not os.path.exists(projects_folder):
            try:
                os.mkdir(projects_folder)
            except OSError as e:
                raise SspError("Error in creating the default projects folder: %s\n%s" % (projects_folder, e))

        return projects_folder
