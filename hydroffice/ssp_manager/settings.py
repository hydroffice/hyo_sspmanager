from __future__ import absolute_import, division, print_function, unicode_literals

import datetime
import os
import shutil

import logging

log = logging.getLogger(__name__)

from .ssp_dicts import Dicts
from .helper import SspError, Helper
from .pkg_clients import PkgClientList
from .atlases import woa09checker


class Settings(object):

    here = os.path.abspath(os.path.dirname(__file__))

    def __init__(self):

        self.export_formats = {
            'ASVP': False,
            'PRO': False,
            'VEL': False,
            'HIPS': False,
            'IXBLUE': False,
            'UNB': False,
            'ELAC': False,
            'CSV': False
        }

        self.filename_prefix = None

        self.inspection_mode = Dicts.inspections_mode['Zoom']

        # oceanographic data sources
        self.ssp_extension_source = Dicts.extension_sources["WOA09"]
        self.ssp_salinity_source = Dicts.salinity_sources["WOA09"]
        self.ssp_temp_sal_source = Dicts.temp_sal_sources["WOA09"]
        self.sis_server_source = Dicts.sis_server_sources["WOA09"]
        self.woa_path = None

        # processing
        self.ssp_up_or_down = Dicts.ssp_directions["down"]
        self.rx_max_wait_time = 30

        # metadata
        self.log_processing_metadata = False
        self.log_server_metadata = False

        # user export settings
        self.user_append_caris_file = False
        self.user_export_prompt_filename = True
        self.user_export_directory = None
        self.user_filename_prefix = None
        self.auto_export_on_send = False

        # user insert
        self.user_speed = None
        self.user_salinity = None
        self.user_temperature = None
        self.user_depth = None

        # server settings
        self.server_append_caris_file = False
        self.server_caris_filename = ""
        self.auto_export_on_server_send = False
        self.server_apply_surface_sound_speed = False

        # sis settings
        self.km_listen_port = 16103
        self.km_listen_timeout = 1
        self.sis_auto_apply_manual_casts = True

        # Sippican settings
        self.sippican_listen_port = 2002
        self.sippican_listen_timeout = 1

        # MVP settings
        self.mvp_ip_address = "127.0.0.1"
        self.mvp_listen_port = 2006
        self.mvp_listen_timeout = 1
        self.mvp_transmission_protocol = "NAVO_ISS60"
        self.mvp_format = "S12"
        self.mvp_winch_port = 3601
        self.mvp_fish_port = 3602
        self.mvp_nav_port = 3603
        self.mvp_system_port = None
        self.mvp_sw_version = 2.47
        self.mvp_instrument = "AML_uSVP"
        self.mvp_instrument_id = "M"

        self.client_list = PkgClientList()

    def load_config(self):
        """read the configuration info present in the settings file"""

        ini_file = 'config.ini'

        # check if the config.ini exists in the user application folder
        user_folder = Helper.default_projects_folder()
        ini_path = os.path.join(user_folder, ini_file)
        if not os.path.exists(ini_path):
            original_ini_path = os.path.join(self.here, ini_file)
            if not os.path.exists(original_ini_path):
                raise SspError("unable to find original settings at %s" % original_ini_path)
            shutil.copyfile(original_ini_path, ini_path)

        # read the whole settings file
        try:
            infile = open(ini_path, 'r')
            ini_content = infile.read()
            infile.close()

        except IOError:
            raise SspError("Troubles in reading the settings file: %s" % ini_path)

        # evaluate settings file line-by-line
        for line_str in ini_content.splitlines():

            # validity checks
            if len(line_str) == 0:
                log.debug("%s: skipping zero length line" % ini_file)
                continue
            elif line_str[0] == "#":
                log.debug("%s: skipping comment line:\n  %s" % (ini_file, line_str))
                continue

            num_fields = len(line_str.split("="))
            if num_fields != 2:
                log.warning("%s: invalid line:\n  %s" % (ini_file, line_str))
                continue

            field_name = line_str.split("=")[0]
            field_value = line_str.split("=")[-1]

            log.debug("%s: valid pair: -> %s + %s" % (ini_file, field_name, field_value))

            # finally read the stored information
            if field_name == "ssp_extension_source":
                if not field_value:  # default
                    self.ssp_extension_source = Dicts.extension_sources["WOA09"]
                else:
                    if field_value not in Dicts.extension_sources:
                        raise SspError("invalid ssp_extension_source: %s" % field_value)
                    self.ssp_extension_source = Dicts.extension_sources[field_value]

            elif field_name == "ssp_salinity_source":
                if not field_value:  # default
                    self.ssp_salinity_source = Dicts.salinity_sources["WOA09"]
                else:
                    if field_value not in Dicts.extension_sources:
                        raise SspError("invalid ssp_salinity_source: %s" % field_value)
                    self.ssp_salinity_source = Dicts.salinity_sources[field_value]

            elif field_name == "ssp_temp_sal_source":
                if not field_value:  # default
                    self.ssp_temp_sal_source = Dicts.temp_sal_sources["WOA09"]
                else:
                    if field_value not in Dicts.extension_sources:
                        raise SspError("invalid ssp_temperature_salinity_source: %s" % field_value)
                    self.ssp_temp_sal_source = Dicts.temp_sal_sources[field_value]

            elif field_name == "sis_server_source":
                if not field_value:  # default
                    self.sis_server_source = Dicts.sis_server_sources["WOA09"]
                else:
                    if field_value not in Dicts.extension_sources:
                        raise SspError("invalid sis_server_source: %s" % field_value)
                    self.sis_server_source = Dicts.sis_server_sources[field_value]

            elif field_name == "woa_path":
                if not field_value:  # default
                    field_value = os.path.join(woa09checker.Woa09Checker.get_atlases_folder(), 'woa09')
                    if not os.path.exists(field_value):
                        try:
                            os.makedirs(field_value)
                        except OSError:
                            raise SspError("unable to create default WOA09 path folder")
                    log.info("default woa path: %s" % field_value)
                if os.path.isabs(field_value):
                    self.woa_path = field_value
                else:  # relative to this file
                    woa_abs_path = os.path.abspath(os.path.join(self.here, field_value))
                    if os.path.exists(woa_abs_path):
                        self.woa_path = woa_abs_path
                    else:
                        self.woa_path = None
                        log.warning("%s: invalid WOA path:\n  %s" % (ini_file, field_value))

            elif field_name == "ssp_up_or_down":
                if not field_value:  # default
                    self.ssp_up_or_down = Dicts.ssp_directions["down"]
                else:
                    if not (field_value in Dicts.ssp_directions):
                        raise SspError("invalid ssp_up_or_down: %s" % field_value)
                    self.ssp_up_or_down = Dicts.ssp_directions[field_value]

            elif field_name == "auto_export_on_send":
                if not field_value:
                    field_value = "False"
                if field_value == "True":
                    self.auto_export_on_send = True
                else:
                    self.auto_export_on_send = False

            elif field_name == "auto_export_on_server_send":
                if not field_value:
                    field_value = "True"
                if field_value == "True":
                    self.auto_export_on_server_send = True
                else:
                    self.auto_export_on_server_send = False

            elif field_name == "user_export_prompt_filename":
                if not field_value:
                    field_value = "False"
                if field_value == "True":
                    self.user_export_prompt_filename = True
                else:
                    self.user_export_prompt_filename = False

            elif field_name == "user_append_caris_file":
                if not field_value:
                    field_value = "False"
                if field_value == "True":
                    self.user_append_caris_file = True
                else:
                    self.user_append_caris_file = False

            elif field_name == "client_list":
                self.client_list.add_client(field_value)

            elif field_name == "km_listen_port":
                if not field_value:
                    field_value = "16103"
                try:
                    self.km_listen_port = int(field_value)
                except ValueError:
                    raise SspError("invalid km_listen_port: %s" % field_value)

            elif field_name == "km_listen_timeout":
                if not field_value:
                    field_value = "1"
                try:
                    self.km_listen_timeout = int(field_value)
                except ValueError:
                    raise SspError("invalid km_listen_timeout: %s" % field_value)

            elif field_name == "sis_auto_apply_manual_casts":
                if not field_value:
                    field_value = "True"
                if field_value == "True":
                    self.sis_auto_apply_manual_casts = True
                else:
                    self.sis_auto_apply_manual_casts = False

            elif field_name == "server_apply_surface_sound_speed":
                if not field_value:
                    field_value = "True"
                if field_value == "True":
                    self.server_apply_surface_sound_speed = True
                else:
                    self.server_apply_surface_sound_speed = False

            elif field_name == "server_append_caris_file":
                if not field_value:
                    field_value = "False"
                if field_value == "True":
                    self.server_append_caris_file = True
                else:
                    self.server_append_caris_file = False

            elif field_name == "sippican_listen_port":
                if not field_value:
                    field_value = "2002"
                try:
                    self.sippican_listen_port = int(field_value)
                except ValueError:
                    raise SspError("invalid sippican_listen_port: %s" % field_value)

            elif field_name == "sippican_listen_timeout":
                if not field_value:
                    field_value = "1"
                try:
                    self.sippican_listen_timeout = int(field_value)
                except ValueError:
                    raise SspError("invalid sippican_listen_timeout: %s" % field_value)

            elif field_name == "mvp_ip_address":
                self.mvp_ip_address = field_value

            elif field_name == "mvp_listen_port":
                self.mvp_listen_port = int(field_value)

            elif field_name == "mvp_listen_timeout":
                self.mvp_listen_timeout = int(field_value)

            elif field_name == "mvp_transmission_protocol":
                self.mvp_transmission_protocol = field_value

            elif field_name == "mvp_format":
                self.mvp_format = field_value

            elif field_name == "mvp_ip_address":
                self.mvp_ip_address = field_value

            elif field_name == "mvp_winch_port":
                self.mvp_winch_port = int(field_value)

            elif field_name == "mvp_fish_port":
                self.mvp_fish_port = int(field_value)

            elif field_name == "mvp_nav_port":
                self.mvp_nav_port = int(field_value)

            elif field_name == "mvp_system_port":
                if field_value == "None":
                    self.mvp_system_port = None
                else:
                    self.mvp_system_port = int(field_value)

            elif field_name == "mvp_sw_version":
                self.mvp_sw_version = float(field_value)

            elif field_name == "mvp_instrument":
                self.mvp_instrument = field_value

            elif field_name == "mvp_instrument_id":
                self.mvp_instrument_id = field_value

            else:
                log.warning("%s: unknown pair:  %s + %s" % (ini_file, field_name, field_value))
                continue

    def switch_export_format(self, fmt):
        log.debug("switching %s" % fmt)

        try:
            self.export_formats[fmt] = not self.export_formats[fmt]

        except KeyError:
            raise SspError("Unknown export data format: %s" % fmt)

    def clear_user_samples(self):
        self.user_speed = None
        self.user_salinity = None
        self.user_temperature = None
        self.user_depth = None

    def __str__(self):
        output = " ### SSP Settings (time stamp: %s) ###\n\n" % datetime.datetime.now().isoformat()

        output += "\n > Oceanographic data sources\n"
        output += "   - ssp_extension_source:  %s\n" % self.ssp_extension_source
        output += "   - ssp_salinity_source:  %s\n" % self.ssp_salinity_source
        output += "   - ssp_temp_sal_source:  %s\n" % self.ssp_temp_sal_source
        output += "   - sis_server_source:  %s\n" % self.sis_server_source
        output += "   - woa_path:  %s\n" % self.woa_path

        output += "\n > Processing\n"
        output += "   - ssp_up_or_down:  %s\n" % self.ssp_up_or_down

        output += "\n > User\n"
        output += "   - user_append_caris_file:  %s\n" % self.user_append_caris_file
        output += "   - user_export_prompt_filename:  %s\n" % self.user_export_prompt_filename
        output += "   - user_export_directory:  %s\n" % self.user_export_directory
        output += "   - user_filename_prefix:  %s\n" % self.user_filename_prefix
        output += "   - auto_export_on_send:  %s\n" % self.auto_export_on_send

        output += "\n > User insert\n"
        output += "   - user_speed:  %s\n" % self.user_speed
        output += "   - user_salinity:  %s\n" % self.user_salinity
        output += "   - user_temperature:  %s\n" % self.user_temperature
        output += "   - user_depth:  %s\n" % self.user_depth

        output += "\n > Server\n"
        output += "   - server_append_caris_file: %s\n" % self.server_append_caris_file
        output += "   - server_caris_filename: %s\n" % self.server_caris_filename
        output += "   - auto_export_on_server_send: %s\n" % self.auto_export_on_server_send
        output += "   - server_apply_surface_sound_speed: %s\n" % self.server_apply_surface_sound_speed

        output += "\n > SIS settings\n"
        output += "   - km_listen_port: %s\n" % self.km_listen_port
        output += "   - km_listen_timeout: %s\n" % self.km_listen_timeout
        output += "   - sis_auto_apply_manual_casts: %s\n" % self.sis_auto_apply_manual_casts

        output += "\n > Sippican settings\n"
        output += "   - sippican_listen_port: %s\n" % self.sippican_listen_port
        output += "   - sippican_listen_timeout: %s\n" % self.sippican_listen_timeout

        output += "\n > MVP settings\n"
        output += "   - mvp_ip_address: %s, mvp_listen_port: %s\n" % (self.mvp_ip_address, self.mvp_listen_port)
        output += "   - mvp_listen_timeout: %s\n" % self.mvp_listen_timeout
        output += "   - mvp_transmission_protocol: %s\n" % self.mvp_transmission_protocol
        output += "   - mvp_format: %s\n" % self.mvp_format
        output += "   - mvp_winch_port: %s, mvp_fish_port: %s, mvp_nav_port: %s, mvp_system_port: %s\n" \
                  % (self.mvp_winch_port, self.mvp_fish_port, self.mvp_nav_port, self.mvp_system_port)
        output += "   - mvp_sw_version: %s\n" % self.mvp_sw_version
        output += "   - mvp_instrument: %s\n" % self.mvp_instrument
        output += "   - mvp_instrument_id: %s\n" % self.mvp_instrument_id

        output += "\n > Metadata\n"
        output += "   - log_server_metadata: %s\n" % self.log_server_metadata
        output += "   - log_processing_metadata: %s\n" % self.log_processing_metadata

        output += "\n > Clients\n"
        for cln in self.client_list.clients:
            output += "   - %s %s:%s %s [%s]\n" % (cln.name, cln.IP, cln.port, cln.protocol, cln.alive)

        return output

    def print_all(self):
        print(self)
