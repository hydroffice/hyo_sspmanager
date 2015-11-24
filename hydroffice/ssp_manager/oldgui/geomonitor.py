from __future__ import absolute_import, division, print_function, unicode_literals

import datetime as dt

import wx
from . import wxmpl
from pylab import *
from mpl_toolkits.basemap import Basemap
import logging

log = logging.getLogger(__name__)

from . import geomonitor_ui
from ..drivers.km import kmio
from ..helper import SspError
from hydroffice.base.timerthread import TimerThread


class GeoMonitor(geomonitor_ui.GeoMonitorBase):
    def __init__(self, km_listener):
        geomonitor_ui.GeoMonitorBase.__init__(self, None, -1, "")

        self.display_timer = None  # a timer for display updates
        self.km_listener = km_listener
        if not isinstance(km_listener, kmio.KmIO):
            if not km_listener:
                log.info("SIS listener not active")
                return
            raise SspError("passed wrong instance of listener: %s" % type(km_listener))

        self.selection_mode = "Zoom"

        self.Bind(wx.EVT_CLOSE, self.on_hide)

        # init plot canvas
        self.plots = wxmpl.PlotPanel(self, -1)
        self.plots.set_location(False)
        self.plots.set_crosshairs(False)
        self.plots.set_selection(False)
        self.plots.set_zoom(False)
        self.map_axes = self.plots.get_figure().add_subplot(111)
        self.map_axes.hold(True)
        self.GetSizer().Add(self.plots, 1, wx.EXPAND)
        self.GetSizer().Fit(self)

        # register to receive wxPython SelectionEvents from a PlotPanel or PlotFrame
        wxmpl.EVT_SELECTION(self, self.plots.GetId(), self._on_selection)

        self.Layout()

        self.last_latitude = None
        self.last_longitude = None
        self.last_ssp = None
        self.last_ssp_time = None
        self.latitude = []
        self.longitude = []
        self.ssp = []
        self.view_min_lat = -90
        self.view_max_lat = 90
        self.lat_step = None
        self.view_min_lon = -180
        self.view_max_lon = 180
        self.lon_step = None
        self.get_lat_lon_steps()
        self.last_ping_time = dt.datetime.utcnow()
        self.is_zoomed = False

        self.m = Basemap(projection='mill', lat_ts=10, llcrnrlon=-180, urcrnrlon=180,
                         llcrnrlat=-90, urcrnrlat=90, resolution='c')
        self.m.drawcoastlines(ax=self.map_axes)
        self.m.fillcontinents(ax=self.map_axes, color='coral', lake_color='aqua')
        self.m.drawmapboundary(ax=self.map_axes, fill_color='aqua')
        self.m.drawparallels(np.arange(-90., 120., 30.), labels=[1, 0, 0, 0], ax=self.map_axes)
        self.m.drawmeridians(np.arange(-180., 180., 60.), labels=[0, 0, 0, 1], ax=self.map_axes)
        self.view_min_x, self.view_min_y = self.m(-180, -90, inverse=True)
        self.view_max_x, self.view_max_y = self.m(180, 90, inverse=True)

    def _on_selection(self, evt):
        x1, y1 = evt.x1data, evt.y1data
        x2, y2 = evt.x2data, evt.y2data

        log.info("got zoom coords %s %s %s %s" % (x1, y1, x2, y2))

        if self.selection_mode == "Zoom":
            # Deal with case of zooming in
            if evt.axes == self.map_axes:
                self.view_min_x = min(x1, x2)
                self.view_max_x = max(x1, x2)
                self.view_min_y = min(y1, y2)
                self.view_max_y = max(y1, y2)
                self.view_min_lon, self.view_min_lat = self.m(self.view_min_x, self.view_min_y, inverse=True)
                self.view_max_lon, self.view_max_lat = self.m(self.view_max_x, self.view_max_y, inverse=True)
                self.get_lat_lon_steps()
                self.m = Basemap(projection='mill', lat_ts=10, resolution='c',
                                 llcrnrlon=self.view_min_lon, urcrnrlon=self.view_max_lon,
                                 llcrnrlat=self.view_min_lat, urcrnrlat=self.view_max_lat)
                self.is_zoomed = True
            else:
                log.info("unknown axes")
            self.update_plots()
        else:
            log.info("nothing to do")

    def on_hide(self, evt):
        log.info("hidden")
        self.hide()

    def hide(self):
        if self.display_timer.is_alive():
            self.display_timer.stop()
        self.Hide()

    def OnShow(self):
        # since a thread cannot re-run, we create a thread each time
        self.display_timer = TimerThread(self.update, timing=3)
        self.display_timer.start()
        self.Show()

    def OnExit(self):
        if self.display_timer:
            if self.display_timer.is_alive():
                self.display_timer.stop()
        self.Destroy()  # Close the frame.

    def update(self):
        if not self.km_listener.nav:
            empty_str = "0000-00-00 00:00:00, 0.0 m/s"
            self.GeographicMonitorFrame_statusbar.SetStatusText(empty_str, 1)
            return

        if not self.km_listener.xyz88 or not self.km_listener.nav:
            empty_str = "0000-00-00 00:00:00, 0.0 m/s"
            self.GeographicMonitorFrame_statusbar.SetStatusText(empty_str, 1)
            return

        self.last_latitude = self.km_listener.nav.latitude
        self.last_longitude = self.km_listener.nav.longitude
        log.info("got position: %s, %s" % (self.last_latitude, self.last_longitude))
        self.latitude.append(self.last_latitude)
        self.longitude.append(self.last_longitude)
        msg_str = "%s, " % (self.km_listener.xyz88.dg_time.strftime("%Y-%m-%d %H:%M:%S"))
        msg_str += "%.1f m/s" % self.km_listener.xyz88.sound_speed
        self.GeographicMonitorFrame_statusbar.SetStatusText(msg_str, 1)

        if self.km_listener.xyz88.dg_time == self.last_ping_time:
            log.info("got same ping times!")
            return
        self.last_ssp_time = self.km_listener.xyz88.dg_time
        self.last_ssp = self.km_listener.xyz88.sound_speed
        self.ssp.append(self.last_ssp)
        log.info("got (%s, %s) -> %s" % (self.last_latitude, self.last_longitude, self.last_ssp))
        self.last_ping_time = self.km_listener.xyz88.dg_time
        if self.display_timer.is_alive():
            self.update_plots()

    def get_lat_lon_steps(self):
        lat_range = math.fabs(self.view_max_lat - self.view_min_lat)
        self.lat_step = int(lat_range / 10.0)
        lon_range = math.fabs(self.view_max_lon - self.view_min_lon)
        self.lon_step = int(lon_range / 10.0)
        log.info("got lat/lon steps %s %s" % (self.lat_step, self.lon_step))

    def update_plots(self):
        log.info("updating plots")

        try:
            self.map_axes.cla()
            self.map_axes.hold(True)
            self.m.drawcoastlines(ax=self.map_axes)
            self.m.fillcontinents(ax=self.map_axes, color='coral', lake_color='aqua')
            self.m.drawmapboundary(ax=self.map_axes, fill_color='aqua')
            self.m.drawparallels(np.arange(-90., 120., self.lat_step),
                                 labels=[1, 0, 0, 0], ax=self.map_axes)
            self.m.drawmeridians(np.arange(-180., 180., self.lon_step),
                                 labels=[0, 0, 0, 1], ax=self.map_axes)
        except:
            log.info("failure in updating")

        x, y = self.m(self.longitude, self.latitude)
        log.info("got projected coords: %s %s from: %s %s" % (x, y, self.longitude, self.latitude))
        self.map_axes.plot(x, y, 'r+')
        self.plots.draw()
