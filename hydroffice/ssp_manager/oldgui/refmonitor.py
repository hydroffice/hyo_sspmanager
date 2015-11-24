from __future__ import absolute_import, division, print_function, unicode_literals

import math
import numpy as np
import logging

log = logging.getLogger(__name__)

from matplotlib import rcParams
rcParams.update(
    {
        'font.family': 'sans-serif',
        'font.size': 7
    }
)
import wx
from . import wxmpl

from . import refmonitor_ui
from ..drivers.km import kmio
from ..helper import SspError
from ..ssp_dicts import Dicts
from hydroffice.base.timerthread import TimerThread


class RefMonitor(refmonitor_ui.RefMonitorBase):
    def __init__(self, km_listener):
        refmonitor_ui.RefMonitorBase.__init__(self, None, -1, "")
        self.SetBackgroundColour(wx.WHITE)

        self.display_timer = None
        self.km_listener = km_listener
        if not isinstance(km_listener, kmio.KmIO):
            if not km_listener:
                log.info("SIS listener not active")
                return
            raise SspError("passed wrong instance of listener: %s" % type(km_listener))

        self.Bind(wx.EVT_CLOSE, self.OnHide)

        self.plots = wxmpl.PlotPanel(self, -1)
        self.plots.set_location(False)
        self.plots.set_crosshairs(False)
        self.plots.set_selection(True)
        self.plots.set_zoom(False)
        self.bathy_axes = self.plots.get_figure().add_subplot(211)
        self.bathy_axes.invert_yaxis()
        self.bathy_axes.set_title("Compared Ping Bathymetry [m]")
        self.correction_axes = self.plots.get_figure().add_subplot(212)
        self.correction_axes.invert_yaxis()
        self.correction_axes.set_title("Resulting Bathymetric Corrections [m]")

        self.GetSizer().Add(self.plots, 1, wx.EXPAND)
        self.sliderLabel = wx.StaticText(self, label="Profile Correction [dm/s]", style=wx.ALIGN_CENTRE)
        self.GetSizer().Add(self.sliderLabel, 0, wx.EXPAND | wx.ALIGN_CENTER | wx.ALL, border=2)
        self.GetSizer().Add(self.SVCorrectorSlider, 0, wx.EXPAND, 0)
        self.GetSizer().Fit(self)

        self.Layout()

        self.ssp = None
        self.ssp_corrected = 0
        self.ssp_corrector = 0
        self.ssp_equiv = 0

        self.pause = False

        # init to hold 1000 beams
        self.depth = np.zeros(1000)
        self.across = np.zeros(1000)
        self.angle = np.zeros(1000)
        self.range = np.zeros(1000)
        self.depth_corrected = np.zeros(1000)
        self.across_corrected = np.zeros(1000)
        self.depth_correction = np.zeros(1000)
        self.across_correction = np.zeros(1000)

        self.avg_depth = 0

    def pause_corrections(self):
        if not self.km_listener:
            return
        if self.display_timer:
            if self.display_timer.is_alive():
                self.display_timer.stop()
                self.pause = True

    def resume_corrections(self):
        if not self.km_listener:
            return
        if self.display_timer:
            self.display_timer = TimerThread(self.update, timing=3)
            self.display_timer.start()
            self.pause = False

    def set_ssp(self, ssp):
        self.ssp = ssp
        self.update_plots()

    def on_ssp_scroll(self, evt):
        self.ssp_corrector = float(self.SVCorrectorSlider.GetValue()) / 10.0
        self.update_plots()

    def get_mean_depth(self):
        return float(self.avg_depth)

    def get_corrector(self):
        return float(self.ssp_corrector)

    def set_corrector(self, val):
        self.SVCorrectorSlider.SetValue(int(val * 10.0))
        self.ssp_corrector = val

    def OnHide(self, evt):
        self.hide()
        evt.Skip()

    def hide(self):
        if self.km_listener:
            if self.display_timer:
                self.display_timer.stop()
        self.Hide()

    def OnShow(self):
        # since a thread cannot re-run, we create a thread each time
        self.display_timer = TimerThread(self.update, timing=3)
        self.display_timer.start()
        self.Show()

    def OnExit(self):
        if self.km_listener:
            if self.display_timer:
                if self.display_timer.is_alive():
                    self.display_timer.stop()
        self.Destroy()  # Close the frame.

    def update(self):

        string0 = "SSP equiv. %.1f, corr. %.1f" % (self.ssp_equiv, self.ssp_corrected)

        if self.km_listener.xyz88:
            string1 = "%s, " % (self.km_listener.xyz88.dg_time.strftime("%Y-%m-%d %H:%M:%S"))
            string1 += "%.1f m/s" % self.km_listener.xyz88.sound_speed
        else:
            string1 = "0000-00-00 00:00:00, 0.0 m/s"

        self.RefractionMonitorFrame_statusbar.SetStatusText(string0, 0)
        self.RefractionMonitorFrame_statusbar.SetStatusText(string1, 1)

        self.update_plots()

    def update_plots(self):
        """update both bathymetry and correction plots"""
        if not self.km_listener or self.pause:
            return

        # clear plots
        self.bathy_axes.cla()
        self.correction_axes.cla()

        if self.km_listener.xyz88 is None:
            log.info("missing XYZ88 datagram")
            return
        num_beams = self.km_listener.xyz88.number_beams
        temp_depth = self.km_listener.xyz88.depth.copy()
        temp_across = self.km_listener.xyz88.across.copy()
        temp_flags = self.km_listener.xyz88.detection_information.copy()
        transducer_draft = self.km_listener.xyz88.transducer_draft
        num_detections = self.km_listener.xyz88.number_detections
        if self.depth.size < num_detections:
            self.depth.resize(num_detections)
            self.across.resize(num_detections)
            self.angle.resize(num_detections)
            self.range.resize(num_detections)
            self.depth_corrected.resize(num_detections)
            self.across_corrected.resize(num_detections)
            self.depth_correction.resize(num_detections)
            self.across_correction.resize(num_detections)
        self.depth[:] = 0
        self.across[:] = 0
        self.angle[:] = 0
        self.range[:] = 0
        self.depth_corrected[:] = 0
        self.across_corrected[:] = 0
        self.depth_correction[:] = 0
        self.across_correction[:] = 0

        count = 0
        for beam in range(num_beams):
            if int(temp_flags[beam]) & 0x80 != 0:
                # We skip beams without valid detections
                continue

            self.depth[count] = temp_depth[beam]
            self.across[count] = temp_across[beam]
            # Hmmmm, angle and range need to be uncorrected for S1Y and S1Z
            self.angle[count] = math.atan(self.across[count] / self.depth[count])
            self.range[count] = math.sqrt(self.depth[count] * self.depth[count] +
                                          self.across[count] * self.across[count])
            count += 1

        self.avg_depth = np.mean(self.depth[0:num_detections])

        if self.avg_depth == 0:
            return

        # Do some plotting!
        self.bathy_axes.plot(self.across[0:num_detections], self.depth[0:num_detections], 'r')
        self.bathy_axes.set_title("Compared Ping Bathymetry [m]")
        self.correction_axes.set_title("Resulting Bathymetric Corrections [m]")
        if not self.ssp or not self.km_listener.ssp or self.pause:
            self.plots.draw()
            return

        # Resample the sound speed profile into 1-m bins and then compute mean sound speed
        # over the bins (since bin size is constant, mean sound speed is the harmonic sound speed)
        num_bins = int(self.avg_depth)
        depth_interp = np.linspace(transducer_draft, self.avg_depth + transducer_draft, num_bins)

        # Now get the equivalent SVP for the current profile being used to reduce the data
        sv_interp = np.interp(depth_interp, self.km_listener.ssp.depth, self.km_listener.ssp.speed)
        self.ssp_equiv = np.mean(sv_interp)

        # Now get the equivalent SVP for the proposed replacement profile
        good_pts = (self.ssp.data[Dicts.idx['flag'], :] == 0)
        sv_interp = np.interp(depth_interp, self.ssp.data[Dicts.idx['depth'], good_pts],
                              self.ssp.data[Dicts.idx['speed'], good_pts])
        sv_equiv2 = np.mean(sv_interp)

        # The proposed "corrected" SVP used the equivalent sv from the
        # candidate profile AND applies a user specified corrector term from
        # the slider bar
        self.ssp_corrected = sv_equiv2 + self.ssp_corrector
        log.info("compare: original %6.1f, corrected %6.1f" % (self.ssp_equiv, self.ssp_corrected))

        if int(self.ssp_equiv * 10.0) == int(self.ssp_corrected * 10.0):
            for count in range(num_detections):
                self.depth_corrected[count] = self.depth[count]
                self.depth_correction[count] = 0.0
                self.across_corrected[count] = self.across[count]
                self.across_correction[count] = 0.0
        else:
            # Now do corrections
            for count in range(num_detections):
                angle_new = math.asin(math.sin(self.angle[count]) * self.ssp_corrected / self.ssp_equiv)
                range_new = self.range[count] * self.ssp_corrected / self.ssp_equiv
                self.depth_corrected[count] = range_new * math.cos(angle_new)
                self.depth_correction[count] = self.depth_corrected[count] - self.depth[count]
                self.across_corrected[count] = range_new * math.sin(angle_new)
                self.across_correction[count] = self.across_corrected[count] - self.across[count]

        self.bathy_axes.hold(True)
        self.bathy_axes.plot(self.across_corrected[0:num_detections], self.depth_corrected[0:num_detections], 'g')
        self.correction_axes.plot(self.across_corrected[0:num_detections], self.depth_correction[0:num_detections], 'b')

        self.plots.draw()
