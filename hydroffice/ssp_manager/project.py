from __future__ import absolute_import, division, print_function, unicode_literals

import os
import time
import datetime as dt
import numpy as np
import logging

log = logging.getLogger(__name__)

from hydroffice.base import project
from hydroffice.base.logging_sqlite import SQLiteHandler
from hydroffice.base.timerthread import TimerThread

from .server import Server
from .helper import Helper
from .helper import SspError
from .ssp_dicts import Dicts
from .ssp import SspData
from .settings import Settings
from .drivers.mvp.mvpio import MvpCastIO
#from .drivers.mvp.mvp_controller import MVPController
from .drivers.km.kmio import KmIO
from .drivers.sippican.sippicanio import SippicanIO
from .atlases import woa09
from .atlases import rtofs


class ServerFilter(logging.Filter):
    def filter(self, record):
        # print(record.name, record.levelname)
        if record.name.startswith('hydroffice.ssp.server'):
            return True
        return False


class NotServerFilter(logging.Filter):
    def filter(self, record):
        # print(record.name, record.levelname)
        if record.name.startswith('hydroffice.ssp.server'):
            return False
        return True


class Project(project.Project):
    """ SSP project """

    here = os.path.abspath(os.path.dirname(__file__))

    def __init__(self, with_listeners=True, with_woa09=True, with_rtofs=True):
        super(Project, self).__init__(Helper.default_projects_folder())

        self.log_sh = SQLiteHandler(db=os.path.join(Helper.default_projects_folder(), "__log__.db"))
        self.log_sh.setLevel(logging.DEBUG)
        self.log_sh.addFilter(NotServerFilter())

        self.log_server_sh = SQLiteHandler(db=os.path.join(Helper.default_projects_folder(), "__server_log__.db"))
        self.log_server_sh.setLevel(logging.DEBUG)
        self.log_server_sh.addFilter(ServerFilter())

        self.server = Server(self)
        self.with_listeners = with_listeners

        # atlases settings
        self.with_woa09 = with_woa09
        self.woa09_atlas_loaded = False
        if self.with_woa09:
            self.woa09_atlas = woa09.Woa09()
            self.ssp_woa = None
            self.ssp_woa_min = None
            self.ssp_woa_max = None

        self.with_rtofs = with_rtofs
        self.rtofs_atlas_loaded = False
        if self.with_rtofs:
            self.rtofs_atlas = rtofs.RTOFS()

        self.server_timer = None

        self.has_sippican_to_process = False
        self.has_mvp_to_process = False

        self.filename = None
        self.filename_suffix = None
        self.time_of_last_tx = None
        self.surface_speed_applied = False
        self.ssp_applied_depth = 0  # > TODO: is properly applied in RunSever?
        self.has_ssp_loaded = False

        self.ssp_reference = None
        self.ssp_reference_filename = ""

        self.s = Settings()
        self.s.load_config()

        self.ssp_data = SspData()

        self.mean_depth = None
        self.vessel_draft = None
        self.surface_sound_speed = None

        # listeners
        self.km_listener = None

        self.mvp_listener = None
        self.mvp_timer = None
        self.mvp_controller = None
        self.mvp_sensors_timer = None

        self.sippican_listener = None
        self.sippican_timer = None

        # This is the default configuration
        self.ssp_recipient_ip = "127.0.0.1"
        self.ssp_recipient_port = 4001

        # optional initialization
        if self.with_woa09:
            self.load_woa09_atlas()

        if self.with_rtofs:
            self.load_rtofs_atlas()

        if self.with_listeners:
            self.init_listeners()
            self._init_timers()

    def init_listeners(self):
        """ build listeners and start to listen """

        self.km_listener = KmIO(self.s.km_listen_port, [0x50, 0x52, 0x55, 0x58], self.s.km_listen_timeout)
        self.km_listener.start_listen()

        self.sippican_listener = SippicanIO(self.s.sippican_listen_port, ["Deep Blue"], self.s.sippican_listen_timeout)
        self.sippican_listener.start_listen()

        self.mvp_listener = MvpCastIO(self.s.mvp_listen_port, [], self.s.mvp_listen_timeout,
                                      self.s.mvp_transmission_protocol, self.s.mvp_format)
        self.mvp_listener.start_listen()

        # self.mvp_controller = MVPController(self.s.mvp_ip_address, self.s.mvp_winch_port, self.s.mvp_fish_port,
        #                                     self.s.mvp_nav_port, self.s.mvp_system_port, self.s.mvp_sw_version,
        #                                     self.s.mvp_instrument_id, self.s.mvp_instrument)
        # self.mvp_controller.start_listen()

    def _init_timers(self):
        """ initialize timers """
        # timer to monitor for Sippican inputs
        self.sippican_timer = TimerThread(self._monitor_sippican, timing=3)
        self.sippican_timer.start()

        # timer to monitor for MVP cast inputs
        self.mvp_timer = TimerThread(self._monitor_mvp, timing=2.1)
        self.mvp_timer.start()

        # timer to monitor for MVP sensor input
        self.mvp_sensors_timer = TimerThread(self._monitor_mvp_sensors, timing=1.5)
        # self.mvp_sensors_timer.start()

    def open_file_format(self, filename, input_format, callback_date=None, callback_pos=None):
        filename_prefix = os.path.splitext(filename)[0]
        filename_suffix = os.path.splitext(filename)[1]
        log.info("filename prefix: %s" % filename_prefix)
        log.info("filename suffix: %s" % filename_suffix)

        # read the different file formats
        ssp = SspData()

        if input_format == Dicts.import_formats["CASTAWAY"]:
            ssp.read_input_file_by_format(filename, input_format)
            ssp.reduce_up_down(self.s.ssp_up_or_down)

        elif input_format == Dicts.import_formats["DIGIBAR_PRO"]:
            ssp.read_input_file_by_format(filename, input_format)
            ssp.reduce_up_down(self.s.ssp_up_or_down)

        elif input_format == Dicts.import_formats["DIGIBAR_S"]:
            ssp.read_input_file_by_format(filename, input_format)
            ssp.reduce_up_down(self.s.ssp_up_or_down)

        elif input_format == Dicts.import_formats["IDRONAUT"]:
            ssp.read_input_file_by_format(filename, input_format)

        elif input_format == Dicts.import_formats["SAIV"]:
            ssp.read_input_file_by_format(filename, input_format)

        elif input_format == Dicts.import_formats["SEABIRD"]:
            ssp.read_input_file_by_format(filename, input_format)
            ssp.reduce_up_down(self.s.ssp_up_or_down)

        elif input_format == Dicts.import_formats["SIPPICAN"]:
            ssp.read_input_file_by_format(filename, input_format)

        elif input_format == Dicts.import_formats["TURO"]:
            ssp.read_input_file_by_format(filename, input_format)

        elif input_format == Dicts.import_formats["UNB"]:
            ssp.read_input_file_by_format(filename, input_format)

        elif input_format == Dicts.import_formats["VALEPORT_MIDAS"] \
                or input_format == Dicts.import_formats["VALEPORT_MONITOR"] \
                or input_format == Dicts.import_formats["VALEPORT_MINI_SVP"]:
            ssp.read_input_file_by_format(filename, input_format)
            ssp.reduce_up_down(self.s.ssp_up_or_down)

        else:
            raise SspError('unsupported import format: %s' % input_format)

        # checks
        if ssp.data.shape[1] == 0:
            raise SspError('load failure, no valid data samples found')
        self.ssp_data = ssp
        if (self.ssp_data.latitude is None) or (self.ssp_data.longitude is None):
            self.ssp_data.latitude, self.ssp_data.longitude = callback_pos()
            if (self.ssp_data.latitude is None) or (self.ssp_data.longitude is None):
                raise SspError("missing geographic location required for database lookup")
        if self.ssp_data.date_time is None:
            self.ssp_data.date_time = callback_date()
            if self.ssp_data.date_time is None:
                raise SspError("missing date required for database lookup.")

        self.filename = filename
        self.s.filename_prefix = filename_prefix
        self.filename_suffix = filename_suffix

        # calculating salinity and depth (it requires position)
        if (input_format == Dicts.import_formats["DIGIBAR_PRO"]) \
                or (input_format == Dicts.import_formats["DIGIBAR_S"]) \
                or (input_format == Dicts.import_formats["TURO"]):
            self.ssp_data.calc_salinity()

        elif input_format == Dicts.import_formats["SAIV"]:
            self.ssp_data.calc_depth()

        elif (input_format == Dicts.import_formats["VALEPORT_MIDAS"]) \
                or (input_format == Dicts.import_formats["VALEPORT_MONITOR"]) \
                or (input_format == Dicts.import_formats["VALEPORT_MINI_SVP"]):
            if self.ssp_data.source_info == "MIDAS SVP 6000" or self.ssp_data.source_info == "MONITOR SVP 500":
                self.ssp_data.calc_depth()
            self.ssp_data.calc_salinity()

        self.has_ssp_loaded = True
        log.info("resulting ssp:\n%s" % self.ssp_data)

        if self.woa09_atlas_loaded:
            self.ssp_woa, self.ssp_woa_min, self.ssp_woa_max = \
                self.woa09_atlas.query(self.ssp_data.latitude, self.ssp_data.longitude, self.ssp_data.date_time)
        else:
            self.ssp_woa = None
            self.ssp_woa_min = None
            self.ssp_woa_max = None

        self.surface_speed_applied = False
        self.ssp_applied_depth = 0

    def _monitor_sippican(self):
        if not self.sippican_listener.cast:
            # log.debug("not new SIPPICAN cast")
            return

        # Deal with the cast right away
        new_sv = self.sippican_listener.cast.convert_ssp()
        # Sippicans are always collected on Windows boxes and the filename
        # reported is a windows path name.
        self.filename = self.sippican_listener.cast.filename.split('\\')[-1]
        self.s.filename_prefix = os.path.splitext(self.filename)[0]

        self.has_sippican_to_process = True

        if self.server.is_running:
            self.server.stopped_on_error = True
            self.server.error_message = "Server stopped due to receipt of Sippican file over network."
            self.server_timer.Stop()
            self.server.on = False
            count = 0
            while self.server.is_running:
                self.status_message = "Waiting for server to stop...%d sec" % count
                time.sleep(1)
                count += 1

        self.ssp_data = new_sv
        if self.woa09_atlas_loaded:
            self.ssp_woa, self.ssp_woa_min, self.ssp_woa_max = self.woa09_atlas.query(self.ssp_data.latitude,
                                                                                      self.ssp_data.longitude,
                                                                                      self.ssp_data.date_time)
        else:
            self.ssp_woa = None

        self.has_ssp_loaded = True
        self.sippican_listener.cast = None

    def _monitor_mvp(self):

        if not self.mvp_listener.cast:
            # log.debug("not new MVP cast")
            return

        try:
            new_sv = self.mvp_listener.cast.convert_ssp()
            log.info("MBP @ new cast at date/time: %s" % new_sv.date_time)
        except SspError as e:
            log.info("MBP @ failure in parsing MVP cast, the expected format was %s > %s"
                     % (self.s.mvp_format, e))
            return

        if self.server.is_running:
            self.server.stopped_on_error = True
            self.server.error_message = "Server stopped due to receipt of MVP file over network."
            self.server_timer.Stop()
            self.server.on = False
            count = 0
            while self.server.is_running:
                self.status_message = "Waiting for server to stop...%d sec" % count
                time.sleep(1)
                count += 1

        self.s.filename_prefix = new_sv.date_time.strftime("%Y%m%d_%H%M%S_MVP")
        self.filename = self.s.filename_prefix + "." + self.s.mvp_format.lower()

        self.ssp_data = new_sv
        if self.woa09_atlas_loaded:
            self.ssp_woa, self.ssp_woa_min, self.ssp_woa_max = self.woa09_atlas.query(self.ssp_data.latitude,
                                                                                      self.ssp_data.longitude,
                                                                                      self.ssp_data.date_time)
        else:
            self.ssp_woa = None

        self.has_mvp_to_process = True
        self.has_ssp_loaded = True
        self.mvp_listener.cast = None

    def _monitor_mvp_sensors(self):
        log.info("MVS @ date: %s" % self.mvp_controller.get_date())
        log.info("MVS @ fish: %s" % self.mvp_controller.get_fish())
        log.info("MVS @ nav: %s" % self.mvp_controller.get_nav())

    def release(self):
        if not self.with_listeners:
            return

        if self.server.is_running:
            log.info("Stopping SIS server")
            self.server.stop()

        self.stop_listeners()

        if self.sippican_timer:
            if self.sippican_timer.is_alive():
                self.sippican_timer.stop()

        if self.mvp_timer:
            if self.mvp_timer.is_alive():
                self.mvp_timer.stop()

        if self.mvp_sensors_timer:
            if self.mvp_sensors_timer.is_alive():
                self.mvp_sensors_timer.stop()

        # close logging and disconnect
        if self.s.log_processing_metadata:
            log.info("END logging of processing metadata")
        if self.s.log_server_metadata:
            log.info("END logging of server metadata")
        # TODO disconnect sqlite handler
        # self.log_db.disconnect()

    def stop_listeners(self):
        log.info("Stop listeners")
        self.km_listener.stop_listen()
        self.sippican_listener.stop_listen()
        self.mvp_listener.stop_listen()
        # self.mvp_controller.stop_listen()

    def has_running_listeners(self):
        """ Check if all listeners are running """
        if not self.with_listeners:
            return False
        running_flag = self.sippican_listener.listening and self.km_listener.listening and self.mvp_listener.listening
        return running_flag

    def load_woa09_atlas(self):
        """ Load the WOA grid """
        try:
            self.woa09_atlas.load_grids(self.s.woa_path)

        except SspError:
            self.woa09_atlas_loaded = False

        self.woa09_atlas_loaded = True

    def load_rtofs_atlas(self):
        """ Load the RTOFS grid """
        try:
            self.rtofs_atlas.load_grids(dt.datetime.utcnow())

        except SspError:
            return False

        self.rtofs_atlas_loaded = True
        return True

    def send_cast(self, client, kng_fmt):
        log.info("Transmitting cast to %s (port: %d)" % (client.IP, client.port))

        if client.protocol == "SIS":
            self.km_listener.ssp = None

        log.info("Sending to %s %s [format %s, protocol %s]" % (client.IP, client.port, kng_fmt, client.protocol))
        client.send_cast(self.ssp_data, kng_fmt)
        log.info("Just sent:\n%s" % self.ssp_data.tx_data)

        if client.protocol != "SIS":
            log.info("Transmitted cast, protocol does not allow verification")
            time.sleep(5)
            return True

        log.info("waiting for receipt confirmation...")
        # Give SIS some time to catch it and re-transmit it
        wait = 0
        while (not self.km_listener.ssp) and (wait < self.s.rx_max_wait_time):
            time.sleep(1)
            log.info("waiting %s s ..." % wait)
            wait += 1

        # Split up the profile that was sent into depth/speed pairs
        count = 0
        speeds = None
        depths = None
        for line in self.ssp_data.tx_data.splitlines():

            if count == 0:
                num_points = int(line.split(",")[2])
                speeds = np.zeros(num_points)
                depths = np.zeros(num_points)
                speeds[count] = float(line.split(",")[-4])
                depths[count] = float(line.split(",")[-5])

            elif count < num_points:
                speeds[count] = float(line.split(",")[-4])
                depths[count] = float(line.split(",")[-5])

            count += 1

            if count == num_points:
                break

        if self.km_listener.ssp:
            # The KM SVP datagrams have a bug in their time reporting and have a 100 second granularity
            # so can't compare times to ensure it's the same profile.  Comparing the sound speeds instead
            speeds_received = np.interp(depths, self.km_listener.ssp.depth, self.km_listener.ssp.speed)
            max_diff = max(abs(speeds - speeds_received))
            log.info("Casts differ by %.1f m/s" % max_diff)

            if max_diff < 0.2:
                self.server.last_sent_ssp_time = self.km_listener.ssp.acquisition_time
                return True

            else:
                log.info("Reception not confirmed > Too big delta")
                return False
        else:
            log.info("Reception not confirmed > Unable to catch the back datagram")
            return False

    def formats_export(self, mode):
        log.info("export mode: %s" % mode)

        export_directory = None
        if mode == "USER":
            export_directory = self.s.user_export_directory
        elif mode == "SERVER":
            export_directory = os.path.join(self.get_output_folder(), "server")
            if not os.path.exists(export_directory):
                os.makedirs(export_directory)
        filename_prefix = self.s.filename_prefix

        num_exported = 0
        for fmt in self.s.export_formats.keys():
            if self.s.export_formats[fmt]:
                self._format_export(export_directory, filename_prefix, fmt, mode)
                num_exported += 1

        if num_exported:
            log.info("exported %s files" % num_exported)

    def _format_export(self, export_directory, filename_prefix, ssp_format, mode):
        # TODO: check the various configuration outputs
        extension = Dicts.export_extensions[ssp_format]
        ssp_output = os.path.basename(filename_prefix)
        ssp_output = os.path.join(export_directory, (ssp_output + "." + extension))

        append_caris_file = False
        if mode == "USER":
            append_caris_file = self.s.user_append_caris_file
        elif mode == "SERVER":
            append_caris_file = self.s.server_append_caris_file

        log.info("output filename: %s" % ssp_output)

        data = self.ssp_data.convert(ssp_format)
        if not data:
            if mode == "USER":
                raise SspError("failed on export for format %s" % ssp_format)
            return

        if ssp_format == "HIPS" and os.path.isfile(ssp_output) and append_caris_file:
            # Appending to an existing HIPS file needs to skip the first two lines in the data output
            outfile = open(ssp_output, 'a')
            count = 0
            for line in data.splitlines():
                if count > 1:
                    outfile.write(line + "\n")
                count += 1
        else:
            outfile = open(ssp_output, 'w')
            outfile.write(data)
        outfile.close()

    def clean_project(self):
        self.has_ssp_loaded = False
        self.filename = ""
        self.s.filename_prefix = ""

    def count_export_formats(self):
        """ helper function to count the number of formats in export """
        num_formats_to_export = 0
        for fmt in self.s.export_formats.keys():
            if self.s.export_formats[fmt]:
                num_formats_to_export += 1
        return num_formats_to_export

    def activate_logging_on_db(self):
        self.s.log_processing_metadata = True
        logging.getLogger().addHandler(self.log_sh)
        log.info("START logging of processing metadata")

    def deactivate_logging_on_db(self):
        self.s.log_processing_metadata = False
        log.info("END logging of processing metadata")
        logging.getLogger().removeHandler(self.log_sh)

    def activate_server_logging_on_db(self):
        self.s.log_server_metadata = True
        logging.getLogger().addHandler(self.log_server_sh)
        log.info("START logging of server metadata")

    def deactivate_server_logging_on_db(self):
        self.s.log_server_metadata = False
        log.info("END logging of server metadata")
        logging.getLogger().removeHandler(self.log_server_sh)

    # ########### SIS ##############

    def get_cast_from_sis(self):
        """ Retrieve a cast from SIS """
        self.km_listener.ssp = None

        log.info("requesting IUR to: %s" % self.ssp_recipient_ip)
        self.km_listener.request_iur(self.ssp_recipient_ip)

        # Give SIS some time to transmit it
        wait = 0
        log.info("waiting ...")
        # This can require time when running on K-Sync with all the sounders waiting in the queue to fire in turn.
        max_wait = 60
        while (not self.km_listener.ssp) and (wait < max_wait):
            log.info("... %s seconds" % wait)
            time.sleep(2)
            wait += 2
        log.info("waited for %s seconds" % wait)
        log.info("got a cast:\n\t%s" % self.km_listener.ssp)
