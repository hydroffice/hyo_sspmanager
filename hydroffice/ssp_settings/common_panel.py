from __future__ import absolute_import, division, print_function, unicode_literals

import wx
from wx.lib import intctrl
import os
import logging

log = logging.getLogger(__name__)

from hydroffice.ssp.settings.settings import Settings
from hydroffice.ssp.settings.db import SettingsDb, DbSettingsError


class CommonPanel(wx.Panel):
    def __init__(self, parent_frame, db, *args, **kwargs):
        """ This panel provides user interaction to common settings """
        super(CommonPanel, self).__init__(*args, **kwargs)

        # Store an handle to the Settings DB
        self.parent_frame = parent_frame
        self.settings_db = db
        self.selected_profile_item = 0

        # Main box
        main_box = wx.StaticBox(self)
        main_box_szr = wx.StaticBoxSizer(main_box, wx.VERTICAL)

        #
        # RX Waiting Time
        #
        rx_wait_time_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        rx_wait_time_txt_szr = wx.BoxSizer(wx.VERTICAL)
        rx_wait_time_txt = wx.StaticText(self, label="RX Maximum Waiting Time", style=wx.ALIGN_CENTER)
        rx_wait_time_txt.Wrap(width=150)
        rx_wait_time_txt_szr.AddStretchSpacer()
        rx_wait_time_txt_szr.Add(rx_wait_time_txt, 0, wx.EXPAND)
        rx_wait_time_txt_szr.AddStretchSpacer()

        # integer control
        self.rx_wait_time = intctrl.IntCtrl(main_box, min=0, max=999999, limited=True)
        self.rx_wait_time.Bind(wx.EVT_TEXT, self.on_wait_time_change)

        # buttons
        lst_rx_wait_time_szr = wx.BoxSizer(wx.VERTICAL)
        rx_wait_time_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        rx_wait_time_btn.SetToolTipString("Apply the new value")
        rx_wait_time_btn.Bind(wx.EVT_BUTTON, self.on_apply_rx_wait_time)
        lst_rx_wait_time_szr.Add(rx_wait_time_btn, 0, wx.ALIGN_RIGHT)

        rx_wait_time_szr.Add(rx_wait_time_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        rx_wait_time_szr.Add(self.rx_wait_time, 2, wx.EXPAND | wx.ALL, 5)
        rx_wait_time_szr.Add(lst_rx_wait_time_szr, 0, wx.EXPAND | wx.ALL, 5)

        #
        # WOA Path
        #
        woa_path_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        woa_path_txt_szr = wx.BoxSizer(wx.VERTICAL)
        woa_path_txt = wx.StaticText(self, label="Path to WOA DB", style=wx.ALIGN_CENTER)
        woa_path_txt.Wrap(width=150)
        woa_path_txt_szr.AddStretchSpacer()
        woa_path_txt_szr.Add(woa_path_txt, 0, wx.EXPAND)
        woa_path_txt_szr.AddStretchSpacer()

        # directory text ctrl
        self.woa_path = wx.TextCtrl(main_box, style=wx.TE_BESTWRAP)
        self.woa_path.Bind(wx.EVT_TEXT, self.on_woa_path_change)

        # buttons
        lst_woa_path_szr = wx.BoxSizer(wx.VERTICAL)
        self.woa_path_browse_btn = wx.DirPickerCtrl(main_box, style=wx.DIRP_DIR_MUST_EXIST, size=(80, -1))
        self.woa_path_browse_btn.SetToolTipString("Browse to the WOA DB folder")
        self.woa_path_browse_btn.Bind(wx.EVT_DIRPICKER_CHANGED, self.on_picked_woa_path)
        lst_woa_path_szr.Add(self.woa_path_browse_btn, 0, wx.ALIGN_RIGHT)
        woa_path_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        woa_path_btn.SetToolTipString("Apply the new value")
        woa_path_btn.Bind(wx.EVT_BUTTON, self.on_apply_woa_path)
        lst_woa_path_szr.Add(woa_path_btn, 0, wx.ALIGN_RIGHT)

        woa_path_szr.Add(woa_path_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        woa_path_szr.Add(self.woa_path, 2, wx.EXPAND | wx.ALL, 5)
        woa_path_szr.Add(lst_woa_path_szr, 0, wx.EXPAND | wx.ALL, 5)

        #
        # SSP up or down cast
        #
        ssp_up_or_down_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        ssp_up_or_down_txt_szr = wx.BoxSizer(wx.VERTICAL)
        ssp_up_or_down_txt = wx.StaticText(self, label="SSP Processing Direction", style=wx.ALIGN_CENTER)
        ssp_up_or_down_txt.Wrap(width=150)
        ssp_up_or_down_txt_szr.AddStretchSpacer()
        ssp_up_or_down_txt_szr.Add(ssp_up_or_down_txt, 0, wx.EXPAND)
        ssp_up_or_down_txt_szr.AddStretchSpacer()

        # choice control
        source_choices = ["up", "down"]
        self.ssp_up_or_down = wx.ComboBox(main_box, choices=source_choices) #, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.ssp_up_or_down.Bind(wx.EVT_COMBOBOX, self.on_ssp_up_or_down_change)

        # buttons
        lst_ssp_up_or_down_szr = wx.BoxSizer(wx.VERTICAL)
        ssp_up_or_down_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        ssp_up_or_down_btn.SetToolTipString("Apply the new value")
        ssp_up_or_down_btn.Bind(wx.EVT_BUTTON, self.on_apply_ssp_up_or_down)
        lst_ssp_up_or_down_szr.Add(ssp_up_or_down_btn, 0, wx.ALIGN_RIGHT)

        ssp_up_or_down_szr.Add(ssp_up_or_down_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        ssp_up_or_down_szr.Add(self.ssp_up_or_down, 2, wx.EXPAND | wx.ALL, 5)
        ssp_up_or_down_szr.Add(lst_ssp_up_or_down_szr, 0, wx.EXPAND | wx.ALL, 5)

        #
        # Add rows to the main box
        #
        main_box_szr.Add(rx_wait_time_szr, 0, wx.EXPAND)
        main_box_szr.Add(woa_path_szr, 0, wx.EXPAND)
        main_box_szr.Add(ssp_up_or_down_szr, 0, wx.EXPAND)

        # Set the main box sizer and fit
        self.SetSizer(main_box_szr)
        self.Layout()

        # Update the data content
        self.update_data()

    def update_data(self, event=None):
        """ Update the data from the database """
        self.rx_wait_time.ChangeValue(self.settings_db.rx_max_wait_time)
        self.rx_wait_time.SetColors(default_color=wx.BLACK)

        if self.settings_db.woa_path is None:
            self.woa_path.ChangeValue("")
        else:
            self.woa_path.ChangeValue(self.settings_db.woa_path)
        self.woa_path.SetForegroundColour(wx.BLACK)

        self.ssp_up_or_down.SetSelection(
            self.ssp_up_or_down.FindString(self.settings_db.ssp_up_or_down))
        self.ssp_up_or_down.SetOwnBackgroundColour(wx.WHITE)

    # RX Waiting time

    def on_wait_time_change(self, event):
        """ Method called when the waiting time is changed """
        log.debug("Changed waiting time: %d" % self.rx_wait_time.GetValue())
        self.rx_wait_time.SetColors(default_color=wx.RED)

    def on_apply_rx_wait_time(self, event):
        log.debug("Apply new waiting time: %d" % self.rx_wait_time.GetValue())
        self.rx_wait_time.SetColors(default_color=wx.BLACK)
        self.settings_db.rx_max_wait_time = self.rx_wait_time.GetValue()
        self.update_data()

    # WOA Path

    def on_woa_path_change(self, event):
        """ Method called when the waiting time is changed """
        log.debug("Changed WOA path: %s" % self.woa_path.GetValue())
        self.woa_path.SetForegroundColour(wx.RED)

    def on_picked_woa_path(self, event):
        """ Method called when the WOA DB path was picked """
        log.debug("Picked WOA path: %s" % self.woa_path_browse_btn.GetPath())
        self.woa_path.SetValue(self.woa_path_browse_btn.GetPath())
        self.woa_path.SetForegroundColour(wx.RED)

    def on_apply_woa_path(self, event):
        log.debug("Apply new WOA path: %s" % self.woa_path.GetValue())
        if self.woa_path.GetValue() == "":
            self.settings_db.woa_path = None
        elif not os.path.exists(self.woa_path.GetValue()):
            dlg = wx.MessageDialog(self,
                                   'The selected path does not exist: %s' % self.woa_path.GetValue(),
                                   'Input error', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return
        else:
            self.settings_db.woa_path = self.woa_path.GetValue()
        self.woa_path.SetForegroundColour(wx.BLACK)
        self.update_data()

    def on_ssp_up_or_down_change(self, event):
        log.debug("SSP up or down: %d(%s)"
                  % (self.ssp_up_or_down.GetSelection(),
                     self.ssp_up_or_down.GetString(self.ssp_up_or_down.GetSelection())))
        self.ssp_up_or_down.SetOwnBackgroundColour(wx.RED)

    def on_apply_ssp_up_or_down(self, event):
        log.debug("Apply new SSP processing direction: %d(%s)"
                  % (self.ssp_up_or_down.GetSelection(),
                     self.ssp_up_or_down.GetString(self.ssp_up_or_down.GetSelection())))
        self.ssp_up_or_down.SetOwnBackgroundColour(wx.RED)
        self.settings_db.ssp_up_or_down = \
            self.ssp_up_or_down.GetString(self.ssp_up_or_down.GetSelection())
        self.update_data()
