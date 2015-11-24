from __future__ import absolute_import, division, print_function, unicode_literals

import logging


class ParsingFilter(logging.Filter):
    def filter(self, record):
        # print(record.name, record.levelname)
        if record.name.startswith('hydroffice.ssp.settings') and (record.levelname == "DEBUG"):
            return False
        return True


# logging settings
logger = logging.getLogger()
logger.setLevel(logging.NOTSET)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)  # change to WARNING to reduce verbosity, DEBUG for high verbosity
ch_formatter = logging.Formatter('%(levelname)-9s %(name)s.%(funcName)s:%(lineno)d > %(message)s')
ch.setFormatter(ch_formatter)
ch.addFilter(ParsingFilter())
logger.addHandler(ch)

from .oldgui import ssp_gui

ssp_gui.gui()



