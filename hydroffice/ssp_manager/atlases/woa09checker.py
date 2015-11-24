from __future__ import absolute_import, division, print_function, unicode_literals

import os
import logging

log = logging.getLogger(__name__)

from ..helper import Helper as BaseHelper
from hydroffice.base.ftpconnector import FtpConnector


class Woa09Checker(object):

    def __init__(self, force_download=True, verbose=True):
        self.verbose = verbose
        self.present = False
        self.atlases_folder = self.get_atlases_folder()
        if not self.is_present() and force_download:
            self.present = self.download_and_unzip()
        else:
            self.present = True

    @classmethod
    def get_atlases_folder(cls):
        """return the folder used to store atlases"""
        ssp_folder = BaseHelper.default_projects_folder()
        return os.path.join(ssp_folder, 'Atlases')

    @classmethod
    def is_present(cls):
        """check if the WOA09 atlas is present"""
        atlases_folder = cls.get_atlases_folder()
        if not os.path.exists(atlases_folder):
            log.debug('not found atlases folder')
            return False

        check_woa09_file = os.path.join(atlases_folder, 'woa09', 'landsea.msk')
        log.debug("checking WOA09 test file at path %s" % check_woa09_file)
        if not os.path.exists(check_woa09_file):
            log.debug('not found woa09 atlas')
            return False

        return True

    def download_and_unzip(self):
        """attempt to download the WOA09 atlas"""
        log.debug('downloading WOA9 atlas')

        try:
            if not os.path.exists(self.atlases_folder):
                os.makedirs(self.atlases_folder)

            ftp = FtpConnector("ftp.ccom.unh.edu", show_progress=True, debug_mode=False)
            data_zip_src = "fromccom/hydroffice/woa09.zip"
            data_zip_dst = os.path.join(self.atlases_folder, "woa09.zip")
            ftp.get_file(data_zip_src, data_zip_dst, unzip_it=True)
            return self.is_present()

        except Exception as e:
            log.error('during WOA09 download and unzip: %s' % e)
            return False
