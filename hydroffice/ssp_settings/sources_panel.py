from __future__ import absolute_import, division, print_function, unicode_literals

import wx
from wx.lib import intctrl
import os
import logging

log = logging.getLogger(__name__)

from hydroffice.ssp.settings.settings import Settings
from hydroffice.ssp.settings.db import SettingsDb, DbSettingsError


class SourcesPanel(wx.Panel):
    def __init__(self, parent_frame, db, *args, **kwargs):
        """ This panel provides user interaction to common settings """
        super(SourcesPanel, self).__init__(*args, **kwargs)

        # Store an handle to the Settings DB
        self.parent_frame = parent_frame
        self.settings_db = db
        self.selected_profile_item = 0

        # Main box
        main_box = wx.StaticBox(self)
        main_box_szr = wx.StaticBoxSizer(main_box, wx.VERTICAL)

        #
        # SSP Ext Source
        #
        ssp_extension_source_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        ssp_extension_source_txt_szr = wx.BoxSizer(wx.VERTICAL)
        ssp_extension_source_txt = wx.StaticText(self, label="SSP Extension Source", style=wx.ALIGN_CENTER)
        ssp_extension_source_txt.Wrap(width=150)
        ssp_extension_source_txt_szr.AddStretchSpacer()
        ssp_extension_source_txt_szr.Add(ssp_extension_source_txt, 0, wx.EXPAND)
        ssp_extension_source_txt_szr.AddStretchSpacer()

        # choice control
        source_choices = ["WOA09", "RTOFS"]
        self.ssp_extension_source = wx.ComboBox(main_box, choices=source_choices) #, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.ssp_extension_source.Bind(wx.EVT_COMBOBOX, self.on_ssp_extension_source_change)

        # buttons
        lst_ssp_extension_source_szr = wx.BoxSizer(wx.VERTICAL)
        ssp_extension_source_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        ssp_extension_source_btn.SetToolTipString("Apply the new value")
        ssp_extension_source_btn.Bind(wx.EVT_BUTTON, self.on_apply_ssp_extension_source)
        lst_ssp_extension_source_szr.Add(ssp_extension_source_btn, 0, wx.ALIGN_RIGHT)

        ssp_extension_source_szr.Add(ssp_extension_source_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        ssp_extension_source_szr.Add(self.ssp_extension_source, 2, wx.EXPAND | wx.ALL, 5)
        ssp_extension_source_szr.Add(lst_ssp_extension_source_szr, 0, wx.EXPAND | wx.ALL, 5)

        #
        # SSP Salinity Source
        #
        ssp_salinity_source_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        ssp_salinity_source_txt_szr = wx.BoxSizer(wx.VERTICAL)
        ssp_salinity_source_txt = wx.StaticText(self, label="SSP Salinity Source", style=wx.ALIGN_CENTER)
        ssp_salinity_source_txt.Wrap(width=150)
        ssp_salinity_source_txt_szr.AddStretchSpacer()
        ssp_salinity_source_txt_szr.Add(ssp_salinity_source_txt, 0, wx.EXPAND)
        ssp_salinity_source_txt_szr.AddStretchSpacer()

        # choice control
        source_choices = ["WOA09", "RTOFS"]
        self.ssp_salinity_source = wx.ComboBox(main_box, choices=source_choices) #, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.ssp_salinity_source.Bind(wx.EVT_COMBOBOX, self.on_ssp_salinity_source_change)

        # buttons
        lst_ssp_salinity_source_szr = wx.BoxSizer(wx.VERTICAL)
        ssp_salinity_source_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        ssp_salinity_source_btn.SetToolTipString("Apply the new value")
        ssp_salinity_source_btn.Bind(wx.EVT_BUTTON, self.on_apply_ssp_salinity_source)
        lst_ssp_salinity_source_szr.Add(ssp_salinity_source_btn, 0, wx.ALIGN_RIGHT)

        ssp_salinity_source_szr.Add(ssp_salinity_source_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        ssp_salinity_source_szr.Add(self.ssp_salinity_source, 2, wx.EXPAND | wx.ALL, 5)
        ssp_salinity_source_szr.Add(lst_ssp_salinity_source_szr, 0, wx.EXPAND | wx.ALL, 5)

        #
        # SSP Temperature and Salinity Source
        #
        ssp_temp_sal_source_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        ssp_temp_sal_source_txt_szr = wx.BoxSizer(wx.VERTICAL)
        ssp_temp_sal_source_txt = wx.StaticText(self, label="SSP Temp/Salinity Source", style=wx.ALIGN_CENTER)
        ssp_temp_sal_source_txt.Wrap(width=150)
        ssp_temp_sal_source_txt_szr.AddStretchSpacer()
        ssp_temp_sal_source_txt_szr.Add(ssp_temp_sal_source_txt, 0, wx.EXPAND)
        ssp_temp_sal_source_txt_szr.AddStretchSpacer()

        # choice control
        source_choices = ["WOA09", "RTOFS"]
        self.ssp_temp_sal_source = wx.ComboBox(main_box, choices=source_choices) #, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.ssp_temp_sal_source.Bind(wx.EVT_COMBOBOX, self.on_ssp_temp_sal_source_change)

        # buttons
        lst_ssp_temp_sal_source_szr = wx.BoxSizer(wx.VERTICAL)
        ssp_temp_sal_source_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        ssp_temp_sal_source_btn.SetToolTipString("Apply the new value")
        ssp_temp_sal_source_btn.Bind(wx.EVT_BUTTON, self.on_apply_ssp_temp_sal_source)
        lst_ssp_temp_sal_source_szr.Add(ssp_temp_sal_source_btn, 0, wx.ALIGN_RIGHT)

        ssp_temp_sal_source_szr.Add(ssp_temp_sal_source_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        ssp_temp_sal_source_szr.Add(self.ssp_temp_sal_source, 2, wx.EXPAND | wx.ALL, 5)
        ssp_temp_sal_source_szr.Add(lst_ssp_temp_sal_source_szr, 0, wx.EXPAND | wx.ALL, 5)

        #
        # SIS Server Source
        #
        sis_server_source_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        sis_server_source_txt_szr = wx.BoxSizer(wx.VERTICAL)
        sis_server_source_txt = wx.StaticText(self, label="SIS Server Source", style=wx.ALIGN_CENTER)
        sis_server_source_txt.Wrap(width=150)
        sis_server_source_txt_szr.AddStretchSpacer()
        sis_server_source_txt_szr.Add(sis_server_source_txt, 0, wx.EXPAND)
        sis_server_source_txt_szr.AddStretchSpacer()

        # choice control
        source_choices = ["WOA09", "RTOFS"]
        self.sis_server_source = wx.ComboBox(main_box, choices=source_choices) #, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.sis_server_source.Bind(wx.EVT_COMBOBOX, self.on_sis_server_source_change)

        # buttons
        lst_sis_server_source_szr = wx.BoxSizer(wx.VERTICAL)
        sis_server_source_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        sis_server_source_btn.SetToolTipString("Apply the new value")
        sis_server_source_btn.Bind(wx.EVT_BUTTON, self.on_apply_sis_server_source)
        lst_sis_server_source_szr.Add(sis_server_source_btn, 0, wx.ALIGN_RIGHT)

        sis_server_source_szr.Add(sis_server_source_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        sis_server_source_szr.Add(self.sis_server_source, 2, wx.EXPAND | wx.ALL, 5)
        sis_server_source_szr.Add(lst_sis_server_source_szr, 0, wx.EXPAND | wx.ALL, 5)

        #
        # Add rows to the main box
        #
        main_box_szr.Add(ssp_extension_source_szr, 0, wx.EXPAND)
        main_box_szr.Add(ssp_salinity_source_szr, 0, wx.EXPAND)
        main_box_szr.Add(ssp_temp_sal_source_szr, 0, wx.EXPAND)
        main_box_szr.Add(sis_server_source_szr, 0, wx.EXPAND)

        # Set the main box sizer and fit
        self.SetSizer(main_box_szr)
        self.Layout()

        # Update the data content
        self.update_data()

    def update_data(self, event=None):
        """ Update the data from the database """
        self.ssp_extension_source.SetSelection(
            self.ssp_extension_source.FindString(self.settings_db.ssp_extension_source))
        self.ssp_extension_source.SetOwnBackgroundColour(wx.WHITE)

        self.ssp_salinity_source.SetSelection(
            self.ssp_salinity_source.FindString(self.settings_db.ssp_salinity_source))
        self.ssp_salinity_source.SetOwnBackgroundColour(wx.WHITE)

        self.ssp_temp_sal_source.SetSelection(
            self.ssp_temp_sal_source.FindString(self.settings_db.ssp_temp_sal_source))
        self.ssp_temp_sal_source.SetOwnBackgroundColour(wx.WHITE)

        self.sis_server_source.SetSelection(
            self.sis_server_source.FindString(self.settings_db.sis_server_source))
        self.sis_server_source.SetOwnBackgroundColour(wx.WHITE)

    # SSP External Source

    def on_ssp_extension_source_change(self, event):
        log.debug("SSP External Source: %d(%s)"
                  % (self.ssp_extension_source.GetSelection(),
                     self.ssp_extension_source.GetString(self.ssp_extension_source.GetSelection())))
        self.ssp_extension_source.SetOwnBackgroundColour(wx.RED)

    def on_apply_ssp_extension_source(self, event):
        log.debug("Apply new SSP External Source: %d(%s)"
                  % (self.ssp_extension_source.GetSelection(),
                     self.ssp_extension_source.GetString(self.ssp_extension_source.GetSelection())))
        self.ssp_extension_source.SetOwnBackgroundColour(wx.RED)
        self.settings_db.ssp_extension_source = self.ssp_extension_source.GetString(self.ssp_extension_source.GetSelection())
        self.update_data()

    def on_ssp_salinity_source_change(self, event):
        log.debug("SSP Salinity Source: %d(%s)"
                  % (self.ssp_salinity_source.GetSelection(),
                     self.ssp_salinity_source.GetString(self.ssp_salinity_source.GetSelection())))
        self.ssp_salinity_source.SetOwnBackgroundColour(wx.RED)

    def on_apply_ssp_salinity_source(self, event):
        log.debug("Apply new SSP Salinity Source: %d(%s)"
                  % (self.ssp_salinity_source.GetSelection(),
                     self.ssp_salinity_source.GetString(self.ssp_salinity_source.GetSelection())))
        self.ssp_salinity_source.SetOwnBackgroundColour(wx.RED)
        self.settings_db.ssp_salinity_source = \
            self.ssp_salinity_source.GetString(self.ssp_salinity_source.GetSelection())
        self.update_data()

    def on_ssp_temp_sal_source_change(self, event):
        log.debug("SSP Temp & Salinity Source: %d(%s)"
                  % (self.ssp_temp_sal_source.GetSelection(),
                     self.ssp_temp_sal_source.GetString(self.ssp_temp_sal_source.GetSelection())))
        self.ssp_temp_sal_source.SetOwnBackgroundColour(wx.RED)

    def on_apply_ssp_temp_sal_source(self, event):
        log.debug("Apply new SSP Temp & Salinity Source: %d(%s)"
                  % (self.ssp_temp_sal_source.GetSelection(),
                     self.ssp_temp_sal_source.GetString(self.ssp_temp_sal_source.GetSelection())))
        self.ssp_temp_sal_source.SetOwnBackgroundColour(wx.RED)
        self.settings_db.ssp_temp_sal_source = \
            self.ssp_temp_sal_source.GetString(self.ssp_temp_sal_source.GetSelection())
        self.update_data()

    def on_sis_server_source_change(self, event):
        log.debug("SIS Server Source: %d(%s)"
                  % (self.sis_server_source.GetSelection(),
                     self.sis_server_source.GetString(self.sis_server_source.GetSelection())))
        self.sis_server_source.SetOwnBackgroundColour(wx.RED)

    def on_apply_sis_server_source(self, event):
        log.debug("Apply new SIS Server Source: %d(%s)"
                  % (self.sis_server_source.GetSelection(),
                     self.sis_server_source.GetString(self.sis_server_source.GetSelection())))
        self.sis_server_source.SetOwnBackgroundColour(wx.RED)
        self.settings_db.sis_server_source = \
            self.sis_server_source.GetString(self.sis_server_source.GetSelection())
        self.update_data()