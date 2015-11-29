from __future__ import absolute_import, division, print_function, unicode_literals

import wx
from wx.lib import intctrl
import os
import logging

log = logging.getLogger(__name__)

from hydroffice.ssp.settings.settings import Settings
from hydroffice.ssp.settings.db import SettingsDb, DbSettingsError


class ServerPanel(wx.Panel):
    def __init__(self, parent_frame, db, *args, **kwargs):
        """ This panel provides user interaction to common settings """
        super(ServerPanel, self).__init__(*args, **kwargs)

        # Store an handle to the Settings DB
        self.parent_frame = parent_frame
        self.settings_db = db
        self.selected_profile_item = 0

        # Main box
        main_box = wx.StaticBox(self)
        main_box_szr = wx.StaticBoxSizer(main_box, wx.VERTICAL)

        #
        # Server Append Caris File
        #
        server_append_caris_file_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        server_append_caris_file_txt_szr = wx.BoxSizer(wx.VERTICAL)
        server_append_caris_file_txt = wx.StaticText(self, label="Append Caris File (server)", style=wx.ALIGN_CENTER)
        server_append_caris_file_txt.Wrap(width=150)
        server_append_caris_file_txt_szr.AddStretchSpacer()
        server_append_caris_file_txt_szr.Add(server_append_caris_file_txt, 0, wx.EXPAND)
        server_append_caris_file_txt_szr.AddStretchSpacer()

        # choice control
        source_choices = ["True", "False"]
        self.server_append_caris_file = wx.ComboBox(main_box, choices=source_choices) #, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.server_append_caris_file.Bind(wx.EVT_COMBOBOX, self.on_server_append_caris_file_change)

        # buttons
        lst_server_append_caris_file_szr = wx.BoxSizer(wx.VERTICAL)
        server_append_caris_file_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        server_append_caris_file_btn.SetToolTipString("Apply the new value")
        server_append_caris_file_btn.Bind(wx.EVT_BUTTON, self.on_apply_server_append_caris_file)
        lst_server_append_caris_file_szr.Add(server_append_caris_file_btn, 0, wx.ALIGN_RIGHT)

        server_append_caris_file_szr.Add(server_append_caris_file_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        server_append_caris_file_szr.Add(self.server_append_caris_file, 2, wx.EXPAND | wx.ALL, 5)
        server_append_caris_file_szr.Add(lst_server_append_caris_file_szr, 0, wx.EXPAND | wx.ALL, 5)
        
        #
        # Auto export on server send
        #
        auto_export_on_server_send_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        auto_export_on_server_send_txt_szr = wx.BoxSizer(wx.VERTICAL)
        auto_export_on_server_send_txt = wx.StaticText(self, label="Auto export on send (server)", style=wx.ALIGN_CENTER)
        auto_export_on_server_send_txt.Wrap(width=150)
        auto_export_on_server_send_txt_szr.AddStretchSpacer()
        auto_export_on_server_send_txt_szr.Add(auto_export_on_server_send_txt, 0, wx.EXPAND)
        auto_export_on_server_send_txt_szr.AddStretchSpacer()

        # choice control
        source_choices = ["True", "False"]
        self.auto_export_on_server_send = wx.ComboBox(main_box, choices=source_choices) #, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.auto_export_on_server_send.Bind(wx.EVT_COMBOBOX, self.on_auto_export_on_server_send_change)

        # buttons
        lst_auto_export_on_server_send_szr = wx.BoxSizer(wx.VERTICAL)
        auto_export_on_server_send_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        auto_export_on_server_send_btn.SetToolTipString("Apply the new value")
        auto_export_on_server_send_btn.Bind(wx.EVT_BUTTON, self.on_apply_auto_export_on_server_send)
        lst_auto_export_on_server_send_szr.Add(auto_export_on_server_send_btn, 0, wx.ALIGN_RIGHT)

        auto_export_on_server_send_szr.Add(auto_export_on_server_send_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        auto_export_on_server_send_szr.Add(self.auto_export_on_server_send, 2, wx.EXPAND | wx.ALL, 5)
        auto_export_on_server_send_szr.Add(lst_auto_export_on_server_send_szr, 0, wx.EXPAND | wx.ALL, 5)

        #
        # Server apply surface sound speed
        #
        server_apply_surface_sound_speed_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        server_apply_surface_sound_speed_txt_szr = wx.BoxSizer(wx.VERTICAL)
        server_apply_surface_sound_speed_txt = wx.StaticText(self, label="Server apply surface sound speed", 
                                                             style=wx.ALIGN_CENTER)
        server_apply_surface_sound_speed_txt.Wrap(width=150)
        server_apply_surface_sound_speed_txt_szr.AddStretchSpacer()
        server_apply_surface_sound_speed_txt_szr.Add(server_apply_surface_sound_speed_txt, 0, wx.EXPAND)
        server_apply_surface_sound_speed_txt_szr.AddStretchSpacer()

        # choice control
        source_choices = ["True", "False"]
        self.server_apply_surface_sound_speed = wx.ComboBox(main_box, choices=source_choices) #, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.server_apply_surface_sound_speed.Bind(wx.EVT_COMBOBOX, self.on_server_apply_surface_sound_speed_change)

        # buttons
        lst_server_apply_surface_sound_speed_szr = wx.BoxSizer(wx.VERTICAL)
        server_apply_surface_sound_speed_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        server_apply_surface_sound_speed_btn.SetToolTipString("Apply the new value")
        server_apply_surface_sound_speed_btn.Bind(wx.EVT_BUTTON, self.on_apply_server_apply_surface_sound_speed)
        lst_server_apply_surface_sound_speed_szr.Add(server_apply_surface_sound_speed_btn, 0, wx.ALIGN_RIGHT)

        server_apply_surface_sound_speed_szr.Add(server_apply_surface_sound_speed_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        server_apply_surface_sound_speed_szr.Add(self.server_apply_surface_sound_speed, 2, wx.EXPAND | wx.ALL, 5)
        server_apply_surface_sound_speed_szr.Add(lst_server_apply_surface_sound_speed_szr, 0, wx.EXPAND | wx.ALL, 5)

        #
        # Add rows to the main box
        #
        main_box_szr.Add(server_append_caris_file_szr, 0, wx.EXPAND)
        main_box_szr.Add(auto_export_on_server_send_szr, 0, wx.EXPAND)
        main_box_szr.Add(server_apply_surface_sound_speed_szr, 0, wx.EXPAND)

        # Set the main box sizer and fit
        self.SetSizer(main_box_szr)
        self.Layout()

        # Update the data content
        self.update_data()

    def update_data(self, event=None):
        """ Update the data from the database """
        self.server_append_caris_file.SetSelection(
            self.server_append_caris_file.FindString(str(self.settings_db.server_append_caris_file)))
        self.server_append_caris_file.SetOwnBackgroundColour(wx.WHITE)

        self.auto_export_on_server_send.SetSelection(
            self.auto_export_on_server_send.FindString(str(self.settings_db.auto_export_on_server_send)))
        self.auto_export_on_server_send.SetOwnBackgroundColour(wx.WHITE)
        
        self.server_apply_surface_sound_speed.SetSelection(
            self.server_apply_surface_sound_speed.FindString(str(self.settings_db.server_apply_surface_sound_speed)))
        self.server_apply_surface_sound_speed.SetOwnBackgroundColour(wx.WHITE)

    # =================================================== 

    def on_server_append_caris_file_change(self, event):
        log.debug("Server append Caris file: %d(%s)"
                  % (self.server_append_caris_file.GetSelection(),
                     self.server_append_caris_file.GetString(self.server_append_caris_file.GetSelection())))
        self.server_append_caris_file.SetOwnBackgroundColour(wx.RED)

    def on_apply_server_append_caris_file(self, event):
        log.debug("Apply server append Caris file: %d(%s)"
                  % (self.server_append_caris_file.GetSelection(),
                     self.server_append_caris_file.GetString(self.server_append_caris_file.GetSelection())))
        self.server_append_caris_file.SetOwnBackgroundColour(wx.RED)
        self.settings_db.server_append_caris_file = \
            self.server_append_caris_file.GetString(self.server_append_caris_file.GetSelection())
        self.update_data()

    def on_auto_export_on_server_send_change(self, event):
        log.debug("Auto export on server send change: %d(%s)"
                  % (self.auto_export_on_server_send.GetSelection(),
                     self.auto_export_on_server_send.GetString(self.auto_export_on_server_send.GetSelection())))
        self.auto_export_on_server_send.SetOwnBackgroundColour(wx.RED)

    def on_apply_auto_export_on_server_send(self, event):
        log.debug("Apply Auto export on server send: %d(%s)"
                  % (self.auto_export_on_server_send.GetSelection(),
                     self.auto_export_on_server_send.GetString(self.auto_export_on_server_send.GetSelection())))
        self.auto_export_on_server_send.SetOwnBackgroundColour(wx.RED)
        self.settings_db.auto_export_on_server_send = \
            self.auto_export_on_server_send.GetString(self.auto_export_on_server_send.GetSelection())
        self.update_data()
        
    def on_server_apply_surface_sound_speed_change(self, event):
        log.debug("Server apply surface sound speed change: %d(%s)"
                  % (self.server_apply_surface_sound_speed.GetSelection(),
                     self.server_apply_surface_sound_speed.GetString(self.server_apply_surface_sound_speed.GetSelection())))
        self.server_apply_surface_sound_speed.SetOwnBackgroundColour(wx.RED)

    def on_apply_server_apply_surface_sound_speed(self, event):
        log.debug("Apply Server apply surface sound speed: %d(%s)"
                  % (self.server_apply_surface_sound_speed.GetSelection(),
                     self.server_apply_surface_sound_speed.GetString(self.server_apply_surface_sound_speed.GetSelection())))
        self.server_apply_surface_sound_speed.SetOwnBackgroundColour(wx.RED)
        self.settings_db.server_apply_surface_sound_speed = \
            self.server_apply_surface_sound_speed.GetString(self.server_apply_surface_sound_speed.GetSelection())
        self.update_data()

