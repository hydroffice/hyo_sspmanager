from __future__ import absolute_import, division, print_function, unicode_literals

import wx
from wx.lib import intctrl
import os
import logging

log = logging.getLogger(__name__)

from hydroffice.ssp.settings.settings import Settings
from hydroffice.ssp.settings.db import SettingsDb, DbSettingsError


class SippicanPanel(wx.Panel):
    def __init__(self, parent_frame, db, *args, **kwargs):
        """ This panel provides user interaction to common settings """
        super(SippicanPanel, self).__init__(*args, **kwargs)

        # Store an handle to the Settings DB
        self.parent_frame = parent_frame
        self.settings_db = db
        self.selected_profile_item = 0

        # Main box
        main_box = wx.StaticBox(self)
        main_box_szr = wx.StaticBoxSizer(main_box, wx.VERTICAL)

        #
        # sippican_listen_port
        #
        sippican_listen_port_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        sippican_listen_port_txt_szr = wx.BoxSizer(wx.VERTICAL)
        sippican_listen_port_txt = wx.StaticText(self, label="Listen Port", style=wx.ALIGN_CENTER)
        sippican_listen_port_txt.Wrap(width=150)
        sippican_listen_port_txt_szr.AddStretchSpacer()
        sippican_listen_port_txt_szr.Add(sippican_listen_port_txt, 0, wx.EXPAND)
        sippican_listen_port_txt_szr.AddStretchSpacer()

        # integer control
        self.sippican_listen_port = intctrl.IntCtrl(main_box, min=0, max=999999, limited=True)
        self.sippican_listen_port.Bind(wx.EVT_TEXT, self.on_sippican_listen_port_change)

        # buttons
        lst_sippican_listen_port_szr = wx.BoxSizer(wx.VERTICAL)
        sippican_listen_port_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        sippican_listen_port_btn.SetToolTipString("Apply the new value")
        sippican_listen_port_btn.Bind(wx.EVT_BUTTON, self.on_apply_sippican_listen_port)
        lst_sippican_listen_port_szr.Add(sippican_listen_port_btn, 0, wx.ALIGN_RIGHT)

        sippican_listen_port_szr.Add(sippican_listen_port_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        sippican_listen_port_szr.Add(self.sippican_listen_port, 2, wx.EXPAND | wx.ALL, 5)
        sippican_listen_port_szr.Add(lst_sippican_listen_port_szr, 0, wx.EXPAND | wx.ALL, 5)     
        
        #
        # sippican_listen_timeout
        #
        sippican_listen_timeout_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        sippican_listen_timeout_txt_szr = wx.BoxSizer(wx.VERTICAL)
        sippican_listen_timeout_txt = wx.StaticText(self, label="Listen TimeOut", style=wx.ALIGN_CENTER)
        sippican_listen_timeout_txt.Wrap(width=150)
        sippican_listen_timeout_txt_szr.AddStretchSpacer()
        sippican_listen_timeout_txt_szr.Add(sippican_listen_timeout_txt, 0, wx.EXPAND)
        sippican_listen_timeout_txt_szr.AddStretchSpacer()

        # integer control
        self.sippican_listen_timeout = intctrl.IntCtrl(main_box, min=0, max=999999, limited=True)
        self.sippican_listen_timeout.Bind(wx.EVT_TEXT, self.on_sippican_listen_timeout_change)

        # buttons
        lst_sippican_listen_timeout_szr = wx.BoxSizer(wx.VERTICAL)
        sippican_listen_timeout_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        sippican_listen_timeout_btn.SetToolTipString("Apply the new value")
        sippican_listen_timeout_btn.Bind(wx.EVT_BUTTON, self.on_apply_sippican_listen_timeout)
        lst_sippican_listen_timeout_szr.Add(sippican_listen_timeout_btn, 0, wx.ALIGN_RIGHT)

        sippican_listen_timeout_szr.Add(sippican_listen_timeout_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        sippican_listen_timeout_szr.Add(self.sippican_listen_timeout, 2, wx.EXPAND | wx.ALL, 5)
        sippican_listen_timeout_szr.Add(lst_sippican_listen_timeout_szr, 0, wx.EXPAND | wx.ALL, 5)

        #
        # Add rows to the main box
        #
        main_box_szr.Add(sippican_listen_port_szr, 0, wx.EXPAND)
        main_box_szr.Add(sippican_listen_timeout_szr, 0, wx.EXPAND)

        # Set the main box sizer and fit
        self.SetSizer(main_box_szr)
        self.Layout()

        # Update the data content
        self.update_data()

    def update_data(self, event=None):
        """ Update the data from the database """
        self.sippican_listen_port.ChangeValue(self.settings_db.sippican_listen_port)
        self.sippican_listen_port.SetColors(default_color=wx.BLACK)
        
        self.sippican_listen_timeout.ChangeValue(self.settings_db.sippican_listen_timeout)
        self.sippican_listen_timeout.SetColors(default_color=wx.BLACK)

    # =================================================== 

    def on_sippican_listen_port_change(self, event):
        log.debug("Changed listen port: %d" % self.sippican_listen_port.GetValue())
        self.sippican_listen_port.SetColors(default_color=wx.RED)

    def on_apply_sippican_listen_port(self, event):
        log.debug("Apply new listen port: %d" % self.sippican_listen_port.GetValue())
        self.sippican_listen_port.SetColors(default_color=wx.BLACK)
        self.settings_db.sippican_listen_port = self.sippican_listen_port.GetValue()
        self.update_data()
        
    def on_sippican_listen_timeout_change(self, event):
        log.debug("Changed listen port: %d" % self.sippican_listen_timeout.GetValue())
        self.sippican_listen_timeout.SetColors(default_color=wx.RED)

    def on_apply_sippican_listen_timeout(self, event):
        log.debug("Apply new listen port: %d" % self.sippican_listen_timeout.GetValue())
        self.sippican_listen_timeout.SetColors(default_color=wx.BLACK)
        self.settings_db.sippican_listen_timeout = self.sippican_listen_timeout.GetValue()
        self.update_data()

