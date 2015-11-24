from __future__ import absolute_import, division, print_function, unicode_literals

import os
import logging

log = logging.getLogger(__name__)

from .ssp import SspData
from .ssp_dicts import Dicts
from .helper import SspError
from .ssp_collection import SspCollection


class CastReader(object):

    here = os.path.abspath(os.path.dirname(__file__))

    def __init__(self):
        self.good_count = 0
        self.fail_count = 0
        self.casts = SspCollection()

    def read_casts_in_folder(self, cast_folder, input_format, time_ordered=True):

        if not os.path.exists(cast_folder):
            raise SspError("the passed cast folder does not exist: %s" % cast_folder)

        self._run_fmt_folder_tree(cast_folder, Dicts.import_extensions[input_format], input_format)

        if time_ordered:
            self.casts.date_time_sort()

    def _run_fmt_folder_tree(self, fmt_dir, fmt_ext, input_format):
        # top folder
        for root, sub_dirs, dir_files in os.walk(fmt_dir):
            log.debug("found %s file in the data folder: %s" % (root, len(dir_files)))

            for dir_file in dir_files:
                dir_file_name, dir_file_ext = os.path.splitext(dir_file)
                if fmt_ext in dir_file_ext.lower():
                    try:
                        self._run_fmt_load(os.path.join(root, dir_file), input_format)
                    except Exception as e:
                        log.error("Error loading %s: %s" % (dir_file, e))
                        self.fail_count += 1
                        continue

    def read_cast(self, cast_file, input_format):
        if not os.path.exists(cast_file):
            raise SspError("the passed cast file does not exist: %s" % cast_file)

        self._run_fmt_load(cast_file, input_format)

    def _run_fmt_load(self, load_file, input_format):
        log.debug("%s [%s]" % (load_file, input_format))
        # read the different file formats
        ssp = SspData()
        ssp.read_input_file_by_format(load_file, input_format)

        if not ssp.date_time:
            log.warning("missing date/time: %s" % load_file)

        if ssp.data.shape[1] == 0:
            raise SspError("not retrieved samples in reading: %s" % load_file)

        self.casts.append(ssp)
        self.good_count += 1

    def total_read_casts(self):
        return len(self.casts.data)

    def test_drivers(self, time_ordered=True):

        data_root_folder = os.path.join(self.here, 'data', 'samples')

        for fmt in Dicts.import_formats:
            fmt_ext = Dicts.import_extensions[Dicts.import_formats[fmt]]
            log.debug("testing %s (%s)" % (fmt, fmt_ext))

            if "_" in fmt:
                base_folder, sub_folder = fmt.lower().split("_", 1)
                fmt_folder = os.path.abspath(os.path.join(data_root_folder, base_folder, sub_folder))
            else:
                fmt_folder = os.path.abspath(os.path.join(data_root_folder, fmt.lower()))

            if not os.path.exists(fmt_folder):
                log.debug("invalid data path: %s" % fmt_folder)
                continue
            log.debug("reading test data from: %s" % fmt_folder)

            self._run_fmt_folder_tree(fmt_folder, fmt_ext, Dicts.import_formats[fmt])

        if time_ordered:
            self.casts.date_time_sort()
