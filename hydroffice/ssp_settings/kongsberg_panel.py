from __future__ import absolute_import, division, print_function, unicode_literals

import wx
from wx.lib import intctrl
import os
import logging

log = logging.getLogger(__name__)

from hydroffice.ssp.settings.settings import Settings
from hydroffice.ssp.settings.db import SettingsDb, DbSettingsError


class KongsbergPanel(wx.Panel):
    def __init__(self, parent_frame, db, *args, **kwargs):
        """ This panel provides user interaction to common settings """
        super(KongsbergPanel, self).__init__(*args, **kwargs)

        # Store an handle to the Settings DB
        self.parent_frame = parent_frame
        self.settings_db = db
        self.selected_profile_item = 0

        # Main box
        main_box = wx.StaticBox(self)
        main_box_szr = wx.StaticBoxSizer(main_box, wx.VERTICAL)

        #
        # km_listen_port_szr
        #
        km_listen_port_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        km_listen_port_txt_szr = wx.BoxSizer(wx.VERTICAL)
        km_listen_port_txt = wx.StaticText(self, label="Listen Port", style=wx.ALIGN_CENTER)
        km_listen_port_txt.Wrap(width=150)
        km_listen_port_txt_szr.AddStretchSpacer()
        km_listen_port_txt_szr.Add(km_listen_port_txt, 0, wx.EXPAND)
        km_listen_port_txt_szr.AddStretchSpacer()

        # integer control
        self.km_listen_port = intctrl.IntCtrl(main_box, min=0, max=999999, limited=True)
        self.km_listen_port.Bind(wx.EVT_TEXT, self.on_km_listen_port_change)

        # buttons
        lst_km_listen_port_szr = wx.BoxSizer(wx.VERTICAL)
        km_listen_port_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        km_listen_port_btn.SetToolTipString("Apply the new value")
        km_listen_port_btn.Bind(wx.EVT_BUTTON, self.on_apply_km_listen_port)
        lst_km_listen_port_szr.Add(km_listen_port_btn, 0, wx.ALIGN_RIGHT)

        km_listen_port_szr.Add(km_listen_port_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        km_listen_port_szr.Add(self.km_listen_port, 2, wx.EXPAND | wx.ALL, 5)
        km_listen_port_szr.Add(lst_km_listen_port_szr, 0, wx.EXPAND | wx.ALL, 5)     
        
        #
        # km_listen_timeout_szr
        #
        km_listen_timeout_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        km_listen_timeout_txt_szr = wx.BoxSizer(wx.VERTICAL)
        km_listen_timeout_txt = wx.StaticText(self, label="Listen TimeOut", style=wx.ALIGN_CENTER)
        km_listen_timeout_txt.Wrap(width=150)
        km_listen_timeout_txt_szr.AddStretchSpacer()
        km_listen_timeout_txt_szr.Add(km_listen_timeout_txt, 0, wx.EXPAND)
        km_listen_timeout_txt_szr.AddStretchSpacer()

        # integer control
        self.km_listen_timeout = intctrl.IntCtrl(main_box, min=0, max=999999, limited=True)
        self.km_listen_timeout.Bind(wx.EVT_TEXT, self.on_km_listen_timeout_change)

        # buttons
        lst_km_listen_timeout_szr = wx.BoxSizer(wx.VERTICAL)
        km_listen_timeout_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        km_listen_timeout_btn.SetToolTipString("Apply the new value")
        km_listen_timeout_btn.Bind(wx.EVT_BUTTON, self.on_apply_km_listen_timeout)
        lst_km_listen_timeout_szr.Add(km_listen_timeout_btn, 0, wx.ALIGN_RIGHT)

        km_listen_timeout_szr.Add(km_listen_timeout_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        km_listen_timeout_szr.Add(self.km_listen_timeout, 2, wx.EXPAND | wx.ALL, 5)
        km_listen_timeout_szr.Add(lst_km_listen_timeout_szr, 0, wx.EXPAND | wx.ALL, 5)     

        #
        # sis_auto_apply_manual_casts
        #
        sis_auto_apply_manual_casts_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        sis_auto_apply_manual_casts_txt_szr = wx.BoxSizer(wx.VERTICAL)
        sis_auto_apply_manual_casts_txt = wx.StaticText(self, label="SIS Auto Apply Manual Casts", style=wx.ALIGN_CENTER)
        sis_auto_apply_manual_casts_txt.Wrap(width=150)
        sis_auto_apply_manual_casts_txt_szr.AddStretchSpacer()
        sis_auto_apply_manual_casts_txt_szr.Add(sis_auto_apply_manual_casts_txt, 0, wx.EXPAND)
        sis_auto_apply_manual_casts_txt_szr.AddStretchSpacer()

        # choice control
        source_choices = ["True", "False"]
        self.sis_auto_apply_manual_casts = wx.ComboBox(main_box, choices=source_choices) #, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.sis_auto_apply_manual_casts.Bind(wx.EVT_COMBOBOX, self.on_sis_auto_apply_manual_casts_change)

        # buttons
        lst_sis_auto_apply_manual_casts_szr = wx.BoxSizer(wx.VERTICAL)
        sis_auto_apply_manual_casts_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        sis_auto_apply_manual_casts_btn.SetToolTipString("Apply the new value")
        sis_auto_apply_manual_casts_btn.Bind(wx.EVT_BUTTON, self.on_apply_sis_auto_apply_manual_casts)
        lst_sis_auto_apply_manual_casts_szr.Add(sis_auto_apply_manual_casts_btn, 0, wx.ALIGN_RIGHT)

        sis_auto_apply_manual_casts_szr.Add(sis_auto_apply_manual_casts_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        sis_auto_apply_manual_casts_szr.Add(self.sis_auto_apply_manual_casts, 2, wx.EXPAND | wx.ALL, 5)
        sis_auto_apply_manual_casts_szr.Add(lst_sis_auto_apply_manual_casts_szr, 0, wx.EXPAND | wx.ALL, 5)

        #
        # Add rows to the main box
        #
        main_box_szr.Add(km_listen_port_szr, 0, wx.EXPAND)
        main_box_szr.Add(km_listen_timeout_szr, 0, wx.EXPAND)
        main_box_szr.Add(sis_auto_apply_manual_casts_szr, 0, wx.EXPAND)

        # Set the main box sizer and fit
        self.SetSizer(main_box_szr)
        self.Layout()

        # Update the data content
        self.update_data()

    def update_data(self, event=None):
        """ Update the data from the database """
        self.km_listen_port.ChangeValue(self.settings_db.km_listen_port)
        self.km_listen_port.SetColors(default_color=wx.BLACK)
        
        self.km_listen_timeout.ChangeValue(self.settings_db.km_listen_timeout)
        self.km_listen_timeout.SetColors(default_color=wx.BLACK)
        
        self.sis_auto_apply_manual_casts.SetSelection(
            self.sis_auto_apply_manual_casts.FindString(str(self.settings_db.sis_auto_apply_manual_casts)))
        self.sis_auto_apply_manual_casts.SetOwnBackgroundColour(wx.WHITE)

    # =================================================== 

    def on_km_listen_port_change(self, event):
        log.debug("Changed listen port: %d" % self.km_listen_port.GetValue())
        self.km_listen_port.SetColors(default_color=wx.RED)

    def on_apply_km_listen_port(self, event):
        log.debug("Apply new listen port: %d" % self.km_listen_port.GetValue())
        self.km_listen_port.SetColors(default_color=wx.BLACK)
        self.settings_db.km_listen_port = self.km_listen_port.GetValue()
        self.update_data()
        
    def on_km_listen_timeout_change(self, event):
        log.debug("Changed listen port: %d" % self.km_listen_timeout.GetValue())
        self.km_listen_timeout.SetColors(default_color=wx.RED)

    def on_apply_km_listen_timeout(self, event):
        log.debug("Apply new listen port: %d" % self.km_listen_timeout.GetValue())
        self.km_listen_timeout.SetColors(default_color=wx.BLACK)
        self.settings_db.km_listen_timeout = self.km_listen_timeout.GetValue()
        self.update_data()

    def on_sis_auto_apply_manual_casts_change(self, event):
        log.debug("SIS auto apply manul cast: %d(%s)"
                  % (self.sis_auto_apply_manual_casts.GetSelection(),
                     self.sis_auto_apply_manual_casts.GetString(self.sis_auto_apply_manual_casts.GetSelection())))
        self.sis_auto_apply_manual_casts.SetOwnBackgroundColour(wx.RED)

    def on_apply_sis_auto_apply_manual_casts(self, event):
        log.debug("Apply SIS auto apply manual cast: %d(%s)"
                  % (self.sis_auto_apply_manual_casts.GetSelection(),
                     self.sis_auto_apply_manual_casts.GetString(self.sis_auto_apply_manual_casts.GetSelection())))
        self.sis_auto_apply_manual_casts.SetOwnBackgroundColour(wx.RED)
        self.settings_db.sis_auto_apply_manual_casts = \
            self.sis_auto_apply_manual_casts.GetString(self.sis_auto_apply_manual_casts.GetSelection())
        self.update_data()
