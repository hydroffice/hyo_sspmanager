from __future__ import absolute_import, division, print_function, unicode_literals

import datetime as dt

import wx

from . import settingsviewer_ui
from ..helper import SspError
from ...base.timerthread import TimerThread


class SettingsViewer(settingsviewer_ui.SettingsViewerBase):
    def __init__(self, ssp_settings, verbose=True):
        settingsviewer_ui.SettingsViewerBase.__init__(self, None, -1, "")
        self.verbose = verbose
        self.ssp_settings = ssp_settings
        self.display_timer = None

        self.Bind(wx.EVT_CLOSE, self.on_hide)

        self.control = wx.TextCtrl(self, size=(400, 600), style=wx.TE_MULTILINE)
        self.control.SetEditable(False)
        small_font = wx.Font(8, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Consolas')
        self.control.SetFont(small_font)
        self.GetSizer().Add(self.control, 1, wx.EXPAND)
        self.GetSizer().Fit(self)

        self.Layout()

    def on_hide(self, evt):
        self.print_info("hidden")
        self.hide()

    def hide(self):
        if self.display_timer.is_alive():
            self.display_timer.stop()
        self.Hide()

    def OnShow(self):
        # since a thread cannot re-run, we create a thread each time
        self.display_timer = TimerThread(self.update, timing=5)
        self.display_timer.start()
        self.Show()

    def OnExit(self):
        if self.display_timer:
            if self.display_timer.is_alive():
                self.display_timer.stop()
        self.Destroy()  # Close the frame.

    def update(self):
        self.control.Clear()
        self.control.AppendText("%s" % self.ssp_settings)

    def print_info(self, debug_info):
        if not self.verbose:
            return
        print("SET > %s" % debug_info)

