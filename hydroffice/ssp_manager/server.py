from __future__ import absolute_import, division, print_function, unicode_literals

import time
import os

import logging

log = logging.getLogger(__name__)

from .ssp_dicts import Dicts
from .helper import SspError


class Server(object):
    def __init__(self, prj):
        self.prj = prj

        self._ref_monitor = None

        self.is_running = False
        self.on = False
        self.stopped_on_error = False
        self.error_message = ""
        self.delivered_casts = 0
        self.force_send = False
        self.update_plot = False
        self.wait_time = 10

        self.last_sent_ssp_time = None

        self.server_vessel_draft = 0.0

    def set_refraction_monitor(self, ref_mon):
        pause_func = getattr(ref_mon, "pause_corrections", None)
        resume_func = getattr(ref_mon, "resume_corrections", None)
        set_corrector_func = getattr(ref_mon, "set_corrector", None)
        get_corrector_func = getattr(ref_mon, "get_corrector", None)
        set_ssp_func = getattr(ref_mon, "set_ssp", None)
        get_mean_depth = getattr(ref_mon, "get_mean_depth", None)

        if not callable(pause_func) or not callable(resume_func) \
                or not callable(get_corrector_func) or not callable(set_corrector_func)\
                or not callable(set_ssp_func) or not callable(get_mean_depth):
            log.warning("Passed invalid Refraction Monitor object")
            return

        log.info("Passed valid Refraction Monitor object")
        self._ref_monitor = ref_mon

    def check_settings(self):
        """Check the server settings"""

        if self.prj.s.sis_server_source == Dicts.sis_server_sources['RTOFS']:  # RTOFS case
            if self.prj.rtofs_atlas_loaded:
                log.info("RTOFS check: OK")
            else:
                log.warning("RTOFS check: KO > Attempting to use WOA09")
                self.prj.s.sis_server_source = Dicts.sis_server_sources['WOA09']

        if self.prj.s.sis_server_source == Dicts.sis_server_sources['WOA09']:  # WOA09 case (or missing RTOFS case)
            if self.prj.woa09_atlas_loaded:
                log.info("WOA09 check: OK")
            else:
                log.error("WOA09 check: KO > The Server Mode is not available")
                return False

        # Check for Kongsberg navigation datagram
        if self.prj.km_listener.nav:
            log.info("SIS NAV broadcast: OK")
        else:
            log.error("SIS NAV broadcast: KO > The Server Mode not available")
            return False

        # Check for Kongsberg depth datagram
        if self.prj.km_listener.xyz88:
            log.info("SIS DEPTH broadcast: OK")
        else:
            log.warning("SIS DEPTH broadcast: KO > SIS may warn about surface sound speed")

        # Test clients interaction
        log.info("Testing clients for reception-confirmation interaction")
        num_live_clients = 0
        for client in range(self.prj.s.client_list.num_clients):

            if self.prj.s.client_list.clients[client].protocol != "SIS":
                self.prj.s.client_list.clients[client].alive = False
                continue

            log.info("Testing client %s" % self.prj.s.client_list.clients[client].IP)
            self.prj.ssp_recipient_ip = self.prj.s.client_list.clients[client].IP

            self.prj.get_cast_from_sis()
            if self.prj.km_listener.ssp:
                log.info("Interaction test: OK")
                self.prj.s.client_list.clients[client].alive = True
                num_live_clients += 1
            else:
                log.warning("Interaction test: KO")
                self.prj.s.client_list.clients[client].alive = False
        if num_live_clients == 0:
            log.error("Unable to confirm interaction with any clients > The Server Mode is not available")
            return False
        else:
            log.info("Interaction verified with %s client/clients" % num_live_clients)

        # test vessel draft
        if self.prj.vessel_draft is None:
            log.info("Vessel draft: %s (server)" % self.server_vessel_draft)
        else:
            log.error("Vessel draft: %s" % self.prj.vessel_draft)

        # test auto-export function
        if self.prj.s.auto_export_on_server_send:
            log.info("Server auto-export: True")

            if self.prj.count_export_formats() == 0:
                log.warning("Server auto-export > No export formats are selected")
        else:
            log.info("Server auto-export: False")

        # reset server flags
        self.update_plot = False
        self.force_send = False
        self.delivered_casts = 0

        return True

    def run(self):
        self.is_running = True
        self.on = True
        self.prj.time_of_last_tx = None
        self.stopped_on_error = False

        last_lat = 999
        last_lon = 999
        last_surface_sound_speed = 0

        while self.on:
            # retrieve spatial timestamp
            latitude = self.prj.km_listener.nav.latitude
            longitude = self.prj.km_listener.nav.longitude
            nav_time = self.prj.km_listener.nav.dg_time
            if (latitude is None) or (longitude is None) or (nav_time is None):
                log.warning("Possible corrupted reception of spatial timestamp > Waiting %s secs"
                            % self.wait_time)
                count = 0
                while self.on and (count < self.wait_time):
                    time.sleep(1)
                    count += 1
                continue

            # retrieve atlas grid position
            if self.prj.s.sis_server_source == Dicts.sis_server_sources['WOA09']:
                lat_grid, lon_grid = self.prj.woa09_atlas.grid_coords(latitude, longitude)
            elif self.prj.s.sis_server_source == Dicts.sis_server_sources['RTOFS']:
                try:
                    lat_grid, lon_grid = self.prj.rtofs_atlas.grid_coords(latitude, longitude)
                except SspError:
                    lat_grid, lon_grid = self.prj.woa09_atlas.grid_coords(latitude, longitude)

            if self.prj.s.server_apply_surface_sound_speed and (self.prj.km_listener.xyz88 is not None):
                surface_sound_speed = self.prj.km_listener.xyz88.sound_speed
                log.info("Using Surface Sound Speed: True > %s" % surface_sound_speed)
                if last_surface_sound_speed:
                    ssp_diff = abs(surface_sound_speed - last_surface_sound_speed)
                else:
                    ssp_diff = 0.0
            else:
                log.info("Using Surface Sound Speed: False")
                surface_sound_speed = None
                ssp_diff = 0.0
            log.info("Surface Sound Speed delta: %.1f" % ssp_diff)

            # sleep and continue the loop (if the position is the same and the ssp diff is tolerable)
            if (last_lat == lat_grid) and (last_lon == lon_grid) and (ssp_diff < 1.0) and (not self.force_send):
                count = 0
                log.info("Wait %s secs before continuing the loop" % self.wait_time)
                while self.on and count < self.wait_time:
                    time.sleep(1)
                    count += 1
                continue

            # send a new cast
            self.force_send = False
            log.info("Sending a new cast")

            # We always do a WOA09 query
            self.prj.ssp_woa, self.prj.ssp_woa_min, self.prj.ssp_woa_max = \
                self.prj.woa09_atlas.query(latitude, longitude, nav_time)

            # Search for synthetic casts
            if self.prj.s.sis_server_source == Dicts.sis_server_sources['WOA09']:
                self.prj.ssp_data, self.prj.ssp_woa_min, self.prj.ssp_woa_max = \
                    self.prj.woa09_atlas.query(latitude, longitude, nav_time)

            elif self.prj.s.sis_server_source == Dicts.sis_server_sources['RTOFS']:
                try:
                    self.prj.ssp_data = self.prj.rtofs_atlas.query(latitude, longitude, nav_time)

                    # We extend RTOFS profiles with WOA09 profiles since they look much farther
                    if self.prj.ssp_woa:
                        self.prj.ssp_data.extend(self.prj.ssp_woa, Dicts.source_types['Woa09Extend'])

                except SspError:
                    log.error("Failed on RTOFS lookup? Reverting to WOA09")
                    self.prj.ssp_data, self.prj.ssp_woa_min, self.prj.ssp_woa_max = \
                        self.prj.woa09_atlas.query(latitude, longitude, nav_time)

            if not self.prj.ssp_data:
                log.warning("Unable to retrieve a synthetic cast > Continue the loop")
                continue

            # Apply the refraction corrector if one is available
            if self._ref_monitor:
                self._ref_monitor.pause_corrections()

                corrector = self._ref_monitor.get_corrector()
                depth = self._ref_monitor.get_mean_depth()

                if corrector != 0.0:
                    self.prj.ssp_data.data[Dicts.idx['speed'], :] = \
                        self.prj.ssp_data.data[Dicts.idx['speed'], :] + corrector
                    self._ref_monitor.set_corrector(0)
                    log.info("Applied corrector: %s (depth: %s)" % (corrector, depth))

            # Apply the surface sound speed
            if self.prj.s.server_apply_surface_sound_speed and surface_sound_speed:
                if self.prj.vessel_draft is None:
                    self.prj.ssp_applied_depth = 1.15 * self.server_vessel_draft
                else:
                    self.prj.ssp_applied_depth = 1.15 * self.prj.vessel_draft
                self.prj.ssp_data.insert_sample(depth=self.prj.ssp_applied_depth, speed=surface_sound_speed,
                                                temperature=None, salinity=None,
                                                source=Dicts.source_types['SurfaceSensor'])
                idx = self.prj.ssp_data.data[Dicts.idx['depth'], :] < self.prj.ssp_applied_depth
                self.prj.ssp_data.data[Dicts.idx['speed'], idx] = surface_sound_speed
                self.prj.surface_speed_applied = True
                log.info("Surface Sound Speed applied: True")
            else:
                self.prj.surface_speed_applied = False
                log.info("Surface Sound Speed applied: False")

            # after the first tx, a cast from SIS is always required
            num_live_clients = 0
            if self.prj.server.last_sent_ssp_time:
                log.info("Requesting cast from SIS (prior to transmission)")

                for client in range(self.prj.s.client_list.num_clients):

                    # skipping dead clients
                    if not self.prj.s.client_list.clients[client].alive:
                        log.info("Dead client: %s > Skipping"
                                 % self.prj.s.client_list.clients[client].IP)
                        continue

                    # actually requiring the SSP
                    self.prj.ssp_recipient_ip = self.prj.s.client_list.clients[client].IP
                    log.info("Testing client: %s" % self.prj.ssp_recipient_ip)
                    self.prj.get_cast_from_sis()
                    log.info("Tested client and got %s" % self.prj.km_listener.ssp)
                    if not self.prj.km_listener.ssp:
                        log.info("Client went dead since last transmission %s" % self.prj.ssp_recipient_ip)
                        self.prj.s.client_list.clients[client].alive = False
                        continue

                    # test by comparing the times
                    if self.last_sent_ssp_time != self.prj.km_listener.ssp.acquisition_time:
                        log.warning("Times mismatch > %s != %s"
                                    % (self.prj.time_of_last_tx, self.last_sent_ssp_time))
                        self.stopped_on_error = True
                        self.prj.server.error_message = "Times mismatch > Another agent uploaded SSP on SIS"
                        log.error(self.prj.server.error_message)
                        self.prj.s.client_list.clients[client].alive = False
                        continue

                    log.info("Live client")

                    num_live_clients += 1

                if num_live_clients == 0:
                    self.stopped_on_error = True
                    self.prj.server.error_message = "No more live clients"
                    log.error("Found no live clients during pre-transmission test")
                    continue

            # We use the "S01" format for Server mode, so that the TX SSP is applied immediately.
            kng_fmt = Dicts.kng_formats["S01"]
            # Tx only to live clients
            num_live_clients = 0
            for client in range(self.prj.s.client_list.num_clients):
                if not self.prj.s.client_list.clients[client].alive:
                    log.warning("Dead client: %s > Skipping"
                                % self.prj.s.client_list.clients[client].IP)
                    continue
                self.prj.ssp_recipient_ip = self.prj.s.client_list.clients[client].IP
                log.info("Live client: %s > Transmitting" % self.prj.ssp_recipient_ip)
                success = self.prj.send_cast(self.prj.s.client_list.clients[client], kng_fmt)

                if not success:
                    self.prj.s.client_list.clients[client].alive = False
                    self.prj.server.error_message = "Unable to confirm SSP reception"
                    log.error(self.prj.server.error_message)

                else:
                    num_live_clients += 1

            if num_live_clients == 0:
                self.stopped_on_error = True
                self.prj.server.error_message = "No Tx to live clients"
                log.error(self.prj.server.error_message)
                continue
            log.info("Total Tx to live clients: %s" % num_live_clients)

            if self.prj.ssp_data.tx_data:
                log.info("Transmitted:\n" + self.prj.ssp_data.tx_data)

            # store for the next Tx
            last_lat = lat_grid
            last_lon = lon_grid
            if surface_sound_speed:
                last_surface_sound_speed = surface_sound_speed
            self.prj.time_of_last_tx = nav_time
            log.info("Delivered SSP with spatial time stamp: %s @ %f %f"
                     % (self.prj.time_of_last_tx, latitude, longitude))
            self.delivered_casts += 1

            # update filename based on the used atlas
            if self.prj.s.sis_server_source == Dicts.sis_server_sources['WOA09']:
                self.prj.filename = "%s_WOA09" % (self.prj.ssp_data.date_time.strftime("%Y%m%d_%H%M%S"))
            elif self.prj.s.sis_server_source == Dicts.sis_server_sources['RTOFS']:
                self.prj.filename = "%s_RTOFS" % (self.prj.ssp_data.date_time.strftime("%Y%m%d_%H%M%S"))
            self.prj.s.filename_prefix = os.path.splitext(self.prj.filename)[0]

            self.prj.has_ssp_loaded = True
            self.update_plot = True

            if self.prj.s.auto_export_on_server_send:
                log.info("Exporting on server send")
                self.prj.formats_export("SERVER")

            if self._ref_monitor:
                self._ref_monitor.set_ssp(self.prj.ssp_data)
                self._ref_monitor.resume_corrections()

            # Sleep to slow down the loop
            count = 0
            while self.on and count < self.wait_time:
                time.sleep(1)
                count += 1

        self.is_running = False
        log.info("Stopped")

    def stop(self, by_thread=False):
        """Actually send the stop command to the thread, waiting for it"""
        self.prj.server_timer.stop()
        self.on = False
        if by_thread:
            log.info("Waiting the thread to stop")
        else:
            log.info("Waiting the thread to stop")
        count = 0
        while self.prj.server.is_running and (count < 30):
            if by_thread:
                log.info("Waiting for server to stop...%d sec" % count)
            else:
                log.info("Waiting for server to stop...%d sec" % count)
            time.sleep(1)
            count += 1

        if count == 30:
            if by_thread:
                log.info("Unable to properly stop the Server Mode")
            else:
                log.info("Unable to properly stop the Server Mode")
        else:
            if by_thread:
                log.info("Server Mode stopped")
            else:
                log.info("Server Mode stopped")

        self.prj.clean_project()
