from __future__ import absolute_import, division, print_function, unicode_literals

import wx
from wx.lib import intctrl
import os
import logging

log = logging.getLogger(__name__)

from hydroffice.ssp.settings.settings import Settings
from hydroffice.ssp.settings.db import SettingsDb, DbSettingsError


class ExportPanel(wx.Panel):
    def __init__(self, parent_frame, db, *args, **kwargs):
        """ This panel provides user interaction to common settings """
        super(ExportPanel, self).__init__(*args, **kwargs)

        # Store an handle to the Settings DB
        self.parent_frame = parent_frame
        self.settings_db = db
        self.selected_profile_item = 0

        # Main box
        main_box = wx.StaticBox(self)
        main_box_szr = wx.StaticBoxSizer(main_box, wx.VERTICAL)

        #
        # User Append Caris File
        #
        user_append_caris_file_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        user_append_caris_file_txt_szr = wx.BoxSizer(wx.VERTICAL)
        user_append_caris_file_txt = wx.StaticText(self, label="Append Caris File (user)", style=wx.ALIGN_CENTER)
        user_append_caris_file_txt.Wrap(width=150)
        user_append_caris_file_txt_szr.AddStretchSpacer()
        user_append_caris_file_txt_szr.Add(user_append_caris_file_txt, 0, wx.EXPAND)
        user_append_caris_file_txt_szr.AddStretchSpacer()

        # choice control
        source_choices = ["True", "False"]
        self.user_append_caris_file = wx.ComboBox(main_box, choices=source_choices) #, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.user_append_caris_file.Bind(wx.EVT_COMBOBOX, self.on_user_append_caris_file_change)

        # buttons
        lst_user_append_caris_file_szr = wx.BoxSizer(wx.VERTICAL)
        user_append_caris_file_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        user_append_caris_file_btn.SetToolTipString("Apply the new value")
        user_append_caris_file_btn.Bind(wx.EVT_BUTTON, self.on_apply_user_append_caris_file)
        lst_user_append_caris_file_szr.Add(user_append_caris_file_btn, 0, wx.ALIGN_RIGHT)

        user_append_caris_file_szr.Add(user_append_caris_file_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        user_append_caris_file_szr.Add(self.user_append_caris_file, 2, wx.EXPAND | wx.ALL, 5)
        user_append_caris_file_szr.Add(lst_user_append_caris_file_szr, 0, wx.EXPAND | wx.ALL, 5)

        #
        # User Export Prompt Filename
        #
        user_export_prompt_filename_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        user_export_prompt_filename_txt_szr = wx.BoxSizer(wx.VERTICAL)
        user_export_prompt_filename_txt = wx.StaticText(self, label="Export Prompt Filename (user)",
                                                        style=wx.ALIGN_CENTER)
        user_export_prompt_filename_txt.Wrap(width=150)
        user_export_prompt_filename_txt_szr.AddStretchSpacer()
        user_export_prompt_filename_txt_szr.Add(user_export_prompt_filename_txt, 0, wx.EXPAND)
        user_export_prompt_filename_txt_szr.AddStretchSpacer()

        # choice control
        source_choices = ["True", "False"]
        self.user_export_prompt_filename = wx.ComboBox(main_box, choices=source_choices) #, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.user_export_prompt_filename.Bind(wx.EVT_COMBOBOX, self.on_user_export_prompt_filename_change)

        # buttons
        lst_user_export_prompt_filename_szr = wx.BoxSizer(wx.VERTICAL)
        user_export_prompt_filename_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        user_export_prompt_filename_btn.SetToolTipString("Apply the new value")
        user_export_prompt_filename_btn.Bind(wx.EVT_BUTTON, self.on_apply_user_export_prompt_filename)
        lst_user_export_prompt_filename_szr.Add(user_export_prompt_filename_btn, 0, wx.ALIGN_RIGHT)

        user_export_prompt_filename_szr.Add(user_export_prompt_filename_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        user_export_prompt_filename_szr.Add(self.user_export_prompt_filename, 2, wx.EXPAND | wx.ALL, 5)
        user_export_prompt_filename_szr.Add(lst_user_export_prompt_filename_szr, 0, wx.EXPAND | wx.ALL, 5)

        #
        # Automatically export on send
        #
        auto_export_on_send_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        auto_export_on_send_txt_szr = wx.BoxSizer(wx.VERTICAL)
        auto_export_on_send_txt = wx.StaticText(self, label="Auto export on send",
                                                        style=wx.ALIGN_CENTER)
        auto_export_on_send_txt.Wrap(width=150)
        auto_export_on_send_txt_szr.AddStretchSpacer()
        auto_export_on_send_txt_szr.Add(auto_export_on_send_txt, 0, wx.EXPAND)
        auto_export_on_send_txt_szr.AddStretchSpacer()

        # choice control
        source_choices = ["True", "False"]
        self.auto_export_on_send = wx.ComboBox(main_box, choices=source_choices) #, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.auto_export_on_send.Bind(wx.EVT_COMBOBOX, self.on_auto_export_on_send_change)

        # buttons
        lst_auto_export_on_send_szr = wx.BoxSizer(wx.VERTICAL)
        auto_export_on_send_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        auto_export_on_send_btn.SetToolTipString("Apply the new value")
        auto_export_on_send_btn.Bind(wx.EVT_BUTTON, self.on_apply_auto_export_on_send)
        lst_auto_export_on_send_szr.Add(auto_export_on_send_btn, 0, wx.ALIGN_RIGHT)

        auto_export_on_send_szr.Add(auto_export_on_send_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        auto_export_on_send_szr.Add(self.auto_export_on_send, 2, wx.EXPAND | wx.ALL, 5)
        auto_export_on_send_szr.Add(lst_auto_export_on_send_szr, 0, wx.EXPAND | wx.ALL, 5)

        #
        # Add rows to the main box
        #
        main_box_szr.Add(user_append_caris_file_szr, 0, wx.EXPAND)
        main_box_szr.Add(user_export_prompt_filename_szr, 0, wx.EXPAND)
        main_box_szr.Add(auto_export_on_send_szr, 0, wx.EXPAND)

        # Set the main box sizer and fit
        self.SetSizer(main_box_szr)
        self.Layout()

        # Update the data content
        self.update_data()

    def update_data(self, event=None):
        """ Update the data from the database """
        self.user_append_caris_file.SetSelection(
            self.user_append_caris_file.FindString(str(self.settings_db.user_append_caris_file)))
        self.user_append_caris_file.SetOwnBackgroundColour(wx.WHITE)

        self.user_export_prompt_filename.SetSelection(
            self.user_export_prompt_filename.FindString(str(self.settings_db.user_export_prompt_filename)))
        self.user_export_prompt_filename.SetOwnBackgroundColour(wx.WHITE)
        
        self.auto_export_on_send.SetSelection(
            self.auto_export_on_send.FindString(str(self.settings_db.auto_export_on_send)))
        self.auto_export_on_send.SetOwnBackgroundColour(wx.WHITE)

    # SSP External Source

    def on_user_append_caris_file_change(self, event):
        log.debug("User append Caris file: %d(%s)"
                  % (self.user_append_caris_file.GetSelection(),
                     self.user_append_caris_file.GetString(self.user_append_caris_file.GetSelection())))
        self.user_append_caris_file.SetOwnBackgroundColour(wx.RED)

    def on_apply_user_append_caris_file(self, event):
        log.debug("Apply user append Caris file: %d(%s)"
                  % (self.user_append_caris_file.GetSelection(),
                     self.user_append_caris_file.GetString(self.user_append_caris_file.GetSelection())))
        self.user_append_caris_file.SetOwnBackgroundColour(wx.RED)
        self.settings_db.user_append_caris_file = \
            self.user_append_caris_file.GetString(self.user_append_caris_file.GetSelection())
        self.update_data()

    def on_user_export_prompt_filename_change(self, event):
        log.debug("User export prompt filename: %d(%s)"
                  % (self.user_export_prompt_filename.GetSelection(),
                     self.user_export_prompt_filename.GetString(self.user_export_prompt_filename.GetSelection())))
        self.user_export_prompt_filename.SetOwnBackgroundColour(wx.RED)

    def on_apply_user_export_prompt_filename(self, event):
        log.debug("Apply user export prompt filename: %d(%s)"
                  % (self.user_export_prompt_filename.GetSelection(),
                     self.user_export_prompt_filename.GetString(self.user_export_prompt_filename.GetSelection())))
        self.user_export_prompt_filename.SetOwnBackgroundColour(wx.RED)
        self.settings_db.user_export_prompt_filename = \
            self.user_export_prompt_filename.GetString(self.user_export_prompt_filename.GetSelection())
        self.update_data()

    def on_auto_export_on_send_change(self, event):
        log.debug("Auto export on send: %d(%s)"
                  % (self.auto_export_on_send.GetSelection(),
                     self.auto_export_on_send.GetString(self.auto_export_on_send.GetSelection())))
        self.auto_export_on_send.SetOwnBackgroundColour(wx.RED)

    def on_apply_auto_export_on_send(self, event):
        log.debug("Apply auto export on send: %d(%s)"
                  % (self.auto_export_on_send.GetSelection(),
                     self.auto_export_on_send.GetString(self.auto_export_on_send.GetSelection())))
        self.auto_export_on_send.SetOwnBackgroundColour(wx.RED)
        self.settings_db.auto_export_on_send = \
            self.auto_export_on_send.GetString(self.auto_export_on_send.GetSelection())
        self.update_data()