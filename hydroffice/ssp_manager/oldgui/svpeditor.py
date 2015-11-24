from __future__ import absolute_import, division, print_function, unicode_literals

import os
import math
import socket
import datetime as dt
import threading
import time
import copy

import numpy as np
import matplotlib.patches
from matplotlib import rcParams
rcParams.update(
    {
        'font.family': 'sans-serif',
        'font.size': 7
    }
)
import wx
from wx import PyDeadObjectError
from . import wxmpl  # local version of this module, since Pydro's one has an issue

import logging

log = logging.getLogger(__name__)

from hydroffice.base.helper import HyOError
from hydroffice.base.timerthread import TimerThread
from hydroffice.base.gdal_aux import GdalAux

from .plots import WxPlots, PlotsSettings
from . import svpeditor_ui
from . import refmonitor
from . import geomonitor
from . import settingsviewer
from .. import __version__
from .. import __license__
from .. import project
from .. import oceanography
from ..ssp_db import SspDb
from ..ssp_dicts import Dicts
from ..ssp_collection import SspCollection
from ..helper import Helper, SspError
from ..atlases.woa09checker import Woa09Checker


class SVPEditor(svpeditor_ui.SVPEditorBase):
    here = os.path.abspath(os.path.dirname(__file__))

    gui_state = {
        "OPEN": 0,
        "CLOSED": 1,
        "SERVER": 2
    }

    def __init__(self):
        svpeditor_ui.SVPEditorBase.__init__(self, None, -1, "")

        self.version = __version__
        self.license = __license__

        # take care of WOA09 atlas
        if not Woa09Checker.is_present():
            dial = wx.MessageDialog(None, 'The WOA09 atlas (used by some advanced SSP functions)\n'
                                          'was not found!\n\n'
                                          'The required data files (~350MB) can be retrieved by\n'
                                          'downloading this archive:\n'
                                          '   ftp.ccom.unh.edu/fromccom/hydroffice/woa09.zip\n'
                                          'and unzipping it into:\n'
                                          '   %s\n\n'
                                          'Do you want that I perform this operation for you?\n'
                                          'Internet connection is required!\n'
                                    % Woa09Checker.get_atlases_folder(),
                                    'SSP Manager - WOA09 atlas', wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
            if dial.ShowModal() == wx.ID_YES:
                chk = Woa09Checker(verbose=True)
                with_woa09 = chk.present
                if not with_woa09:
                    wx.MessageDialog(None, 'Unable to retrieve the WOA09 atlas. You might:\n'
                                           ' - download the archive from (anonymous ftp):\n'
                                           '   ftp.ccom.unh.edu/fromccom/hydroffice/woa09.zip\n'
                                           ' - unzip the archive into:\n'
                                           '   %s\n'
                                           ' - restart SSP Manager\n'
                                     % Woa09Checker.get_atlases_folder(),
                                     'WOA09 atlas', wx.OK | wx.ICON_QUESTION)
                    log.info("disabling WOA09 functions")
            else:
                log.info("disabling WOA09 functions")
                with_woa09 = False
        else:
            with_woa09 = True

        # We load WOA09 atlas and attempt the RTOFS atlas (since it requires internet connection)
        self.prj = project.Project(with_listeners=True, with_woa09=with_woa09, with_rtofs=True)

        # check listeners
        if not self.prj.has_running_listeners():
            msg = 'Kongsberg and/or Sippican and/or MVP network I/O cannot bind to ports.\n' \
                  'Is there another instance of SSP Manager running already?'
            dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

        # check woa09 atlas
        if not self.prj.woa09_atlas_loaded:
            msg = 'Error: failed on World Ocean Atlas grid file load'
            dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

        # check rtofs atlas
        if not self.prj.rtofs_atlas_loaded:
            msg = 'Warning: failure in RTOFS atlas loading (internet connectivity required).\n' \
                  'RTOFS queries disabled.'
            dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

        self.status_message = ""

        # UI
        self.p = PlotsSettings()
        self.ref_monitor = None
        self.geo_monitor = None
        self.set_viewer = None
        self.init_ui()

        # update state
        self.state = None
        self._update_state(self.gui_state["CLOSED"])

        # GUI timers (status bar and plots)
        self.status_timer = TimerThread(self._update_status, timing=3)
        self.status_timer.start()
        self.plot_timer = TimerThread(self._update_plot, timing=3)
        self.plot_timer.start()

    def init_ui(self):
        favicon = wx.Icon(os.path.join(self.here, 'favicon.ico'), wx.BITMAP_TYPE_ICO, 32, 32)
        wx.Frame.SetIcon(self, favicon)

        if os.name == 'nt':
            # This is needed to display the app icon on the taskbar on Windows 7
            import ctypes

            app_id = 'SSP Manager v.%s' % self.version
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

        self.Bind(wx.EVT_CLOSE, self.on_file_exit)

        # add plots panel
        self.p.plots = WxPlots(self)
        self.p.plots.callback_right_click_down = self.on_context

        # expand the panel to fit the whole app
        self.GetSizer().Add(self.p.plots, 1, wx.EXPAND)
        self.GetSizer().Fit(self)
        self.Layout()

        # register to receive wxPython SelectionEvents from a PlotPanel or PlotFrame
        wxmpl.EVT_SELECTION(self, self.p.plots.GetId(), self._on_area_selected)
        wxmpl.EVT_POINT(self, self.p.plots.GetId(), self._on_point_selected)

        # Other graphical panels are instantiated and are only shown when requested
        self.ref_monitor = refmonitor.RefMonitor(self.prj.km_listener)
        self.geo_monitor = geomonitor.GeoMonitor(self.prj.km_listener)
        self.set_viewer = settingsviewer.SettingsViewer(self.prj.s)

    def on_context(self, event):
        """
        Create and show a Context Menu
        """
        # we don't want the context menu without data
        if not self.prj.has_ssp_loaded:
            return

        id_ctx_reset_view = None
        id_ctx_zoom = None
        id_ctx_flag = None
        id_ctx_unflag = None
        id_ctx_insert = None
        # only do this part the first time so the events are only bound once
        if not hasattr(self, "id_ctx_reset_view"):
            id_ctx_reset_view = wx.NewId()
            self.Bind(wx.EVT_MENU, self.on_reset_view, id=id_ctx_reset_view)
            id_ctx_zoom = wx.NewId()
            self.Bind(wx.EVT_MENU, self.on_popup, id=id_ctx_zoom)
            id_ctx_flag = wx.NewId()
            self.Bind(wx.EVT_MENU, self.on_popup, id=id_ctx_flag)
            id_ctx_unflag = wx.NewId()
            self.Bind(wx.EVT_MENU, self.on_popup, id=id_ctx_unflag)
            id_ctx_insert = wx.NewId()
            self.Bind(wx.EVT_MENU, self.on_popup, id=id_ctx_insert)

        # build the menu
        context_menu = wx.Menu()
        context_menu.Append(id_ctx_reset_view, "Reset view")
        context_menu.AppendSeparator()
        item_zoom = context_menu.Append(id_ctx_zoom, "Zoom",
                                        "Zoom on plot by mouse selection", wx.ITEM_RADIO)
        if self.PlotZoom.IsChecked():
            item_zoom.Check(True)
        item_flag = context_menu.Append(id_ctx_flag, "Flag",
                                        "Flag samples on plot by mouse selection", wx.ITEM_RADIO)
        if self.PlotFlag.IsChecked():
            item_flag.Check(True)
        item_unflag = context_menu.Append(id_ctx_unflag, "Unflag",
                                          "Unflag samples on plot by mouse selection", wx.ITEM_RADIO)
        if self.PlotUnflag.IsChecked():
            item_unflag.Check(True)
        item_insert = context_menu.Append(id_ctx_insert, "Insert",
                                          "Insert a sample by mouse clicking", wx.ITEM_RADIO)
        if self.PlotInsert.IsChecked():
            item_insert.Check(True)

        # show the popup menu
        self.PopupMenu(context_menu)
        context_menu.Destroy()

        event.Skip()

    def on_popup(self, event):
        """
        Print the label of the menu item selected
        """
        item_id = event.GetId()
        menu = event.GetEventObject()
        menu_item = menu.FindItemById(item_id)

        if menu_item.GetLabel() == "Zoom":
            event = wx.MenuEvent(wx.wxEVT_COMMAND_MENU_SELECTED, self.PlotZoom.GetId(), self.ProcessInspection)
            wx.PostEvent(self, event)
            self.PlotZoom.Check(True)
        elif menu_item.GetLabel() == "Flag":
            event = wx.MenuEvent(wx.wxEVT_COMMAND_MENU_SELECTED, self.PlotFlag.GetId(), self.ProcessInspection)
            wx.PostEvent(self, event)
            self.PlotFlag.Check(True)
        elif menu_item.GetLabel() == "Unflag":
            event = wx.MenuEvent(wx.wxEVT_COMMAND_MENU_SELECTED, self.PlotUnflag.GetId(), self.ProcessInspection)
            wx.PostEvent(self, event)
            self.PlotUnflag.Check(True)
        elif menu_item.GetLabel() == "Insert":
            event = wx.MenuEvent(wx.wxEVT_COMMAND_MENU_SELECTED, self.PlotInsert.GetId(), self.ProcessInspection)
            wx.PostEvent(self, event)
            self.PlotInsert.Check(True)

    # ####### FILE ########

    # Import

    def on_file_import_castaway(self, evt):
        self._open_data_file(Dicts.import_formats['CASTAWAY'])

    def on_file_import_saiv(self, evt):
        self._open_data_file(Dicts.import_formats['SAIV'])

    def on_file_import_idronaut(self, evt):
        self._open_data_file(Dicts.import_formats['IDRONAUT'])

    def on_file_import_digibar_pro(self, evt):
        self._open_data_file(Dicts.import_formats['DIGIBAR_PRO'])

    def on_file_import_digibar_s(self, evt):
        self._open_data_file(Dicts.import_formats['DIGIBAR_S'])

    def on_file_import_sippican(self, evt):
        self._open_data_file(Dicts.import_formats['SIPPICAN'])

    def on_file_import_seabird(self, evt):
        self._open_data_file(Dicts.import_formats['SEABIRD'])

    def on_file_import_turo(self, evt):
        self._open_data_file(Dicts.import_formats['TURO'])

    def on_file_import_unb(self, evt):
        self._open_data_file(Dicts.import_formats['UNB'])

    def on_file_import_valeport_midas(self, evt):
        self._open_data_file(Dicts.import_formats['VALEPORT_MIDAS'])

    def on_file_import_valeport_monitor(self, evt):
        self._open_data_file(Dicts.import_formats['VALEPORT_MONITOR'])

    def on_file_import_valeport_minisvp(self, evt):
        self._open_data_file(Dicts.import_formats['VALEPORT_MINI_SVP'])

    def _open_data_file(self, input_format):

        if not (input_format in Dicts.import_formats.values()):
            raise SspError("unsupported import format: %s" % input_format)

        if self.prj.has_ssp_loaded:
            self.prj.clean_project()
            self.clear_app()

        try:
            ext = Dicts.import_extensions[input_format]
        except KeyError:
            raise SspError("unsupported import extension format: %s" % input_format)

        # retrieve the name of the format
        name_format = [key for key, value in Dicts.import_formats.items() if value == input_format][0]
        selection_filter = "%s files (*.%s,*.%s)|*.%s;*.%s|All File (*.*)|*.*" \
                           % (name_format, ext, ext.upper(), ext, ext.upper())
        dlg = wx.FileDialog(self, "File selection", "", "", selection_filter, style=wx.FD_OPEN | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        import_directory = dlg.GetDirectory()
        import_file = dlg.GetFilename()
        dlg.Destroy()
        filename = os.path.join(import_directory, import_file)

        try:
            self.prj.open_file_format(filename, input_format, self.get_date, self.get_position)
        except SspError as e:
            dlg = wx.MessageDialog(None, e.message, "Error", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()  # Show it
            dlg.Destroy()
            return

        # set the new SSP for the refraction monitor
        if self.ref_monitor:
            self.ref_monitor.set_ssp(self.prj.ssp_data)
            self.ref_monitor.set_corrector(0)

        self._update_state(self.gui_state['OPEN'])
        self._update_plot()
        self.status_message = "Loaded %s" % self.prj.filename

    # Query

    def on_file_query_woa09(self, evt):
        if not self.prj.woa09_atlas_loaded:
            msg = "Functionality disabled: Failed on WOA2009 grid load"
            dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        if self.prj.has_ssp_loaded:
            self.prj.clean_project()
            self.clear_app()

        msg = "User requested WOA09 synthetic cast"
        log.info(msg)

        latitude, longitude = self.get_position()
        if (latitude is None) or (longitude is None):
            log.info("not a valid position")
            return
        log.info("using position: %s, %s" % (longitude, latitude))

        query_date = self.get_date()
        if query_date is None:
            log.info("not a valid date time")
            return
        log.info("using date time: %s" % query_date)

        try:
            woa_data, woa_min, woa_max = self.prj.woa09_atlas.query(latitude, longitude, query_date)
            if woa_data is None:
                log.info("unable to retrieve data")
                return

        except SspError:
            msg = "Failed on WOA09 lookup"
            dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        log.info("got WOA SSP:\n%s" % woa_data)
        self.prj.ssp_woa = woa_data
        self.prj.ssp_woa_min = woa_min
        self.prj.ssp_woa_max = woa_max
        self.prj.ssp_data = copy.deepcopy(woa_data)

        self.prj.filename = "%s_WOA09" % (self.prj.ssp_woa.date_time.strftime("%Y%m%d_%H%M%S"))
        self.prj.s.filename_prefix = os.path.splitext(self.prj.filename)[0]
        self.prj.has_ssp_loaded = True
        self.prj.surface_speed_applied = False
        self.prj.ssp_applied_depth = 0

        self._update_plot()
        self._update_state(self.gui_state['OPEN'])

        self.status_message = "Synthetic WOA09 cast"
        log.info("Synthetic WOA09 cast using pos: (%.6f, %.6f) and time: %s"
                        % (latitude, longitude, query_date))

    def on_file_query_rtofs(self, evt):
        if not self.prj.rtofs_atlas_loaded:
            msg = "Functionality disabled: Failed on RTOFS grid load"
            dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        if self.prj.has_ssp_loaded:
            self.prj.clean_project()
            self.clear_app()

        msg = "User requested RTOFS synthetic cast"
        log.info(msg)

        latitude, longitude = self.get_position()
        if (latitude is None) or (longitude is None):
            log.info("not a valid position")
            return
        log.info("using position: %s, %s" % (longitude, latitude))

        query_date = self.get_date()
        if query_date is None:
            log.info("not a valid date time")
            return
        log.info("using date time: %s" % query_date)

        try:
            temp_ssp = self.prj.rtofs_atlas.query(latitude, longitude, query_date)
            if temp_ssp is None:
                log.info("empty result from RTOFS query")
                return

        except SspError:
            msg = "Failed on RTOFS lookup"
            dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        self.prj.ssp_data = temp_ssp

        try:
            self.prj.ssp_woa, self.prj.ssp_woa_min, self.prj.ssp_woa_max = self.prj.woa09_atlas.query(latitude,
                                                                                                      longitude,
                                                                                                      query_date)
            if self.prj.ssp_woa is None:
                log.info("failure in performing WOA09 lookup")

        except HyOError:
            log.info("failure in performing WOA09 lookup")

        self.prj.filename = "%s_RTOFS" % (self.prj.ssp_data.date_time.strftime("%Y%m%d_%H%M%S"))
        self.prj.s.filename_prefix = os.path.splitext(self.prj.filename)[0]
        self.prj.has_ssp_loaded = True
        self.prj.surface_speed_applied = False
        self.prj.ssp_applied_depth = 0

        self._update_plot()
        self._update_state(self.gui_state['OPEN'])

        self.status_message = "Synthetic RTOFS cast"
        log.info("Synthetic RTOFS cast using pos: (%.6f, %.6f) and time: %s"
                        % (latitude, longitude, query_date))

    def on_file_query_sis(self, evt):
        log.info("requesting profile from SIS")

        if self.prj.has_ssp_loaded:
            self.prj.clean_project()
            self.clear_app()

        # Need to request the current SVP cast from the clients prior.  Take the first one that comes through.
        self.prj.km_listener.ssp = None
        for client in range(self.prj.s.client_list.num_clients):
            log.info("testing client %s" % self.prj.s.client_list.clients[client].IP)
            self.prj.ssp_recipient_ip = self.prj.s.client_list.clients[client].IP
            self.prj.get_cast_from_sis()
            if self.prj.km_listener.ssp:
                break

        if not self.prj.km_listener.ssp:
            msg = "Unable to get SIS cast from any clients"
            dlg = wx.MessageDialog(None, msg, "Acknowledge", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()  # Show it
            dlg.Destroy()
            return

        log.info("got SSP from SIS: %s" % self.prj.km_listener.ssp)

        latitude, longitude = self.get_position()
        if (latitude is None) or (longitude is None):
            log.info("not a valid position")
            return
        log.info("using position: %s, %s" % (longitude, latitude))

        self.prj.ssp_data = self.prj.km_listener.ssp.convert_ssp()
        self.prj.ssp_data.set_position(latitude, longitude)

        self.prj.filename = "%s_SIS" % (self.prj.ssp_data.date_time.strftime("%Y%m%d_%H%M%S"))
        self.prj.s.filename_prefix = os.path.splitext(self.prj.filename)[0]

        self.prj.ssp_woa, self.prj.ssp_woa_min, self.prj.ssp_woa_max = \
            self.prj.woa09_atlas.query(latitude, longitude, self.prj.ssp_data.date_time)

        if self.prj.ssp_woa is not None:
            self.prj.ssp_data.replace_samples(self.prj.ssp_woa, 'salinity')
            self.prj.ssp_data.replace_samples(self.prj.ssp_woa, 'temperature')

        self.prj.has_ssp_loaded = True
        self.prj.surface_speed_applied = False
        self.prj.ssp_applied_depth = 0

        self._update_plot()
        self._update_state(self.gui_state['OPEN'])
        self.status_message = "Retrieved SIS current cast, user chose %.2f %.2f for position, cast date is %s" % (
            latitude, longitude, self.prj.ssp_data.date_time)

    # Export

    def on_file_export_asvp(self, evt):
        self.prj.s.switch_export_format("ASVP")

    def on_file_export_csv(self, evt):
        self.prj.s.switch_export_format("CSV")

    def on_file_export_pro(self, evt):
        self.prj.s.switch_export_format("PRO")

    def on_file_export_elac(self, evt):
        self.prj.s.switch_export_format("ELAC")

    def on_file_export_hips(self, evt):
        self.prj.s.switch_export_format("HIPS")

    def on_file_export_ixblue(self, evt):
        self.prj.s.switch_export_format("IXBLUE")

    def on_file_export_unb(self, evt):
        self.prj.s.switch_export_format("UNB")

    def on_file_export_vel(self, evt):
        self.prj.s.switch_export_format("VEL")

    def on_file_export_cast(self, evt):
        """Manage the user export"""

        # check if at least a format was selected
        if self.prj.count_export_formats() == 0:
            msg = "Please select at least a file format for export!"
            dlg = wx.MessageDialog(None, msg, "Cast export", wx.OK | wx.ICON_QUESTION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # set the export folder and filename
        if self.prj.s.user_export_prompt_filename:
            dlg = wx.FileDialog(self, "Specify an output file prefix", "", "", "All Files (*.*)|*.*",
                                style=wx.FD_SAVE | wx.FD_CHANGE_DIR)
            if dlg.ShowModal() == wx.ID_CANCEL:
                dlg.Destroy()
                return
            dlg.Destroy()
            self.prj.s.user_export_directory = dlg.GetDirectory()
            filename = dlg.GetFilename()
            self.prj.s.user_filename_prefix = os.path.splitext(filename)[0]

        else:
            # Accommodate files that are imported from an existing file (and have a fully qualified path name
            # in the self.prj.filename variable AND accommodate files that are generated in memory (e.g. WOA query)
            # and have a pathless filename in self.prj.filename.
            self.prj.s.user_export_directory = self.prj.get_output_folder()
            filename = os.path.basename(self.prj.filename)
            self.prj.s.user_filename_prefix = os.path.splitext(filename)[0]

        # actually do the export
        self.prj.formats_export("USER")

        # open export folder
        Helper.explore_folder(self.prj.s.user_export_directory)

    # clear

    def on_file_clear(self, evt):
        if self.prj.has_sippican_to_process or self.prj.has_mvp_to_process:
            msg = "You haven't processed/delivered " + self.prj.filename \
                  + " yet!\nAre you sure you want to close this file?"
            dlg = wx.MessageDialog(None, msg, "Confirm File Close", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_CANCEL:
                return
        self.prj.clean_project()
        self.clear_app()

    def clear_app(self):
        self._update_plot()
        self._update_state(self.gui_state['CLOSED'])
        self.status_message = ""

    def on_file_exit(self, evt):
        dlg = wx.MessageDialog(self, "Do you really want to close this application?", "Confirm Exit",
                               wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_CANCEL:
            return

        # Kill all gui tools
        if self.ref_monitor:
            log.info("killing refraction monitor")
            self.ref_monitor.OnExit()
        if self.geo_monitor:
            log.info("killing geo monitor")
            self.geo_monitor.OnExit()
        if self.set_viewer:
            log.info("killing settings viewer")
            self.set_viewer.OnExit()

        if self.status_timer:
            log.info("stopping status timer")
            if self.status_timer.is_alive():
                self.status_timer.stop()
        if self.plot_timer:
            log.info("stopping plot timer")
            if self.plot_timer.is_alive():
                self.plot_timer.stop()

        self.prj.release()
        time.sleep(2)  # to be sure that all the threads stop

        self.Destroy()  # Close the frame.
        log.info("exit done")

    # ####### View ########

    def on_reset_view(self, evt):
        self.p.has_zoom_applied = False
        self._update_plot()

    def on_view_hide_flagged(self, evt):
        self.p.display_flagged = not self.p.display_flagged
        self._update_plot()

    def on_view_hide_woa(self, evt):
        if not self.prj.has_ssp_loaded:
            return

        self.p.display_woa = not self.p.display_woa
        self._update_plot()

    def on_view_hide_depth(self, evt):
        self.p.display_depth = not self.p.display_depth
        self._update_plot()

    def _reset_view_limits(self):
        if self.p.has_zoom_applied or (not self.prj.has_ssp_loaded):
            return

        good_pts = (self.prj.ssp_data.data[Dicts.idx['flag'], :] == 0)
        if self.p.display_flagged:
            good_pts[:] = True

        self.p.min_speed = min(self.prj.ssp_data.data[Dicts.idx['speed'], good_pts])
        self.p.max_speed = max(self.prj.ssp_data.data[Dicts.idx['speed'], good_pts])
        self.p.min_temp = min(self.prj.ssp_data.data[Dicts.idx['temperature'], good_pts])
        self.p.max_temp = max(self.prj.ssp_data.data[Dicts.idx['temperature'], good_pts])
        self.p.min_sal = min(self.prj.ssp_data.data[Dicts.idx['salinity'], good_pts])
        self.p.max_sal = max(self.prj.ssp_data.data[Dicts.idx['salinity'], good_pts])
        self.p.max_depth = min(self.prj.ssp_data.data[Dicts.idx['depth'], good_pts])
        self.p.min_depth = max(self.prj.ssp_data.data[Dicts.idx['depth'], good_pts])

        if self.prj.surface_sound_speed:
            self.p.min_speed = min(self.p.min_speed, self.prj.surface_sound_speed)
            self.p.max_speed = max(self.p.max_speed, self.prj.surface_sound_speed)

        if self.p.display_woa and self.prj.ssp_woa:
            self.p.min_depth = max(self.p.min_depth,
                                   max(self.prj.ssp_woa.data[Dicts.idx['depth'], :]))
            self.p.max_depth = min(self.p.max_depth,
                                   min(self.prj.ssp_woa.data[Dicts.idx['depth'], :]))
            self.p.min_speed = min(self.p.min_speed,
                                   min(self.prj.ssp_woa.data[Dicts.idx['speed'], :]))
            self.p.max_speed = max(self.p.max_speed,
                                   max(self.prj.ssp_woa.data[Dicts.idx['speed'], :]))
            self.p.min_temp = min(self.p.min_temp,
                                  min(self.prj.ssp_woa.data[Dicts.idx['temperature'], :]))
            self.p.max_temp = max(self.p.max_temp,
                                  max(self.prj.ssp_woa.data[Dicts.idx['temperature'], :]))
            self.p.min_sal = min(self.p.min_sal,
                                 min(self.prj.ssp_woa.data[Dicts.idx['salinity'], :]))
            self.p.max_sal = max(self.p.max_sal,
                                 max(self.prj.ssp_woa.data[Dicts.idx['salinity'], :]))

            if self.prj.ssp_woa_min and self.prj.ssp_woa_max:
                if self.prj.ssp_woa_min.data.shape[1] > 0:
                    self.p.min_depth = max(self.p.min_depth,
                                           max(self.prj.ssp_woa_min.data[Dicts.idx['depth'], :]))
                    self.p.max_depth = min(self.p.max_depth,
                                           min(self.prj.ssp_woa_min.data[Dicts.idx['depth'], :]))
                    self.p.min_speed = min(self.p.min_speed,
                                           min(self.prj.ssp_woa_min.data[Dicts.idx['speed'], :]))
                    self.p.max_speed = max(self.p.max_speed,
                                           max(self.prj.ssp_woa_min.data[Dicts.idx['speed'], :]))
                    self.p.min_temp = min(self.p.min_temp,
                                          min(self.prj.ssp_woa_min.data[Dicts.idx['temperature'],
                                              :]))
                    self.p.max_temp = max(self.p.max_temp,
                                          max(self.prj.ssp_woa_min.data[Dicts.idx['temperature'],
                                              :]))
                    self.p.min_sal = min(self.p.min_sal,
                                         min(self.prj.ssp_woa_min.data[Dicts.idx['salinity'], :]))
                    self.p.max_sal = max(self.p.max_sal,
                                         max(self.prj.ssp_woa_min.data[Dicts.idx['salinity'], :]))

                if self.prj.ssp_woa_max.data.shape[1] > 0:
                    self.p.min_depth = max(self.p.min_depth,
                                           max(self.prj.ssp_woa_max.data[Dicts.idx['depth'], :]))
                    self.p.max_depth = min(self.p.max_depth,
                                           min(self.prj.ssp_woa_max.data[Dicts.idx['depth'], :]))
                    self.p.min_speed = min(self.p.min_speed,
                                           min(self.prj.ssp_woa_max.data[Dicts.idx['speed'], :]))
                    self.p.max_speed = max(self.p.max_speed,
                                           max(self.prj.ssp_woa_max.data[Dicts.idx['speed'], :]))
                    self.p.min_temp = min(self.p.min_temp,
                                          min(self.prj.ssp_woa_max.data[Dicts.idx['temperature'],
                                              :]))
                    self.p.max_temp = max(self.p.max_temp,
                                          max(self.prj.ssp_woa_max.data[Dicts.idx['temperature'],
                                              :]))
                    self.p.min_sal = min(self.p.min_sal,
                                         min(self.prj.ssp_woa_max.data[Dicts.idx['salinity'], :]))
                    self.p.max_sal = max(self.p.max_sal,
                                         max(self.prj.ssp_woa_max.data[Dicts.idx['salinity'], :]))

        if self.p.display_reference and self.prj.ssp_reference:
            self.p.min_depth = max(self.p.min_depth,
                                   max(self.prj.ssp_reference.data[Dicts.idx['depth'], :]))
            self.p.max_depth = min(self.p.max_depth,
                                   min(self.prj.ssp_reference.data[Dicts.idx['depth'], :]))
            self.p.min_speed = min(self.p.min_speed,
                                   min(self.prj.ssp_reference.data[Dicts.idx['speed'], :]))
            self.p.max_speed = max(self.p.max_speed,
                                   max(self.prj.ssp_reference.data[Dicts.idx['speed'], :]))
            self.p.min_temp = min(self.p.min_temp,
                                  min(self.prj.ssp_reference.data[Dicts.idx['temperature'], :]))
            self.p.max_temp = max(self.p.max_temp,
                                  max(self.prj.ssp_reference.data[Dicts.idx['temperature'], :]))
            self.p.min_sal = min(self.p.min_sal,
                                 min(self.prj.ssp_reference.data[Dicts.idx['salinity'], :]))
            self.p.max_sal = max(self.p.max_sal,
                                 max(self.prj.ssp_reference.data[Dicts.idx['salinity'], :]))

        if self.p.sel_mode == self.p.sel_modes["Insert"]:
            if self.prj.s.user_depth:
                self.p.min_depth = max(self.p.min_depth, self.prj.s.user_depth)
                self.p.max_depth = min(self.p.max_depth, self.prj.s.user_depth)

            if self.prj.s.user_speed:
                self.p.min_speed = min(self.p.min_speed, self.prj.s.user_speed)
                self.p.max_speed = max(self.p.max_speed, self.prj.s.user_speed)

            if self.prj.s.user_temperature:
                self.p.min_temp = min(self.p.min_temp, self.prj.s.user_temperature)
                self.p.max_temp = max(self.p.max_temp, self.prj.s.user_temperature)

            if self.prj.s.user_salinity:
                self.p.min_sal = min(self.p.min_sal, self.prj.s.user_salinity)
                self.p.max_sal = max(self.p.max_sal, self.prj.s.user_salinity)

        view_range = self.p.max_depth - self.p.min_depth
        if view_range == 0.0:
            view_range = 5.0

        # We let the depth scale be 25% larger to allow the user to extend
        self.p.min_depth -= 0.25 * view_range
        self.p.max_depth = -1

        view_range = self.p.max_speed - self.p.min_speed
        if view_range == 0.0:
            view_range = 5.0
        self.p.min_speed -= 0.05 * view_range
        self.p.max_speed += 0.05 * view_range

        view_range = self.p.max_temp - self.p.min_temp
        if view_range == 0.0:
            view_range = 5.0
        self.p.min_temp -= 0.05 * view_range
        self.p.max_temp += 0.05 * view_range

        view_range = self.p.max_sal - self.p.min_sal
        if view_range == 0.0:
            view_range = 5.0
        self.p.min_sal -= 0.05 * view_range
        self.p.max_sal += 0.05 * view_range

        # msg = "View limits:\n" \
        #       "- depth: %s -> %s\n" \
        #       "- speed: %s -> %s" % (self.p.min_depth, self.p.max_depth, self.p.min_speed, self.p.max_speed)
        # log.info(msg)

    # ####### Plot ######

    def on_plot_zoom(self, evt):
        self.prj.s.inspection_mode = Dicts.inspections_mode['Zoom']  # zoom mode
        self.prj.s.clear_user_samples()

        self.p.sel_mode = self.p.sel_modes["Zoom"]
        self._update_plot()
        log.info("inspection mode: zoom")

    def on_plot_flag(self, evt):
        self.prj.s.inspection_mode = Dicts.inspections_mode['Flag']  # flag data
        self.prj.s.clear_user_samples()

        self.p.sel_mode = self.p.sel_modes["Flag"]
        self._update_plot()
        log.info("flag interaction: active")

    def on_plot_unflag(self, evt):
        self.prj.s.inspection_mode = Dicts.inspections_mode['Unflag']  # unflag data
        self.prj.s.clear_user_samples()

        self.p.sel_mode = self.p.sel_modes["Flag"]
        self._update_plot()
        log.info("unflag interaction: active")

    def on_plot_insert(self, evt):
        self.prj.s.inspection_mode = Dicts.inspections_mode['Insert']  # insert data
        self.prj.s.clear_user_samples()

        self.p.sel_mode = self.p.sel_modes["Insert"]
        self._update_plot()
        log.info("insert interaction: active")

    def _on_point_selected(self, evt):
        if self.p.sel_mode != self.p.sel_modes["Insert"]:
            return

        log.info("point selection: %s, %s" % (evt.xdata, evt.ydata))

        x, y = evt.xdata, evt.ydata
        if evt.axes == self.p.speed_axes:
            if self.prj.s.user_salinity and self.prj.s.user_temperature and self.prj.s.user_depth:
                self.prj.s.user_speed = oceanography.soundspeed(self.prj.s.user_depth, self.prj.s.user_temperature,
                                                                self.prj.s.user_salinity, self.prj.ssp_data.latitude)
                msg = "User manually inserted temperature %f and salinity %f at depth %f, calculated sound speed %f" \
                      % (self.prj.s.user_temperature, self.prj.s.user_salinity, self.prj.s.user_depth,
                         self.prj.s.user_speed)
            else:
                self.prj.s.user_speed = x
                self.prj.s.user_depth = y
                self.prj.s.user_temperature = None
                self.prj.s.user_salinity = None
                msg = "User manually inserted sound speed %f at depth %f" \
                      % (self.prj.s.user_speed, self.prj.s.user_depth)

            self.prj.ssp_data.insert_sample(depth=self.prj.s.user_depth, speed=self.prj.s.user_speed,
                                            temperature=self.prj.s.user_temperature, salinity=self.prj.s.user_salinity,
                                            source=Dicts.source_types['User'])
            log.info(msg)
            self.prj.s.clear_user_samples()

        elif evt.axes == self.p.temp_axes:
            self.prj.s.user_temperature = x
            self.prj.s.user_depth = y

        elif evt.axes == self.p.sal_axes:
            self.prj.s.user_salinity = x
            self.prj.s.user_depth = y

        self._update_plot()

    def _on_area_selected(self, evt):

        if (self.p.sel_mode != self.p.sel_modes["Flag"]) and (self.p.sel_mode != self.p.sel_modes["Zoom"]):
            return

        log.info("area selection: %s, %s / %s, %s"
                        % (evt.x1data, evt.y1data, evt.x2data, evt.y2data))

        x1, y1 = evt.x1data, evt.y1data
        x2, y2 = evt.x2data, evt.y2data

        if self.p.sel_mode == self.p.sel_modes["Flag"]:
            # Deal with case of user selecting points
            if evt.axes == self.p.speed_axes:
                self.prj.ssp_data.toggle_flag([y1, y2], [x1, x2], 'speed', self.prj.s.inspection_mode)
            elif evt.axes == self.p.temp_axes:
                self.prj.ssp_data.toggle_flag([y1, y2], [x1, x2], 'temperature', self.prj.s.inspection_mode)
            elif evt.axes == self.p.sal_axes:
                self.prj.ssp_data.toggle_flag([y1, y2], [x1, x2], 'salinity', self.prj.s.inspection_mode)

        elif self.p.sel_mode == self.p.sel_modes["Zoom"]:
            # Deal with case of zooming in
            if evt.axes == self.p.speed_axes:
                self.p.min_speed = x1
                self.p.max_speed = x2
            elif evt.axes == self.p.temp_axes:
                self.p.min_temp = x1
                self.p.max_temp = x2
            elif evt.axes == self.p.sal_axes:
                self.p.min_sal = x1
                self.p.max_sal = x2
            self.p.min_depth = y1
            self.p.max_depth = y2
            self.p.has_zoom_applied = True

        # In all cases, we update the plots accordingly
        self._update_plot()

    def _update_plot(self):
        """Update the plots"""
        # log.info("updating plots")

        if self.prj.has_sippican_to_process or self.prj.has_mvp_to_process:
            if self.state == self.gui_state["CLOSED"]:
                self._update_state(self.gui_state["OPEN"])

        self._reset_view_limits()

        try:
            self._update_plot_worker()
        except PyDeadObjectError:
            log.info("dead object")
        except IndexError:
            log.info("index error during plot updating")
        except KeyError:
            log.info("key error during plot updating")
        except ValueError:
            log.info("value error during plot updating")
        except AttributeError:
            log.info("attribute error during plot updating")
        except RuntimeError:
            log.info("runtime error during plot updating")

    def _update_plot_worker(self):
        """Update the plots"""

        self.p.plots.get_figure().clf()
        if not self.prj.has_ssp_loaded:
            self.p.plots.draw()
            return

        if self.prj.server.is_running:
            bg_color = '#32cd32'  # green
        elif self.prj.has_sippican_to_process or self.prj.has_mvp_to_process:
            bg_color = '#F23047'  # red
        else:
            bg_color = 'w'

        # Fresh axes every time
        self.p.speed_axes = self.p.plots.get_figure().add_subplot(131, axisbg=bg_color)
        self.p.speed_axes.invert_yaxis()
        self.p.temp_axes = self.p.plots.get_figure().add_subplot(132, sharey=self.p.speed_axes, axisbg=bg_color)
        self.p.temp_axes.invert_yaxis()
        self.p.sal_axes = self.p.plots.get_figure().add_subplot(133, sharey=self.p.speed_axes, axisbg=bg_color)
        self.p.sal_axes.invert_yaxis()

        if self.prj.has_ssp_loaded and self.p.display_woa and self.prj.ssp_woa:
            # Plot WOA2009 profile for context if desired, but only if we have a current SV loaded
            self.p.speed_axes.plot(self.prj.ssp_woa.data[Dicts.idx['speed'], :],
                                   self.prj.ssp_woa.data[Dicts.idx['depth'], :], 'm--')
            self.p.speed_axes.hold(True)
            self.p.temp_axes.plot(self.prj.ssp_woa.data[Dicts.idx['temperature'], :],
                                  self.prj.ssp_woa.data[Dicts.idx['depth'], :], 'm--')
            self.p.temp_axes.hold(True)
            self.p.sal_axes.plot(self.prj.ssp_woa.data[Dicts.idx['salinity'], :],
                                 self.prj.ssp_woa.data[Dicts.idx['depth'], :], 'm--')
            self.p.sal_axes.hold(True)

            if self.prj.ssp_woa_max and self.prj.ssp_woa_min:
                self.p.speed_axes.plot(self.prj.ssp_woa_min.data[Dicts.idx['speed'], :],
                                       self.prj.ssp_woa_min.data[Dicts.idx['depth'], :], 'm--')
                self.p.temp_axes.plot(self.prj.ssp_woa_min.data[Dicts.idx['temperature'], :],
                                      self.prj.ssp_woa_min.data[Dicts.idx['depth'], :], 'm--')
                self.p.sal_axes.plot(self.prj.ssp_woa_min.data[Dicts.idx['salinity'], :],
                                     self.prj.ssp_woa_min.data[Dicts.idx['depth'], :], 'm--')
                self.p.speed_axes.plot(self.prj.ssp_woa_max.data[Dicts.idx['speed'], :],
                                       self.prj.ssp_woa_max.data[Dicts.idx['depth'], :], 'm--')
                self.p.temp_axes.plot(self.prj.ssp_woa_max.data[Dicts.idx['temperature'], :],
                                      self.prj.ssp_woa_max.data[Dicts.idx['depth'], :], 'm--')
                self.p.sal_axes.plot(self.prj.ssp_woa_max.data[Dicts.idx['salinity'], :],
                                     self.prj.ssp_woa_max.data[Dicts.idx['depth'], :], 'm--')

        if self.p.display_reference and self.prj.ssp_reference:
            # Plot Reference profile
            good_pts = (self.prj.ssp_reference.data[Dicts.idx['flag'], :] == 0)
            self.p.speed_axes.plot(self.prj.ssp_reference.data[Dicts.idx['speed'], good_pts],
                                   self.prj.ssp_reference.data[Dicts.idx['depth'], good_pts], 'y')

            if self.prj.has_ssp_loaded:
                self.p.speed_axes.plot(self.prj.ssp_reference.data[Dicts.idx['speed'], good_pts],
                                       self.prj.ssp_reference.data[Dicts.idx['depth'], good_pts],
                                       'y', linewidth=3.0)

            self.p.speed_axes.hold(True)

            self.p.temp_axes.plot(self.prj.ssp_reference.data[Dicts.idx['temperature'], good_pts],
                                  self.prj.ssp_reference.data[Dicts.idx['depth'], good_pts], 'y')

            if self.prj.has_ssp_loaded:
                self.p.temp_axes.plot(self.prj.ssp_reference.data[Dicts.idx['temperature'], good_pts],
                                      self.prj.ssp_reference.data[Dicts.idx['depth'], good_pts],
                                      'y', linewidth=3.0)
            self.p.temp_axes.hold(True)

            self.p.sal_axes.plot(self.prj.ssp_reference.data[Dicts.idx['salinity'], good_pts],
                                 self.prj.ssp_reference.data[Dicts.idx['depth'], good_pts], 'y')
            if self.prj.has_ssp_loaded:
                self.p.sal_axes.plot(self.prj.ssp_reference.data[Dicts.idx['salinity'], good_pts],
                                     self.prj.ssp_reference.data[Dicts.idx['depth'], good_pts],
                                     'y', linewidth=3.0)

            self.p.sal_axes.hold(True)

        if self.prj.ssp_data.sis_data is not None:
            # Plot thinned SSP for sis
            good_pts = (self.prj.ssp_data.sis_data[Dicts.idx['flag'], :] == 0)
            self.p.speed_axes.plot(self.prj.ssp_data.sis_data[Dicts.idx['speed'], good_pts],
                                   self.prj.ssp_data.sis_data[Dicts.idx['depth'], good_pts],
                                   marker='o', markersize=2.5, markerfacecolor='#00FF00', fillstyle=u'full',
                                   linestyle='-', color='#33FF33')

        if self.prj.has_ssp_loaded and self.p.display_flagged:
            # Plot rejected points if desired
            bad_pts = (self.prj.ssp_data.data[Dicts.idx['flag'], :] == 1)
            self.p.speed_axes.plot(self.prj.ssp_data.data[Dicts.idx['speed'], bad_pts],
                                   self.prj.ssp_data.data[Dicts.idx['depth'], bad_pts], 'r,')
            self.p.speed_axes.hold(True)
            self.p.temp_axes.plot(self.prj.ssp_data.data[Dicts.idx['temperature'], bad_pts],
                                  self.prj.ssp_data.data[Dicts.idx['depth'], bad_pts], 'r,')
            self.p.temp_axes.hold(True)
            self.p.sal_axes.plot(self.prj.ssp_data.data[Dicts.idx['salinity'], bad_pts],
                                 self.prj.ssp_data.data[Dicts.idx['depth'], bad_pts], 'r,')
            self.p.sal_axes.hold(True)

        # Now plot the good points
        if self.prj.server.is_running:
            line = 'k'
        else:
            line = 'b'

        if self.prj.has_ssp_loaded:
            good_pts = (self.prj.ssp_data.data[Dicts.idx['flag'], :] == 0)
            self.p.speed_axes.plot(self.prj.ssp_data.data[Dicts.idx['speed'], good_pts],
                                   self.prj.ssp_data.data[Dicts.idx['depth'], good_pts], line)
            self.p.temp_axes.plot(self.prj.ssp_data.data[Dicts.idx['temperature'], good_pts],
                                  self.prj.ssp_data.data[Dicts.idx['depth'], good_pts], line)
            self.p.sal_axes.plot(self.prj.ssp_data.data[Dicts.idx['salinity'], good_pts],
                                 self.prj.ssp_data.data[Dicts.idx['depth'], good_pts], line)

        # Label plots, etc
        self.p.speed_axes.grid()
        self.p.speed_axes.axis([self.p.min_speed, self.p.max_speed, self.p.min_depth, self.p.max_depth])
        self.p.speed_axes.set_xlabel('Sound Speed [m/s]')
        self.p.speed_axes.set_ylabel('Depth [m]')

        self.p.temp_axes.grid()
        self.p.temp_axes.axis([self.p.min_temp, self.p.max_temp, self.p.min_depth,
                               self.p.max_depth])
        self.p.temp_axes.set_xlabel('Temp [deg. C]')

        self.p.sal_axes.grid()
        self.p.sal_axes.axis([self.p.min_sal, self.p.max_sal, self.p.min_depth,
                              self.p.max_depth])
        self.p.sal_axes.set_xlabel('Sal [psu]')

        if self.prj.server.is_running:
            age_of_transmission = dt.datetime.utcnow() - self.prj.time_of_last_tx
            self.p.temp_axes.set_title("SERVER: %d cast(s) delivered\nTime since last transmission: %s"
                                       % (self.prj.server.delivered_casts,
                                          ':'.join(str(age_of_transmission).split(':')[:2])))

        elif self.prj.has_sippican_to_process or self.prj.has_mvp_to_process:
            self.p.temp_axes.set_title("Received %s... please process and deliver to SIS"
                                       % (os.path.basename(self.prj.filename)))

        else:
            if self.prj.time_of_last_tx:
                age_of_transmission = dt.datetime.utcnow() - self.prj.time_of_last_tx
                self.p.temp_axes.set_title("%s\nTime since last transmission: %s" % (
                    os.path.basename(self.prj.filename), ':'.join(str(age_of_transmission).split(':')[:2])))
            else:
                self.p.temp_axes.set_title("%s" % os.path.basename(self.prj.filename))

        # plot the current mean depth (if available and the user setting is on)
        #print("# %s %s" % (self.prj.mean_depth, self.p.display_depth))
        if self.prj.mean_depth and self.p.display_depth:
            # draw line on the 3 plots
            line = '#663300'
            y = [self.prj.mean_depth, self.prj.mean_depth]
            x = [-100.0, 2000]  # sound speed
            self.p.speed_axes.plot(x, y, line)
            x = [-100.0, 100]  # temperature
            self.p.temp_axes.plot(x, y, line)
            x = [-100.0, 100]  # salinity
            self.p.sal_axes.plot(x, y, line)

            # draw rectangle on the 3 plots
            if self.prj.server.is_running:
                a = 0.8
            else:
                a = 0.5
            sel = matplotlib.patches.Rectangle((-100.0, self.prj.mean_depth), 2100, 12000, edgecolor='k',
                                               facecolor='#996633', label='_nolegend_', alpha=a)
            self.p.speed_axes.add_patch(sel)
            sel = matplotlib.patches.Rectangle((-100.0, self.prj.mean_depth), 200, 12000, edgecolor='k',
                                               facecolor='#996633', label='_nolegend_', alpha=a)
            self.p.temp_axes.add_patch(sel)
            sel = matplotlib.patches.Rectangle((-100.0, self.prj.mean_depth), 200, 12000, edgecolor='k',
                                               facecolor='#996633', label='_nolegend_', alpha=a)
            self.p.sal_axes.add_patch(sel)

        # plot vessel draft and surface sound speed (if available) [only on the speed plot]
        #print("@ %s %s" % (self.prj.vessel_draft, self.prj.surface_sound_speed))
        if self.prj.vessel_draft and self.prj.surface_sound_speed:
            line = 'g--'
            # vertical line
            x = [self.prj.surface_sound_speed, self.prj.surface_sound_speed]
            y = [0.0, 12000]
            self.p.speed_axes.plot(x, y, line)
            # horizontal line
            x = [-100.0, 2100]
            y = [self.prj.vessel_draft, self.prj.vessel_draft]
            self.p.speed_axes.plot(x, y, line)
            # dot at the draft/surface sound speed intersection
            self.p.speed_axes.plot(self.prj.surface_sound_speed, self.prj.vessel_draft, 'g+', mew=1.6, ms=6)

        # plotting during point insertion
        if self.p.sel_mode == self.p.sel_modes["Insert"]:

            salinities = np.zeros(2)
            temperatures = np.zeros(2)
            depths = np.zeros(2)

            depths[0] = self.prj.s.user_depth

            pts = ((self.prj.ssp_data.data[Dicts.idx['flag'], :] == 0)
                   & (self.prj.ssp_data.data[Dicts.idx['depth'], :] < self.prj.s.user_depth))
            if np.count_nonzero(pts) > 0:
                depths[1] = self.prj.ssp_data.data[Dicts.idx['depth'], pts][-1]
                temperatures[1] = self.prj.ssp_data.data[Dicts.idx['temperature'], pts][-1]
                salinities[1] = self.prj.ssp_data.data[Dicts.idx['salinity'], pts][-1]
                if self.prj.s.user_salinity:
                    salinities[0] = self.prj.s.user_salinity
                    self.p.sal_axes.plot(salinities, depths, "c--")
                if self.prj.s.user_temperature:
                    temperatures[0] = self.prj.s.user_temperature
                    self.p.temp_axes.plot(temperatures, depths, "c--")

            pts = ((self.prj.ssp_data.data[Dicts.idx['flag'], :] == 0)
                   & (self.prj.ssp_data.data[Dicts.idx['depth'], :] > self.prj.s.user_depth))
            if np.count_nonzero(pts) > 0:
                depths[1] = self.prj.ssp_data.data[Dicts.idx['depth'], pts][0]
                temperatures[1] = self.prj.ssp_data.data[Dicts.idx['temperature'], pts][0]
                salinities[1] = self.prj.ssp_data.data[Dicts.idx['salinity'], pts][0]
                if self.prj.s.user_salinity:
                    salinities[0] = self.prj.s.user_salinity
                    self.p.sal_axes.plot(salinities, depths, "c--")
                if self.prj.s.user_temperature:
                    temperatures[0] = self.prj.s.user_temperature
                    self.p.temp_axes.plot(temperatures, depths, "c--")

            if self.prj.s.user_salinity:
                self.p.sal_axes.plot(self.prj.s.user_salinity, self.prj.s.user_depth, "c.")
            if self.prj.s.user_temperature:
                self.p.temp_axes.plot(self.prj.s.user_temperature, self.prj.s.user_depth, "c.")

        self.p.plots.draw()

    # ######  Process #####

    def on_process_load_salinity(self, evt):
        """XBT-specific function to add salinity values"""

        if self.prj.ssp_data.sensor_type != Dicts.sensor_types["XBT"]:
            msg = 'This is a XBT-specific function!'
            dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        if self.prj.ssp_reference:
            log.info("using reference cast to augment salinity")
            self.prj.ssp_data.replace_samples(self.prj.ssp_reference, 'salinity')
            salinity_source = 'user-specified reference file %s' % self.prj.ssp_reference_filename

        else:  # atlases
            if self.prj.s.ssp_salinity_source == Dicts.salinity_sources["RTOFS"]:
                # ext_type = Dicts.source_types['RtofsExtend']
                salinity_source = "RTOFS"
                if not self.prj.rtofs_atlas_loaded:
                    if self.prj.woa09_atlas_loaded:  # try with WOA09
                        log.info("RTOFS grids not loaded, reverting to WOA09")
                        #ext_type = Dicts.source_types['Woa09Extend']
                        salinity_source = "WOA09"
                        self.prj.ssp_data.replace_samples(self.prj.ssp_woa, 'salinity')
                    else:
                        msg = "Functionality disabled: Failed on load RTOFS and WOA09 grids"
                        dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
                        dlg.ShowModal()
                        dlg.Destroy()
                        return
                else:
                    try:
                        temp_sv = self.prj.rtofs_atlas.query(self.prj.ssp_data.latitude,
                                                             self.prj.ssp_data.longitude,
                                                             self.prj.ssp_data.date_time)
                        self.prj.ssp_data.replace_samples(temp_sv, 'salinity')

                    except SspError:
                        if self.prj.woa09_atlas_loaded:  # try with WOA09
                            log.info("failure in RTOFS lookup, reverting to WOA09")
                            #ext_type = Dicts.source_types['Woa09Extend']
                            salinity_source = "WOA09"
                            self.prj.ssp_data.replace_samples(self.prj.ssp_woa, 'salinity')

                        else:
                            msg = "Functionality disabled: Failed on load RTOFS and WOA09 grids"
                            dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
                            dlg.ShowModal()
                            dlg.Destroy()
                            return

            elif self.prj.s.ssp_salinity_source == Dicts.salinity_sources["WOA09"]:
                # ext_type = Dicts.source_types['Woa09Extend']
                salinity_source = "WOA09"

                if not self.prj.woa09_atlas_loaded:
                    msg = "Functionality disabled: failure in loading WOA09 atlas"
                    dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return

                if self.prj.ssp_woa is None:
                    msg = "Functionality disabled: failure in WOA2009 lookup"
                    dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return

                # And then extend by WOA
                self.prj.ssp_data.replace_samples(self.prj.ssp_woa, 'salinity')

            else:
                raise SspError("unsupported extension source: %s" % self.prj.s.ssp_extension_source)

        # Now replace the salinity values in the cast with the salinity values in WOA
        self.prj.ssp_data.calc_speed()
        # add metadata to source info
        self.prj.ssp_data.modify_source_info("salinity augmented from %s" % salinity_source)

        self._update_plot()
        msg = 'Salinity added to profile using source %s' % salinity_source
        log.info(msg)
        self.status_message = 'Salinity added from %s' % salinity_source

    def on_process_load_temp_and_sal(self, evt):
        """XSV- and SVP- specific function"""

        if (self.prj.ssp_data.sensor_type != Dicts.sensor_types["XSV"])\
                and (self.prj.ssp_data.sensor_type != Dicts.sensor_types["SVP"]):
            msg = 'XSV- and SVP-specific function!'
            dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        if self.prj.ssp_reference:
            log.info("using reference cast to augment salinity and temperature")
            self.prj.ssp_data.replace_samples(self.prj.ssp_reference, 'salinity')
            self.prj.ssp_data.replace_samples(self.prj.ssp_reference, 'temperature')
            temperature_salinity_source = 'user specified reference file %s' % self.prj.ssp_reference_filename

        else:  # atlases
            if self.prj.s.ssp_salinity_source == Dicts.salinity_sources["RTOFS"]:
                # ext_type = Dicts.source_types['RtofsExtend']
                temperature_salinity_source = "RTOFS"
                if not self.prj.rtofs_atlas_loaded:
                    if self.prj.woa09_atlas_loaded:  # try with WOA09
                        log.info("RTOFS grids not loaded, reverting to WOA09")
                        #ext_type = Dicts.source_types['Woa09Extend']
                        temperature_salinity_source = "WOA09"
                        self.prj.ssp_data.replace_samples(self.prj.ssp_woa, 'salinity')
                        self.prj.ssp_data.replace_samples(self.prj.ssp_woa, 'temperature')
                    else:
                        msg = "Functionality disabled: Failed on load RTOFS and WOA09 grids"
                        dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
                        dlg.ShowModal()
                        dlg.Destroy()
                        return
                else:
                    try:
                        temp_sv = self.prj.rtofs_atlas.query(self.prj.ssp_data.latitude,
                                                             self.prj.ssp_data.longitude,
                                                             self.prj.ssp_data.date_time)
                        self.prj.ssp_data.replace_samples(temp_sv, 'salinity')
                        self.prj.ssp_data.replace_samples(temp_sv, 'temperature')

                    except SspError:
                        if self.prj.woa09_atlas_loaded:  # try with WOA09
                            log.info("failure in RTOFS lookup, reverting to WOA09")
                            #ext_type = Dicts.source_types['Woa09Extend']
                            temperature_salinity_source = "WOA09"
                            self.prj.ssp_data.replace_samples(self.prj.ssp_woa, 'salinity')
                            self.prj.ssp_data.replace_samples(self.prj.ssp_woa, 'temperature')

                        else:
                            msg = "Functionality disabled: Failed on load RTOFS and WOA09 grids"
                            dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
                            dlg.ShowModal()
                            dlg.Destroy()
                            return

            elif self.prj.s.ssp_salinity_source == Dicts.salinity_sources["WOA09"]:
                # ext_type = Dicts.source_types['Woa09Extend']
                temperature_salinity_source = "WOA09"

                if not self.prj.woa09_atlas_loaded:
                    msg = "Functionality disabled: failure in loading WOA09 atlas"
                    dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return

                if self.prj.ssp_woa is None:
                    msg = "Functionality disabled: failure in WOA2009 lookup"
                    dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return

                # And then extend by WOA
                self.prj.ssp_data.replace_samples(self.prj.ssp_woa, 'salinity')
                self.prj.ssp_data.replace_samples(self.prj.ssp_woa, 'temperature')

            else:
                raise SspError("unsupported extension source: %s" % self.prj.s.ssp_extension_source)

        # add metadata to source info
        self.prj.ssp_data.modify_source_info("temperature/salinity augmented from %s" % temperature_salinity_source)

        # We don't recalculate speed, of course.  T/S is simply for absorption coefficient calculation
        self._update_plot()
        msg = 'Temperature/Salinity added to profile using source %s' % temperature_salinity_source
        log.info(msg)
        self.status_message = "Temperature/salinity added from %s" % temperature_salinity_source

    def on_process_load_surface_ssp(self, evt):

        if self.prj.km_listener.xyz88:
            surface_ssp = np.mean(self.prj.km_listener.xyz88.sound_speed)
            surface_ssp_source = "depth datagram"
        else:
            dlg = wx.TextEntryDialog(None,
                                     'No surface sound speed received on port 16103.\nPlease enter surface sound speed',
                                     'Text Entry')

            if dlg.ShowModal() == wx.ID_CANCEL:
                dlg.Destroy()
                return

            dlg.Destroy()
            surface_ssp = float(dlg.GetValue())
            surface_ssp_source = "manual entry"

        if not self.prj.vessel_draft:
            self.get_transducer_draft()

        if not self.prj.vessel_draft:
            return

        # Insert the surface speed value into the profile at the vessel_draft
        self.prj.surface_speed_applied = True
        self.prj.ssp_applied_depth = 1.15 * self.prj.vessel_draft
        self.prj.ssp_data.insert_sample(depth=self.prj.ssp_applied_depth, speed=surface_ssp,
                                        temperature=None, salinity=None,
                                        source=Dicts.source_types['SurfaceSensor'])

        # And set all values shoaller than the draft to be the same speed
        idx = self.prj.ssp_data.data[Dicts.idx['depth'], :] < self.prj.ssp_applied_depth
        self.prj.ssp_data.data[Dicts.idx['speed'], idx] = surface_ssp
        self.prj.ssp_data.modify_source_info('surface sound speed from %s' % surface_ssp_source)

        self._update_plot()
        msg = 'Surface sound speed %.2f added to profile for upper %.1f m (source: %s)' \
              % (surface_ssp, self.prj.vessel_draft, surface_ssp_source)
        log.info(msg)
        self.status_message = "Added surface sound speed %.1f" % surface_ssp

    def on_process_extend(self, evt):
        if self.prj.has_ssp_loaded is None:
            log.info("no ssp to extend")
            return

        if self.prj.ssp_reference:
            log.info("Extending with user-specified reference profile")
            ext_type = Dicts.source_types['UserRefExtend']
            self.prj.ssp_data.extend(self.prj.ssp_reference, ext_type)

        else:  # atlases
            if self.prj.s.ssp_extension_source == Dicts.extension_sources["RTOFS"]:
                ext_type = Dicts.source_types['RtofsExtend']
                if not self.prj.rtofs_atlas_loaded:
                    if self.prj.woa09_atlas_loaded:  # try with WOA09
                        log.info("RTOFS grids not loaded, reverting to WOA09")
                        ext_type = Dicts.source_types['Woa09Extend']
                        self.prj.ssp_data.extend(self.prj.ssp_woa, ext_type)
                    else:
                        msg = "Functionality disabled: Failed on load RTOFS and WOA09 grids"
                        dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
                        dlg.ShowModal()
                        dlg.Destroy()
                        return
                else:
                    try:
                        temp_sv = self.prj.rtofs_atlas.query(self.prj.ssp_data.latitude,
                                                             self.prj.ssp_data.longitude,
                                                             self.prj.ssp_data.date_time)
                        self.prj.ssp_data.extend(temp_sv, ext_type)
                        # now use the WOA09 since it usually goes deeper
                        self.prj.ssp_data.extend(temp_sv, Dicts.source_types['Woa09Extend'])

                    except SspError:
                        if self.prj.woa09_atlas_loaded:  # try with WOA09
                            log.info("failure in RTOFS lookup, reverting to WOA09")
                            ext_type = Dicts.source_types['Woa09Extend']
                            self.prj.ssp_data.extend(self.prj.ssp_woa, ext_type)

                        else:
                            msg = "Functionality disabled: Failed on load RTOFS and WOA09 grids"
                            dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
                            dlg.ShowModal()
                            dlg.Destroy()
                            return

            elif self.prj.s.ssp_extension_source == Dicts.extension_sources["WOA09"]:
                ext_type = Dicts.source_types['Woa09Extend']

                if not self.prj.woa09_atlas_loaded:
                    msg = "Functionality disabled: failure in loading WOA09 atlas"
                    dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return

                if self.prj.ssp_woa is None:
                    msg = "Functionality disabled: failure in WOA2009 lookup"
                    dlg = wx.MessageDialog(None, msg, "Error", wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return

                # And then extend by WOA
                self.prj.ssp_data.extend(self.prj.ssp_woa, ext_type)

            else:
                raise SspError("unsupported extension source: %s" % self.prj.s.ssp_extension_source)

        self._update_plot()

        msg = 'Profile extended to depth %d m using source type %s' \
              % (self.prj.ssp_data.data[Dicts.idx['depth'], self.prj.ssp_data.data.shape[1] - 1], ext_type)
        log.info(msg)
        self.prj.ssp_data.modify_source_info("extension type %s" % ext_type)
        self.status_message = 'Profile extended using source type %s' % ext_type

    def on_process_preview_thinning(self, event):
        log.info("preview thinning")
        self.prj.ssp_data.prepare_sis_data(thin=True)

        self._update_plot()

        log.info('Preview the thinning step required by some client types')
        self.status_message = 'Preview thinning'

    def on_process_send_profile(self, evt):

        if self.prj.s.auto_export_on_send and self.prj.count_export_formats() == 0:
            msg = "The selected 'auto-export' option requires selection of export formats from Export sub-menu.\n" \
                  "Send anyway or cancel?"
            dlg = wx.MessageDialog(None, msg, "Auto-export option", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_CANCEL:
                return

        if not self.prj.ssp_recipient_ip:
            dlg = wx.TextEntryDialog(None, 'Enter Remote IP address', 'Text Entry')
            if dlg.ShowModal() == wx.ID_CANCEL:
                dlg.Destroy()
                return
            dlg.Destroy()

            try:
                # inet_pton supports IPV6
                socket.inet_aton(dlg.GetValue())

            except socket.error:
                dlg = wx.MessageDialog(None, "Error: Invalid IP address", "Error", wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()  # Show it
                dlg.Destroy()
                return

            self.prj.ssp_recipient_ip = dlg.GetValue()
            dlg.Destroy()

        if self.ref_monitor:
            self.ref_monitor.pause_corrections()

            corrector = self.ref_monitor.get_corrector()
            depth = self.ref_monitor.get_mean_depth()

            # Only if the server is not running
            if corrector != 0.0:
                msg = "Do you really want to apply the corrector calculated with the Refraction Monitor?\n" \
                      "This will manipulate the SSP (corrector: %.1f, depth: %.1f)" \
                      % (corrector, depth)
                dlg = wx.MessageDialog(None, msg, "Warning", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
                result = dlg.ShowModal()
                if result == wx.ID_CANCEL:
                    corrector = 0.0
                dlg.Destroy()

            if corrector != 0.0:
                log.info("applying corrector: %s %s" % (corrector, depth))

                if self.prj.surface_speed_applied:
                    idx = self.prj.ssp_data.data[Dicts.idx['depth'], :] > self.prj.ssp_applied_depth
                    self.prj.ssp_data.data[Dicts.idx['speed'], idx] = \
                        self.prj.ssp_data.data[Dicts.idx['speed'], idx] + corrector
                else:
                    self.prj.ssp_data.data[Dicts.idx['speed'], :] = \
                        self.prj.ssp_data.data[Dicts.idx['speed'], :] + corrector
                self.ref_monitor.set_corrector(0)

        # loop through client list
        success = True
        fmt = None
        for client in range(self.prj.s.client_list.num_clients):

            if self.prj.s.sis_auto_apply_manual_casts:
                fmt = Dicts.kng_formats['S01']
            else:
                fmt = Dicts.kng_formats['S12']

            msg = "Transmitting cast to %s" % self.prj.s.client_list.clients[client].IP
            log.info(msg)
            self.status_message = msg
            self._update_status()

            success = self.prj.send_cast(self.prj.s.client_list.clients[client], fmt)

            if self.prj.s.sis_auto_apply_manual_casts:
                if success:
                    if self.prj.s.client_list.clients[client].protocol == "SIS":
                        log.info("Reception confirmed from " + self.prj.s.client_list.clients[client].IP)
                        self.status_message = "Reception confirmed!"
                        msg = "SIS confirmed the SSP reception!"
                        dlg = wx.MessageDialog(None, msg, "SIS acknowledge", wx.OK)
                        dlg.ShowModal()
                        dlg.Destroy()
                        if self.prj.has_sippican_to_process:
                            self.prj.has_sippican_to_process = False
                        if self.prj.has_mvp_to_process:
                            self.prj.has_mvp_to_process = False
                    else:
                        self.status_message = "Transmitted cast, confirm reception in %s" % (
                            self.prj.s.client_list.clients[client].protocol)
                else:
                    msg = "Cannot confirm reception of profile for client %s, please check SIS:\n" % (
                        self.prj.s.client_list.clients[client].IP)
                    msg += "1) Check sound speed file name in SIS run-time parameters " \
                           "and match date/time in SIS .asvp filename with cast date/time to ensure receipt\n"
                    msg += "2) Ensure SVP datagram is being distributed to this IP " \
                           "on port %d to enable future confirmations" % self.prj.s.km_listen_port
                    log.info(msg)
                    dlg = wx.MessageDialog(None, msg, "Acknowledge", wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()  # Show it
                    dlg.Destroy()

        if not self.prj.s.sis_auto_apply_manual_casts:
            msg = "Profile transmitted, SIS is waiting for operator confirmation."
            log.info(msg)
            dlg = wx.MessageDialog(None, msg, "Acknowledge", wx.OK)
            dlg.ShowModal()  # Show it
            dlg.Destroy()

        msg = "Transmitted Data: %s" % self.prj.ssp_data.convert_km(fmt)
        log.info(msg)

        # Now that we're done sending to clients, auto-export files if desired
        if self.prj.s.auto_export_on_send:
            self.prj.formats_export("USER")

        if success:
            self.prj.time_of_last_tx = dt.datetime.utcnow()
        else:
            self.prj.time_of_last_tx = None

        self._update_plot()

        if self.ref_monitor:
            self.ref_monitor.resume_corrections()

        if self.prj.has_sippican_to_process or self.prj.has_mvp_to_process:
            # If we had received a sippican cast over UDP
            # then update the display to remove the RED background
            self.prj.has_sippican_to_process = False
            self.prj.has_mvp_to_process = False
            self._update_plot()

    def on_process_store_db(self, event):
        log.info("store current SSP:\n%s" % self.prj.ssp_data)

        # create a collection with only the current cast
        ssp_coll = SspCollection()
        ssp_coll.append(self.prj.ssp_data)

        # add the created collection to the local db
        ssp_db = SspDb()
        ssp_db.add_casts(ssp_coll)
        ssp_db.disconnect()

    def on_process_redo_processing(self, event):

        msg = "Do you really want to reload the stored raw data?\n" \
              "This implies to lose all the applied processing actions!"
        dlg = wx.MessageDialog(None, msg, "Restart processing", wx.YES | wx.NO | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_NO:
            return

        log.info("restart processing")
        self.prj.ssp_data.restart_processing()

        self._update_plot()

        log.info('Restart processing using stored raw data')
        self.status_message = 'Restart processing'

    def on_process_log_metadata(self, evt):
        """Activate the logging of the processing metadata"""
        flag = self.ProcessLogMetadata.IsChecked()

        # to be able to log the first and the last message
        if flag:
            self.prj.activate_logging_on_db()
        else:
            self.prj.deactivate_logging_on_db()

    # def on_process_express_mode(self, evt):
    # """DISABLED SINCE USERS TEND TO MISUSE THIS FUNCTIONALITY"""
    #     msg = "Are you sure you want to do express processing?\nThis will deliver the profile to the sounder."
    #     dlg = wx.MessageDialog(None, msg, "Question", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
    #     result = dlg.ShowModal()
    #     dlg.Destroy()
    #     if result == wx.ID_CANCEL:
    #         return
    #     if self.prj.ssp_data.sensor_type == Dict.sensor_types["XBT"]:
    #         self.on_process_load_salinity(evt)
    #     elif self.prj.ssp_data.sensor_type == "XSV" or self.prj.ssp_data.sensor_type == "SVP":
    #         self.on_process_load_temp_and_sal(evt)
    #     self.on_process_load_surface_ssp(evt)
    #     self.on_process_extend(evt)
    #     self.on_process_send_profile(evt)

    # ####### Database ######

    def on_db_query_internal_db(self, event):
        log.info("query internal db")

        self._query_db()

    def on_db_query_external_db(self, event):
        log.info("query external db")

        # retrieve the name of the format
        selection_filter = "DB files (*.db,*.DB)|*.db;*.DB|All File (*.*)|*.*"
        dlg = wx.FileDialog(self, "External DB Selection", "", "", selection_filter,
                            style=wx.FD_OPEN | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        db_directory = dlg.GetDirectory()
        db_file = dlg.GetFilename()
        dlg.Destroy()
        db_path = os.path.join(db_directory, db_file)

        self._query_db(db_path)

    def _query_db(self, db_path=None):
        """Query and load SSP from a DB (both internal and extenal)"""

        try:
            if db_path is None:
                ssp_db = SspDb()
            else:
                ssp_db = SspDb(db_path=db_path)

        except HyOError as e:
            msg = '%s' % e
            dlg = wx.MessageDialog(None, msg, "Local DB", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        pk_list = ssp_db.list_all_ssp_pks()
        #print(pk_list)
        if len(pk_list) == 0:
            msg = 'The DB is empty. Load and store an SSP first!'
            dlg = wx.MessageDialog(None, msg, "Local DB", wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
            ssp_db.disconnect()
            return

        if self.prj.has_ssp_loaded:
            self.prj.clean_project()
            self.clear_app()

        dlg_list = [("%04d: %s @ %s [%s]" % (tp[0], tp[1], tp[2], Dicts.first_match(Dicts.sensor_types, int(tp[4]))))
                    for tp in pk_list]
        #print(dlg_list)
        dialog = wx.SingleChoiceDialog(None, "Pick a stored SSP", "Local DB", dlg_list)
        selection = dialog.ShowModal()
        dialog.Destroy()
        if selection != wx.ID_OK:
            ssp_db.disconnect()
            return

        # actually loading the data
        self.prj.ssp_data = ssp_db.get_ssp_by_pk(pk_list[dialog.GetSelection()][0])
        self.prj.filename = "%s_LocalDB" % self.prj.ssp_data.original_path
        self.prj.s.filename_prefix = os.path.splitext(self.prj.filename)[0]

        self.prj.ssp_woa, self.prj.ssp_woa_min, self.prj.ssp_woa_max = \
            self.prj.woa09_atlas.query(self.prj.ssp_data.latitude, self.prj.ssp_data.longitude,
                                       self.prj.ssp_data.date_time)

        if self.prj.ssp_woa is not None:
            self.prj.ssp_data.replace_samples(self.prj.ssp_woa, 'salinity')
            self.prj.ssp_data.replace_samples(self.prj.ssp_woa, 'temperature')

        self.prj.has_ssp_loaded = True
        self.prj.surface_speed_applied = False
        self.prj.ssp_applied_depth = 0

        self._update_plot()
        self._update_state(self.gui_state['OPEN'])

        self.status_message = "Loaded SSP from local DB"
        log.info("Loaded selected SSP: %s [%s]\n" % (dialog.GetSelection(), dialog.GetStringSelection()))

        ssp_db.disconnect()

    # Delete

    def on_db_delete_internal(self, event):
        log.info("deletion from internal db")

        self._delete_db_ssp()

    def on_db_delete_external(self, event):
        log.info("deletion from external db")

        # retrieve the name of the format
        selection_filter = "DB files (*.db,*.DB)|*.db;*.DB|All File (*.*)|*.*"
        dlg = wx.FileDialog(self, "External DB Selection", "", "", selection_filter,
                            style=wx.FD_OPEN | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        db_directory = dlg.GetDirectory()
        db_file = dlg.GetFilename()
        dlg.Destroy()
        db_path = os.path.join(db_directory, db_file)

        self._query_db(db_path)

    def _delete_db_ssp(self, db_path=None):
        """Delete SSP entries from a DB (both internal and extenal)"""

        try:
            if db_path is None:
                ssp_db = SspDb()
            else:
                ssp_db = SspDb(db_path=db_path)

        except HyOError as e:
            msg = '%s' % e
            dlg = wx.MessageDialog(None, msg, "Local DB", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        pk_list = ssp_db.list_all_ssp_pks()
        #print(pk_list)
        if len(pk_list) == 0:
            msg = 'The DB is empty. Nothing to delete!'
            dlg = wx.MessageDialog(None, msg, "Local DB", wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
            ssp_db.disconnect()
            return

        if self.prj.has_ssp_loaded:
            self.prj.clean_project()
            self.clear_app()

        dlg_list = [("%04d: %s @ %s [%s]" % (tp[0], tp[1], tp[2], Dicts.first_match(Dicts.sensor_types, int(tp[4]))))
                    for tp in pk_list]
        #print(dlg_list)
        dialog = wx.SingleChoiceDialog(None, "Pick a stored SSP", "Local DB", dlg_list)
        selection = dialog.ShowModal()
        dialog.Destroy()
        if selection != wx.ID_OK:
            ssp_db.disconnect()
            return

        # actually do the deletion
        try:
            ssp_db.delete_ssp_by_pk(pk_list[dialog.GetSelection()][0])

        except HyOError as e:
            msg = '%s' % e
            dlg = wx.MessageDialog(None, msg, "Local DB", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

    # Export

    def on_db_export_shp(self, event):
        log.info("exporting as shapefile")
        self._db_export(GdalAux.ogr_formats[b'ESRI Shapefile'])

    def on_db_export_kml(self, event):
        log.info("exporting as kml")
        self._db_export(GdalAux.ogr_formats[b'KML'])

    def on_db_export_csv(self, event):
        log.info("exporting as csv")
        self._db_export(GdalAux.ogr_formats[b'CSV'])

    @classmethod
    def _db_export(cls, ogr_format):
        ssp_db = SspDb()
        try:
            ssp_db.convert_ssp_view_to_ogr(ogr_format)

        except HyOError as e:
            msg = '%s' % e
            dlg = wx.MessageDialog(None, msg, "Local DB", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return
        Helper.explore_folder(ssp_db.export_folder)

    # Plot

    def on_db_plot_map_ssp(self, event):
        log.info("plot a map with all SSPs")
        ssp_db = SspDb()
        ssp_db.map_ssp_view()

    def on_db_plot_daily_ssp(self, event):
        log.info("plot daily SSPs")
        ssp_db = SspDb()
        ssp_db.create_daily_plots(save_fig=False)

    def on_db_save_daily_ssp(self, event):
        log.info("save daily SSPs")
        ssp_db = SspDb()
        ssp_db.create_daily_plots(save_fig=True)
        Helper.explore_folder(ssp_db.plots_folder)

    # ####### Tools ######

    def on_tools_geo_monitor(self, evt):
        """Display a map with the profile position"""
        if not self.geo_monitor:
            log.info("geo monitor not available")
            return

        # Request the current SVP cast from the clients prior. Take the first one that comes through.
        self.prj.km_listener.ssp = None
        for client in range(self.prj.s.client_list.num_clients):
            log.info("Testing client %s for position ..." % self.prj.s.client_list.clients[client].IP)
            self.prj.ssp_recipient_ip = self.prj.s.client_list.clients[client].IP
            self.prj.get_cast_from_sis()
            if self.prj.km_listener.ssp:
                log.info("... got SSP > valid client")
                break
            else:
                log.info("... not valid SSP > skip this client")

        if not self.prj.km_listener.ssp:
            msg = "Unable to run the geo-monitor since no casts were retrieved from SIS clients"
            dlg = wx.MessageDialog(None, msg, "Clients issue", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()  # Show it
            dlg.Destroy()
            return

        self.geo_monitor.OnShow()

    def on_tools_refraction_monitor(self, evt):
        """Display a refraction monitor"""
        if not self.ref_monitor:
            log.info("refraction monitor not available")
            return

        # Request the current SVP cast from the clients prior. Take the first one that comes through.
        self.prj.km_listener.ssp = None
        for client in range(self.prj.s.client_list.num_clients):
            log.info("Testing client %s for position ..." % self.prj.s.client_list.clients[client].IP)
            self.prj.ssp_recipient_ip = self.prj.s.client_list.clients[client].IP
            self.prj.get_cast_from_sis()
            if self.prj.km_listener.ssp:
                log.info("... got SSP > valid client")
                break
            else:
                log.info("... not valid SSP > skip this client")

        if not self.prj.km_listener.ssp:
            msg = "Unable to run the ref-monitor since no casts were retrieved from SIS clients"
            dlg = wx.MessageDialog(None, msg, "Clients issue", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()  # Show it
            dlg.Destroy()
            return

        log.info("got SIS ssp (samples %s)" % self.prj.km_listener.ssp.num_entries)

        if self.state == self.gui_state['CLOSED']:
            # Maybe when running in this state, the requested SVP is
            # loaded into the SVP Editor?  This is behavior is inconsistent
            # with other modes (OPEN, SERVER) where the profile is already loaded.
            # Perhaps should force user to open a profile from SIS?
            # Could then limit ability to launch refraction monitor from the
            # OPEN and SERVER states and have it disabled in the CLOSED state.
            log.info("we are CLOSED!")
            ssp = self.prj.km_listener.ssp.convert_ssp()
            if self.ref_monitor:
                self.ref_monitor.set_ssp(ssp)

        elif (self.state == self.gui_state['OPEN']) or (self.state == self.gui_state['SERVER']):
            if self.ref_monitor:
                self.ref_monitor.set_ssp(self.prj.ssp_data)

        self.ref_monitor.OnShow()

    def on_tools_info_settings(self, evt):
        self.set_viewer.OnShow()

    # ### SERVER ###

    def on_tools_server_start(self, event):
        """start the server mode"""

        dlg = wx.MessageDialog(self,
                               "Do you really want to start the Server Mode?\n\n"
                               "The Server Mode creates SSPs based on oceanographic models for SIS.\n"
                               "Thus, it is meant for use in transit, NOT for systematic seabed mapping.\n"
                               "This Mode will OVERWRITE the current SIS SSP.\n",
                               "Server Mode", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_CANCEL:
            return

        # - check and ask for draft
        if not self.prj.vessel_draft:
            self.get_transducer_draft()

            # if still not available, return
            if self.prj.vessel_draft is None:
                return
            else:  # store since it can change with updates
                self.prj.server.server_vessel_draft = self.prj.vessel_draft

        log.info("Starting server")

        # - start the server
        if self.prj.server.check_settings():
            self._update_state(self.gui_state["SERVER"])
            self.p.display_woa = True

            if self.prj.has_ssp_loaded:
                self.prj.clean_project()
                self.clear_app()

        else:
            dlg = wx.MessageDialog(self, "Unable to start the Server Mode", "Server Mode", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        self.prj.server.set_refraction_monitor(self.ref_monitor)
        threading.Thread(target=self.prj.server.run).start()

        # Now set up a timer for cast plot updates
        self.prj.server_timer = TimerThread(self.monitor_server, timing=1)
        self.prj.server_timer.start()

    def on_tools_server_send(self, e):
        log.info("forcing server to send profile NOW!")
        self.prj.server.force_send = True

    def monitor_server(self):
        if self.prj.server.stopped_on_error:
            self.prj.server.stop(by_thread=True)

            if (not self.prj.has_sippican_to_process) and (not self.prj.has_mvp_to_process):
                msg = "Server stopped with message: %s" % self.prj.server.error_message
                dlg = wx.MessageDialog(None, msg, "Acknowledge", wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()

            self.clear_app()

        else:
            if self.prj.server.update_plot:
                self._update_plot()
            self.prj.server.update_plot = False

    def on_tools_server_stop(self, e):
        dlg = wx.MessageDialog(self, "Do you really want to stop the server?", "Confirm Server Stop",
                               wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_CANCEL:
            return
        log.info("User instructed to stop the Server Mode")

        self.prj.server.stop()
        self.clear_app()

    def on_tools_server_log_metadata(self, event):
        """Activate the logging of the server metadata"""
        flag = self.ServerLogMetadata.IsChecked()

        if flag:
            self.prj.activate_server_logging_on_db()
        else:
            self.prj.deactivate_server_logging_on_db()

    # ### REF CAST ###

    def on_tools_set_reference_cast(self, evt):
        """set a reference cast"""
        log.info("set as reference cast:\n%s" % self.prj.ssp_data)

        self.prj.ssp_reference = copy.deepcopy(self.prj.ssp_data)
        self.prj.ssp_reference_filename = self.prj.filename

        self._update_plot()

    def on_tools_edit_reference_cast(self, evt):

        if not self.prj.ssp_reference:
            return

        if self.prj.has_ssp_loaded:
            msg = 'Must close currently loaded profile to edit the reference profile.  Proceed?'
            dlg = wx.MessageDialog(None, msg, "Question", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
            result = dlg.ShowModal()  # Show it
            dlg.Destroy()
            if result == wx.ID_CANCEL:
                return
            self.prj.clean_project()
            self.clear_app()

        self.prj.ssp_data = copy.deepcopy(self.prj.ssp_reference)
        self.prj.filename = self.prj.ssp_reference_filename
        self.prj.s.filename_prefix = os.path.splitext(self.prj.filename)[0]

        self.prj.ssp_woa, self.prj.ssp_woa_min, self.prj.ssp_woa_max = self.prj.woa09_atlas.query(
            self.prj.ssp_data.latitude,
            self.prj.ssp_data.longitude,
            self.prj.ssp_data.date_time)
        self.prj.has_ssp_loaded = True

        self.prj.surface_speed_applied = False
        self.prj.ssp_applied_depth = 0

        self._update_state(self.gui_state['OPEN'])
        self._update_plot()
        self.status_message = "Loaded %s" % self.prj.filename

    def on_tools_clear_reference_cast(self, evt):
        self.prj.ssp_reference = None
        self.prj.ssp_reference_filename = None
        self._update_plot()

    # ####### HELP ######

    def on_help_manual(self, event):
        """
        open manual
        """
        manual_path = os.path.abspath(os.path.join(self.here, os.path.pardir, "docs", "manual.pdf"))
        if not os.path.isfile(manual_path):
            log.warning("missing manual at: %s" % manual_path)
            return
        log.info("open manual: %s" % manual_path)
        Helper.explore_folder(manual_path)

    def on_help_about(self, e):
        """Info about the application"""
        current_year = dt.datetime.now().strftime("%Y")
        dlg = wx.AboutDialogInfo()
        dlg.SetName("SSP Manager")
        dlg.SetVersion(self.version)
        dlg.SetLicense(self.license)
        dlg.SetIcon(wx.Icon(os.path.join(self.here, "ccom.png"), wx.BITMAP_TYPE_PNG))
        dlg.SetDescription("SSP Manager processes XBT/SVP/CTD data for being used by \n"
                           "acoustic systems.\n\n"
                           "This work is/has been funded by:\n"
                           " - NOAA grant NA10NOS4000073\n"
                           " - NSF grant 1150574\n\n"
                           "For bugs and unsupported formats, please send an email \n"
                           "(with attached the data files to reproduce and troubleshoot \n"
                           "the issue!) to:\n"
                           " - hydroffice.ssp_manager@ccom.unh.edu\n\n"
                           "For code contributions and general comments, write to:\n"
                           " - gmasetti@ccom.unh.edu\n"
                           " - brc@ccom.unh.edu\n"
                           " - matthew.wilson@noaa.gov")
        dlg.SetCopyright("%s (C) UNH/CCOM" % current_year)
        wx.AboutBox(dlg)

    ################################################
    ###               USER DIALOGS               ###

    def get_transducer_draft(self):
        """Ask user for transducer draft"""
        if self.prj.km_listener.xyz88:
            self.prj.vessel_draft = self.prj.km_listener.xyz88.transducer_draft
            return

        dlg = wx.TextEntryDialog(None, 'Enter the transducer draft', 'Transducer draft')
        if dlg.ShowModal() == wx.ID_CANCEL:
            self.prj.vessel_draft = None
            dlg.Destroy()
            return

        dlg_value = dlg.GetValue()
        dlg.Destroy()

        try:
            self.prj.vessel_draft = float(dlg_value)

        except ValueError:
            msg = "Invalid draft entry: %s" % dlg_value
            dlg = wx.MessageDialog(None, msg, "Invalid value", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            self.prj.vessel_draft = None
            return

    def get_position(self):
        """Ask user for position, if not available"""
        latitude = None
        longitude = None

        if self.prj.km_listener.nav:
            msg = "Geographic location required for pressure/depth conversion and atlas lookup.\n" \
                  "Use geographic position from SIS?\nChoose 'no' to enter position manually."
            dlg = wx.MessageDialog(None, msg, "Question", wx.YES | wx.NO | wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()

            if result == wx.ID_YES:
                latitude = self.prj.km_listener.nav.latitude
                longitude = self.prj.km_listener.nav.longitude
                msg = 'User set cast position %lf %lf from SIS input' % (latitude, longitude)
                log.info(msg)

            elif result == wx.ID_NO:
                latitude = None
                longitude = None

        if not latitude or not longitude:
            # latitude
            while True:
                dlg = wx.TextEntryDialog(None, "Geographic location required for pressure/depth conversion and atlas "
                                               "lookup.Enter latitude as signed decimal degrees (-10.123).",
                                         "Latitude")
                if dlg.ShowModal() == wx.ID_CANCEL:
                    dlg.Destroy()
                    return [None, None]
                else:
                    try:
                        latitude = float(dlg.GetValue())
                        dlg.Destroy()
                        break

                    except ValueError:
                        pass

            # longitude
            while True:
                dlg = wx.TextEntryDialog(None, "Geographic location required for pressure/depth conversion and atlas "
                                               "lookup. Enter longitude as signed decimal degrees (-50.123).",
                                         "Longitude")
                if dlg.ShowModal() == wx.ID_CANCEL:
                    dlg.Destroy()
                    return [None, None]
                else:
                    try:
                        longitude = float(dlg.GetValue())
                        dlg.Destroy()
                        break

                    except ValueError:
                        pass

            msg = 'Manual user input position: %lf %lf' % (latitude, longitude)
            log.info(msg)

        return [latitude, longitude]

    def get_date(self):
        """Ask user for date, if not available"""

        # SIS specific
        if self.prj.km_listener.nav:
            msg = "Date required for database lookup.\nUse date from SIS?\nChoose 'no' to enter date manually."
            dlg = wx.MessageDialog(None, msg, "Question", wx.YES | wx.NO | wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()

            if result == wx.ID_YES:
                date = self.prj.km_listener.nav.dg_time
                if date:
                    msg = 'Cast date %s from SIS input' % date
                    log.info(msg)
                    return date
                else:
                    msg = 'Invalid date in SIS datagram'
                    log.info(msg)

        # date from the machine clock
        msg = "Date required for database lookup.\nUse UTC date from this machine?\nChoose 'no' to enter date manually."
        dlg = wx.MessageDialog(None, msg, "Question", wx.YES | wx.NO | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_YES:
            date = dt.datetime.utcnow()
            msg = 'User set cast date %s from computer clock' % date
            log.info(msg)
            return date

        # user input date / time
        while True:
            msg = "Date required for database lookup.\nPlease enter date (YYYY-MM-DD)."
            dlg = wx.TextEntryDialog(None, msg, 'Date')
            if dlg.ShowModal() == wx.ID_CANCEL:
                return None
            else:
                date_string = dlg.GetValue()
                dlg.Destroy()
                try:
                    dt.datetime(int(date_string[0:4]), int(date_string[5:7]), int(date_string[8:10]))
                    break
                except ValueError:
                    continue

        while True:
            msg = "Date required for database lookup.\nPlease enter time (HH:MM:SS)."
            dlg = wx.TextEntryDialog(None, msg, 'Enter Date')
            if dlg.ShowModal() == wx.ID_CANCEL:
                return None
            else:
                cast_time = dlg.GetValue()
                dlg.Destroy()
                try:
                    date = dt.datetime(int(date_string[0:4]), int(date_string[5:7]), int(date_string[8:10]),
                                       int(cast_time[0:2]), int(cast_time[3:5]), int(cast_time[6:8]), 0)
                    msg = 'User input cast date %s' % date
                    log.info(msg)
                    return date
                except ValueError:
                    pass

    # ###############################################
    # ###                  DEBUGGING              ###

    def _update_state(self, state):

        for item in svpeditor_ui.MENUS_ALL:  # Enable ALL the menu items
            self.GetMenuBar().FindItemById(item).Enable(True)

        # selectively disable some based on the state
        if state == self.gui_state["CLOSED"]:
            for item in svpeditor_ui.MENUS_DISABLED_ON_CLOSED:
                self.GetMenuBar().FindItemById(item).Enable(False)
            if self.ref_monitor:
                self.ref_monitor.set_ssp(None)
                self.ref_monitor.hide()

        elif state == self.gui_state["OPEN"]:
            for item in svpeditor_ui.MENUS_DISABLED_ON_OPEN:
                self.GetMenuBar().FindItemById(item).Enable(False)
            if self.prj.ssp_data.sensor_type != Dicts.sensor_types["XBT"]:
                self.ProcessLoadSal.Enable(False)
            if self.prj.ssp_data.sensor_type != Dicts.sensor_types["XSV"] \
                    and self.prj.ssp_data.sensor_type != Dicts.sensor_types["SVP"]:
                self.ProcessLoadTempSal.Enable(False)
            if self.ref_monitor:
                self.ref_monitor.set_ssp(self.prj.ssp_data)

        elif state == self.gui_state["SERVER"]:
            for item in svpeditor_ui.MENUS_DISABLED_ON_SERVER:
                self.GetMenuBar().FindItemById(item).Enable(False)
            if self.ref_monitor:
                self.ref_monitor.set_ssp(None)

        else:
            raise SspError("Passed wrong state type: %s is %s" % (state, type(state)))

        self.state = state

    def _update_status(self):
        """Provide info from SIS to the user through status bar"""

        self.frame_statusbar.SetStatusText(self.status_message, 0)

        # in case that the SIS listener is absent
        if self.prj.km_listener is None:
            self.frame_statusbar.SetStatusText("Disabled SIS listener", 1)
            return

        sis_info_str = str()

        if self.prj.km_listener.nav is not None:
            # time stamp
            if self.prj.km_listener.nav.dg_time is not None:
                sis_info_str = "%s, " % (self.prj.km_listener.nav.dg_time.strftime("%Y-%m-%d %H:%M:%S"))

            else:
                sis_info_str = "NA, "

            # position
            if (self.prj.km_listener.nav.latitude is not None) and \
                    (self.prj.km_listener.nav.longitude is not None):

                latitude = self.prj.km_listener.nav.latitude
                if latitude >= 0:
                    letter = "N"
                else:
                    letter = "S"
                lat_min = float(60 * math.fabs(latitude - int(latitude)))
                lat_str = "%02d\N{DEGREE SIGN}%7.3f'%s" % (int(math.fabs(latitude)), lat_min, letter)

                longitude = self.prj.km_listener.nav.longitude
                if longitude < 0:
                    letter = "W"
                else:
                    letter = "E"
                lon_min = float(60 * math.fabs(longitude - int(longitude)))
                lon_str = "%03d\N{DEGREE SIGN}%7.3f'%s" % (int(math.fabs(longitude)), lon_min, letter)

                sis_info_str += "(%s, %s), " % (lat_str, lon_str)

            else:
                sis_info_str += "(NA, NA), "

        if self.prj.km_listener.xyz88 is not None:
            if self.prj.km_listener.xyz88.sound_speed is not None:
                sis_info_str += '%.1f m/s, ' % self.prj.km_listener.xyz88.sound_speed
                self.prj.surface_sound_speed = self.prj.km_listener.xyz88.sound_speed
                self.prj.vessel_draft = self.prj.km_listener.xyz88.transducer_draft
            else:
                sis_info_str += 'NA m/s, '
                self.prj.surface_sound_speed = None
                self.prj.vessel_draft = None

            if (self.prj.km_listener.xyz88.number_beams is not None) and \
                    (self.prj.km_listener.xyz88.depth is not None) and \
                    (self.prj.km_listener.xyz88.transducer_draft is not None) and \
                    (self.prj.km_listener.xyz88.detection_information is not None):

                mean_depth = 0.0
                depth_count = 0
                for beam in range(self.prj.km_listener.xyz88.number_beams):
                    if int(self.prj.km_listener.xyz88.detection_information[beam]) & 0x80 != 0:
                        # We skip beams without valid detections
                        continue
                    mean_depth = mean_depth + self.prj.km_listener.xyz88.depth[beam]
                    depth_count += 1

                if depth_count > 0:
                    mean_depth = mean_depth / depth_count + self.prj.km_listener.xyz88.transducer_draft
                    sis_info_str += '%.1f m' % mean_depth
                    self.prj.mean_depth = mean_depth
                else:
                    sis_info_str += 'NA m'
                    self.prj.mean_depth = None
        else:
            sis_info_str += 'XYZ88 NA [Pinging?]'
            self.prj.mean_depth = None
            self.prj.surface_sound_speed = None
            self.prj.vessel_draft = None

        self.frame_statusbar.SetStatusText(sis_info_str, 1)
