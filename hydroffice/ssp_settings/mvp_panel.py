from __future__ import absolute_import, division, print_function, unicode_literals

import wx
from wx.lib import intctrl
import os
import logging

log = logging.getLogger(__name__)

from hydroffice.ssp.settings.settings import Settings
from hydroffice.ssp.settings.db import SettingsDb, DbSettingsError


class MVPPanel(wx.Panel):
    def __init__(self, parent_frame, db, *args, **kwargs):
        """ This panel provides user interaction to common settings """
        super(MVPPanel, self).__init__(*args, **kwargs)

        # Store an handle to the Settings DB
        self.parent_frame = parent_frame
        self.settings_db = db
        self.selected_profile_item = 0

        # Main box
        main_box = wx.StaticBox(self)
        main_box_szr = wx.StaticBoxSizer(main_box, wx.VERTICAL)

        #
        # mvp_ip_address
        #
        mvp_ip_address_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        mvp_ip_address_txt_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_ip_address_txt = wx.StaticText(self, label="IP Address", style=wx.ALIGN_CENTER)
        mvp_ip_address_txt.Wrap(width=150)
        mvp_ip_address_txt_szr.AddStretchSpacer()
        mvp_ip_address_txt_szr.Add(mvp_ip_address_txt, 0, wx.EXPAND)
        mvp_ip_address_txt_szr.AddStretchSpacer()

        # directory text ctrl
        self.mvp_ip_address = wx.TextCtrl(main_box, style=wx.TE_BESTWRAP)
        self.mvp_ip_address.Bind(wx.EVT_TEXT, self.on_mvp_ip_address_change)

        # buttons
        lst_mvp_ip_address_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_ip_address_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        mvp_ip_address_btn.SetToolTipString("Apply the new value")
        mvp_ip_address_btn.Bind(wx.EVT_BUTTON, self.on_apply_mvp_ip_address)
        lst_mvp_ip_address_szr.Add(mvp_ip_address_btn, 0, wx.ALIGN_RIGHT)

        mvp_ip_address_szr.Add(mvp_ip_address_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        mvp_ip_address_szr.Add(self.mvp_ip_address, 2, wx.EXPAND | wx.ALL, 5)
        mvp_ip_address_szr.Add(lst_mvp_ip_address_szr, 0, wx.EXPAND | wx.ALL, 5)

        #
        # mvp_listen_port
        #
        mvp_listen_port_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        mvp_listen_port_txt_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_listen_port_txt = wx.StaticText(self, label="Listen Port", style=wx.ALIGN_CENTER)
        mvp_listen_port_txt.Wrap(width=150)
        mvp_listen_port_txt_szr.AddStretchSpacer()
        mvp_listen_port_txt_szr.Add(mvp_listen_port_txt, 0, wx.EXPAND)
        mvp_listen_port_txt_szr.AddStretchSpacer()

        # integer control
        self.mvp_listen_port = intctrl.IntCtrl(main_box, min=0, max=999999, limited=True)
        self.mvp_listen_port.Bind(wx.EVT_TEXT, self.on_mvp_listen_port_change)

        # buttons
        lst_mvp_listen_port_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_listen_port_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        mvp_listen_port_btn.SetToolTipString("Apply the new value")
        mvp_listen_port_btn.Bind(wx.EVT_BUTTON, self.on_apply_mvp_listen_port)
        lst_mvp_listen_port_szr.Add(mvp_listen_port_btn, 0, wx.ALIGN_RIGHT)

        mvp_listen_port_szr.Add(mvp_listen_port_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        mvp_listen_port_szr.Add(self.mvp_listen_port, 2, wx.EXPAND | wx.ALL, 5)
        mvp_listen_port_szr.Add(lst_mvp_listen_port_szr, 0, wx.EXPAND | wx.ALL, 5)     
        
        #
        # mvp_listen_timeout
        #
        mvp_listen_timeout_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        mvp_listen_timeout_txt_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_listen_timeout_txt = wx.StaticText(self, label="Listen TimeOut", style=wx.ALIGN_CENTER)
        mvp_listen_timeout_txt.Wrap(width=150)
        mvp_listen_timeout_txt_szr.AddStretchSpacer()
        mvp_listen_timeout_txt_szr.Add(mvp_listen_timeout_txt, 0, wx.EXPAND)
        mvp_listen_timeout_txt_szr.AddStretchSpacer()

        # integer control
        self.mvp_listen_timeout = intctrl.IntCtrl(main_box, min=0, max=999999, limited=True)
        self.mvp_listen_timeout.Bind(wx.EVT_TEXT, self.on_mvp_listen_timeout_change)

        # buttons
        lst_mvp_listen_timeout_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_listen_timeout_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        mvp_listen_timeout_btn.SetToolTipString("Apply the new value")
        mvp_listen_timeout_btn.Bind(wx.EVT_BUTTON, self.on_apply_mvp_listen_timeout)
        lst_mvp_listen_timeout_szr.Add(mvp_listen_timeout_btn, 0, wx.ALIGN_RIGHT)

        mvp_listen_timeout_szr.Add(mvp_listen_timeout_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        mvp_listen_timeout_szr.Add(self.mvp_listen_timeout, 2, wx.EXPAND | wx.ALL, 5)
        mvp_listen_timeout_szr.Add(lst_mvp_listen_timeout_szr, 0, wx.EXPAND | wx.ALL, 5)     

        #
        # mvp_transmission_protocol
        #
        mvp_transmission_protocol_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        mvp_transmission_protocol_txt_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_transmission_protocol_txt = wx.StaticText(self, label="Transmission Protocol", style=wx.ALIGN_CENTER)
        mvp_transmission_protocol_txt.Wrap(width=150)
        mvp_transmission_protocol_txt_szr.AddStretchSpacer()
        mvp_transmission_protocol_txt_szr.Add(mvp_transmission_protocol_txt, 0, wx.EXPAND)
        mvp_transmission_protocol_txt_szr.AddStretchSpacer()

        # choice control
        source_choices = ["NAVO_ISS60", "UNDEFINED"]
        self.mvp_transmission_protocol = wx.ComboBox(main_box, choices=source_choices) #, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.mvp_transmission_protocol.Bind(wx.EVT_COMBOBOX, self.on_mvp_transmission_protocol_change)

        # buttons
        lst_mvp_transmission_protocol_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_transmission_protocol_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        mvp_transmission_protocol_btn.SetToolTipString("Apply the new value")
        mvp_transmission_protocol_btn.Bind(wx.EVT_BUTTON, self.on_apply_mvp_transmission_protocol)
        lst_mvp_transmission_protocol_szr.Add(mvp_transmission_protocol_btn, 0, wx.ALIGN_RIGHT)

        mvp_transmission_protocol_szr.Add(mvp_transmission_protocol_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        mvp_transmission_protocol_szr.Add(self.mvp_transmission_protocol, 2, wx.EXPAND | wx.ALL, 5)
        mvp_transmission_protocol_szr.Add(lst_mvp_transmission_protocol_szr, 0, wx.EXPAND | wx.ALL, 5)

        #
        # mvp_format
        #
        mvp_format_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        mvp_format_txt_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_format_txt = wx.StaticText(self, label="Format", style=wx.ALIGN_CENTER)
        mvp_format_txt.Wrap(width=150)
        mvp_format_txt_szr.AddStretchSpacer()
        mvp_format_txt_szr.Add(mvp_format_txt, 0, wx.EXPAND)
        mvp_format_txt_szr.AddStretchSpacer()

        # choice control
        source_choices = ["S12", "CALC", "ASVP"]
        self.mvp_format = wx.ComboBox(main_box, choices=source_choices) #, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.mvp_format.Bind(wx.EVT_COMBOBOX, self.on_mvp_format_change)

        # buttons
        lst_mvp_format_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_format_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        mvp_format_btn.SetToolTipString("Apply the new value")
        mvp_format_btn.Bind(wx.EVT_BUTTON, self.on_apply_mvp_format)
        lst_mvp_format_szr.Add(mvp_format_btn, 0, wx.ALIGN_RIGHT)

        mvp_format_szr.Add(mvp_format_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        mvp_format_szr.Add(self.mvp_format, 2, wx.EXPAND | wx.ALL, 5)
        mvp_format_szr.Add(lst_mvp_format_szr, 0, wx.EXPAND | wx.ALL, 5)
        
        #
        # mvp_instrument
        #
        mvp_instrument_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        mvp_instrument_txt_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_instrument_txt = wx.StaticText(self, label="Instrument", style=wx.ALIGN_CENTER)
        mvp_instrument_txt.Wrap(width=150)
        mvp_instrument_txt_szr.AddStretchSpacer()
        mvp_instrument_txt_szr.Add(mvp_instrument_txt, 0, wx.EXPAND)
        mvp_instrument_txt_szr.AddStretchSpacer()

        # choice control
        source_choices = ["AML_uSVP", "AML_uSVPT", "AML_Smart_SVP", "AML_uCTD", "AML_uCTD+", "Valeport_SVPT", 
                          "SBE_911+", "SBE_49"]
        self.mvp_instrument = wx.ComboBox(main_box, choices=source_choices) #, style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.mvp_instrument.Bind(wx.EVT_COMBOBOX, self.on_mvp_instrument_change)

        # buttons
        lst_mvp_instrument_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_instrument_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        mvp_instrument_btn.SetToolTipString("Apply the new value")
        mvp_instrument_btn.Bind(wx.EVT_BUTTON, self.on_apply_mvp_instrument)
        lst_mvp_instrument_szr.Add(mvp_instrument_btn, 0, wx.ALIGN_RIGHT)

        mvp_instrument_szr.Add(mvp_instrument_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        mvp_instrument_szr.Add(self.mvp_instrument, 2, wx.EXPAND | wx.ALL, 5)
        mvp_instrument_szr.Add(lst_mvp_instrument_szr, 0, wx.EXPAND | wx.ALL, 5)

        #
        # mvp_instrument_id
        #
        mvp_instrument_id_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        mvp_instrument_id_txt_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_instrument_id_txt = wx.StaticText(self, label="Instrument ID", style=wx.ALIGN_CENTER)
        mvp_instrument_id_txt.Wrap(width=150)
        mvp_instrument_id_txt_szr.AddStretchSpacer()
        mvp_instrument_id_txt_szr.Add(mvp_instrument_id_txt, 0, wx.EXPAND)
        mvp_instrument_id_txt_szr.AddStretchSpacer()

        # directory text ctrl
        self.mvp_instrument_id = wx.TextCtrl(main_box, style=wx.TE_BESTWRAP)
        self.mvp_instrument_id.Bind(wx.EVT_TEXT, self.on_mvp_instrument_id_change)

        # buttons
        lst_mvp_instrument_id_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_instrument_id_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        mvp_instrument_id_btn.SetToolTipString("Apply the new value")
        mvp_instrument_id_btn.Bind(wx.EVT_BUTTON, self.on_apply_mvp_instrument_id)
        lst_mvp_instrument_id_szr.Add(mvp_instrument_id_btn, 0, wx.ALIGN_RIGHT)

        mvp_instrument_id_szr.Add(mvp_instrument_id_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        mvp_instrument_id_szr.Add(self.mvp_instrument_id, 2, wx.EXPAND | wx.ALL, 5)
        mvp_instrument_id_szr.Add(lst_mvp_instrument_id_szr, 0, wx.EXPAND | wx.ALL, 5)

        #
        # mvp_winch_port
        #
        mvp_winch_port_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        mvp_winch_port_txt_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_winch_port_txt = wx.StaticText(self, label="Winch Port", style=wx.ALIGN_CENTER)
        mvp_winch_port_txt.Wrap(width=150)
        mvp_winch_port_txt_szr.AddStretchSpacer()
        mvp_winch_port_txt_szr.Add(mvp_winch_port_txt, 0, wx.EXPAND)
        mvp_winch_port_txt_szr.AddStretchSpacer()

        # integer control
        self.mvp_winch_port = intctrl.IntCtrl(main_box, min=0, max=999999, limited=True)
        self.mvp_winch_port.Bind(wx.EVT_TEXT, self.on_mvp_winch_port_change)

        # buttons
        lst_mvp_winch_port_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_winch_port_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        mvp_winch_port_btn.SetToolTipString("Apply the new value")
        mvp_winch_port_btn.Bind(wx.EVT_BUTTON, self.on_apply_mvp_winch_port)
        lst_mvp_winch_port_szr.Add(mvp_winch_port_btn, 0, wx.ALIGN_RIGHT)

        mvp_winch_port_szr.Add(mvp_winch_port_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        mvp_winch_port_szr.Add(self.mvp_winch_port, 2, wx.EXPAND | wx.ALL, 5)
        mvp_winch_port_szr.Add(lst_mvp_winch_port_szr, 0, wx.EXPAND | wx.ALL, 5)    

        #
        # mvp_fish_port
        #
        mvp_fish_port_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        mvp_fish_port_txt_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_fish_port_txt = wx.StaticText(self, label="Fish Port", style=wx.ALIGN_CENTER)
        mvp_fish_port_txt.Wrap(width=150)
        mvp_fish_port_txt_szr.AddStretchSpacer()
        mvp_fish_port_txt_szr.Add(mvp_fish_port_txt, 0, wx.EXPAND)
        mvp_fish_port_txt_szr.AddStretchSpacer()

        # integer control
        self.mvp_fish_port = intctrl.IntCtrl(main_box, min=0, max=999999, limited=True)
        self.mvp_fish_port.Bind(wx.EVT_TEXT, self.on_mvp_fish_port_change)

        # buttons
        lst_mvp_fish_port_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_fish_port_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        mvp_fish_port_btn.SetToolTipString("Apply the new value")
        mvp_fish_port_btn.Bind(wx.EVT_BUTTON, self.on_apply_mvp_fish_port)
        lst_mvp_fish_port_szr.Add(mvp_fish_port_btn, 0, wx.ALIGN_RIGHT)

        mvp_fish_port_szr.Add(mvp_fish_port_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        mvp_fish_port_szr.Add(self.mvp_fish_port, 2, wx.EXPAND | wx.ALL, 5)
        mvp_fish_port_szr.Add(lst_mvp_fish_port_szr, 0, wx.EXPAND | wx.ALL, 5)   

        #
        # mvp_nav_port
        #
        mvp_nav_port_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        mvp_nav_port_txt_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_nav_port_txt = wx.StaticText(self, label="Nav Port", style=wx.ALIGN_CENTER)
        mvp_nav_port_txt.Wrap(width=150)
        mvp_nav_port_txt_szr.AddStretchSpacer()
        mvp_nav_port_txt_szr.Add(mvp_nav_port_txt, 0, wx.EXPAND)
        mvp_nav_port_txt_szr.AddStretchSpacer()

        # integer control
        self.mvp_nav_port = intctrl.IntCtrl(main_box, min=0, max=999999, limited=True)
        self.mvp_nav_port.Bind(wx.EVT_TEXT, self.on_mvp_nav_port_change)

        # buttons
        lst_mvp_nav_port_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_nav_port_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        mvp_nav_port_btn.SetToolTipString("Apply the new value")
        mvp_nav_port_btn.Bind(wx.EVT_BUTTON, self.on_apply_mvp_nav_port)
        lst_mvp_nav_port_szr.Add(mvp_nav_port_btn, 0, wx.ALIGN_RIGHT)

        mvp_nav_port_szr.Add(mvp_nav_port_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        mvp_nav_port_szr.Add(self.mvp_nav_port, 2, wx.EXPAND | wx.ALL, 5)
        mvp_nav_port_szr.Add(lst_mvp_nav_port_szr, 0, wx.EXPAND | wx.ALL, 5)    

        #
        # mvp_system_port
        #
        mvp_system_port_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        mvp_system_port_txt_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_system_port_txt = wx.StaticText(self, label="System Port", style=wx.ALIGN_CENTER)
        mvp_system_port_txt.Wrap(width=150)
        mvp_system_port_txt_szr.AddStretchSpacer()
        mvp_system_port_txt_szr.Add(mvp_system_port_txt, 0, wx.EXPAND)
        mvp_system_port_txt_szr.AddStretchSpacer()

        # integer control
        self.mvp_system_port = intctrl.IntCtrl(main_box, min=0, max=999999, limited=True)
        self.mvp_system_port.Bind(wx.EVT_TEXT, self.on_mvp_system_port_change)

        # buttons
        lst_mvp_system_port_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_system_port_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        mvp_system_port_btn.SetToolTipString("Apply the new value")
        mvp_system_port_btn.Bind(wx.EVT_BUTTON, self.on_apply_mvp_system_port)
        lst_mvp_system_port_szr.Add(mvp_system_port_btn, 0, wx.ALIGN_RIGHT)

        mvp_system_port_szr.Add(mvp_system_port_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        mvp_system_port_szr.Add(self.mvp_system_port, 2, wx.EXPAND | wx.ALL, 5)
        mvp_system_port_szr.Add(lst_mvp_system_port_szr, 0, wx.EXPAND | wx.ALL, 5)    

        #
        # mvp_sw_version
        #
        mvp_sw_version_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        mvp_sw_version_txt_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_sw_version_txt = wx.StaticText(self, label="Software Version", style=wx.ALIGN_CENTER)
        mvp_sw_version_txt.Wrap(width=150)
        mvp_sw_version_txt_szr.AddStretchSpacer()
        mvp_sw_version_txt_szr.Add(mvp_sw_version_txt, 0, wx.EXPAND)
        mvp_sw_version_txt_szr.AddStretchSpacer()

        # directory text ctrl
        self.mvp_sw_version = wx.TextCtrl(main_box, style=wx.TE_BESTWRAP)
        self.mvp_sw_version.Bind(wx.EVT_TEXT, self.on_mvp_sw_version_change)

        # buttons
        lst_mvp_sw_version_szr = wx.BoxSizer(wx.VERTICAL)
        mvp_sw_version_btn = wx.Button(main_box, label="Apply", size=(80, -1))
        mvp_sw_version_btn.SetToolTipString("Apply the new value")
        mvp_sw_version_btn.Bind(wx.EVT_BUTTON, self.on_apply_mvp_sw_version)
        lst_mvp_sw_version_szr.Add(mvp_sw_version_btn, 0, wx.ALIGN_RIGHT)

        mvp_sw_version_szr.Add(mvp_sw_version_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        mvp_sw_version_szr.Add(self.mvp_sw_version, 2, wx.EXPAND | wx.ALL, 5)
        mvp_sw_version_szr.Add(lst_mvp_sw_version_szr, 0, wx.EXPAND | wx.ALL, 5)

        #
        # Add rows to the main box
        #
        main_box_szr.Add(mvp_ip_address_szr, 0, wx.EXPAND)
        main_box_szr.Add(mvp_listen_port_szr, 0, wx.EXPAND)
        main_box_szr.Add(mvp_listen_timeout_szr, 0, wx.EXPAND)
        main_box_szr.Add(mvp_transmission_protocol_szr, 0, wx.EXPAND)
        main_box_szr.Add(mvp_format_szr, 0, wx.EXPAND)
        main_box_szr.Add(mvp_instrument_szr, 0, wx.EXPAND)
        main_box_szr.Add(mvp_instrument_id_szr, 0, wx.EXPAND)
        main_box_szr.Add(mvp_winch_port_szr, 0, wx.EXPAND)
        main_box_szr.Add(mvp_fish_port_szr, 0, wx.EXPAND)
        main_box_szr.Add(mvp_nav_port_szr, 0, wx.EXPAND)
        main_box_szr.Add(mvp_system_port_szr, 0, wx.EXPAND)
        main_box_szr.Add(mvp_sw_version_szr, 0, wx.EXPAND)

        # Set the main box sizer and fit
        self.SetSizer(main_box_szr)
        self.Layout()

        # Update the data content
        self.update_data()

    def update_data(self, event=None):
        """ Update the data from the database """
        if self.settings_db.mvp_ip_address is None:
            self.mvp_ip_address.ChangeValue("")
        else:
            self.mvp_ip_address.ChangeValue(self.settings_db.mvp_ip_address)
        self.mvp_ip_address.SetForegroundColour(wx.BLACK)
        
        self.mvp_listen_port.ChangeValue(self.settings_db.mvp_listen_port)
        self.mvp_listen_port.SetColors(default_color=wx.BLACK)
        
        self.mvp_listen_timeout.ChangeValue(self.settings_db.mvp_listen_timeout)
        self.mvp_listen_timeout.SetColors(default_color=wx.BLACK)
        
        self.mvp_transmission_protocol.SetSelection(
            self.mvp_transmission_protocol.FindString(str(self.settings_db.mvp_transmission_protocol)))
        self.mvp_transmission_protocol.SetOwnBackgroundColour(wx.WHITE)
        
        self.mvp_format.SetSelection(
            self.mvp_format.FindString(str(self.settings_db.mvp_format)))
        self.mvp_format.SetOwnBackgroundColour(wx.WHITE)
        
        self.mvp_instrument.SetSelection(
            self.mvp_instrument.FindString(str(self.settings_db.mvp_instrument)))
        self.mvp_instrument.SetOwnBackgroundColour(wx.WHITE)

        if self.settings_db.mvp_instrument_id is None:
            self.mvp_instrument_id.ChangeValue("")
        else:
            self.mvp_instrument_id.ChangeValue(self.settings_db.mvp_instrument_id)
        self.mvp_instrument_id.SetForegroundColour(wx.BLACK)

        self.mvp_winch_port.ChangeValue(self.settings_db.mvp_winch_port)
        self.mvp_winch_port.SetColors(default_color=wx.BLACK)
        
        self.mvp_fish_port.ChangeValue(self.settings_db.mvp_fish_port)
        self.mvp_fish_port.SetColors(default_color=wx.BLACK)

        self.mvp_nav_port.ChangeValue(self.settings_db.mvp_nav_port)
        self.mvp_nav_port.SetColors(default_color=wx.BLACK)

        self.mvp_system_port.ChangeValue(self.settings_db.mvp_system_port)
        self.mvp_system_port.SetColors(default_color=wx.BLACK)

        if self.settings_db.mvp_sw_version is None:
            self.mvp_sw_version.ChangeValue("")
        else:
            self.mvp_sw_version.ChangeValue(self.settings_db.mvp_sw_version)
        self.mvp_sw_version.SetForegroundColour(wx.BLACK)

    # =================================================== 

    def on_mvp_ip_address_change(self, event):
        """ Method called when the waiting time is changed """
        log.debug("Changed MVP IP address: %s" % self.mvp_ip_address.GetValue())
        self.mvp_ip_address.SetForegroundColour(wx.RED)

    def on_apply_mvp_ip_address(self, event):
        log.debug("Apply new MVP IP address: %s" % self.mvp_ip_address.GetValue())
        if self.mvp_ip_address.GetValue() == "":
            self.settings_db.mvp_ip_address = "127.0.0.1"
        else:
            self.settings_db.mvp_ip_address = self.mvp_ip_address.GetValue()
        self.mvp_ip_address.SetForegroundColour(wx.BLACK)
        self.update_data()

    def on_mvp_listen_port_change(self, event):
        log.debug("Changed listen port: %d" % self.mvp_listen_port.GetValue())
        self.mvp_listen_port.SetColors(default_color=wx.RED)

    def on_apply_mvp_listen_port(self, event):
        log.debug("Apply new listen port: %d" % self.mvp_listen_port.GetValue())
        self.mvp_listen_port.SetColors(default_color=wx.BLACK)
        self.settings_db.mvp_listen_port = self.mvp_listen_port.GetValue()
        self.update_data()
        
    def on_mvp_listen_timeout_change(self, event):
        log.debug("Changed listen port: %d" % self.mvp_listen_timeout.GetValue())
        self.mvp_listen_timeout.SetColors(default_color=wx.RED)

    def on_apply_mvp_listen_timeout(self, event):
        log.debug("Apply new listen port: %d" % self.mvp_listen_timeout.GetValue())
        self.mvp_listen_timeout.SetColors(default_color=wx.BLACK)
        self.settings_db.mvp_listen_timeout = self.mvp_listen_timeout.GetValue()
        self.update_data()

    def on_mvp_transmission_protocol_change(self, event):
        log.debug("SIS auto apply manul cast: %d(%s)"
                  % (self.mvp_transmission_protocol.GetSelection(),
                     self.mvp_transmission_protocol.GetString(self.mvp_transmission_protocol.GetSelection())))
        self.mvp_transmission_protocol.SetOwnBackgroundColour(wx.RED)

    def on_apply_mvp_transmission_protocol(self, event):
        log.debug("Apply MVP transmission protocol: %d(%s)"
                  % (self.mvp_transmission_protocol.GetSelection(),
                     self.mvp_transmission_protocol.GetString(self.mvp_transmission_protocol.GetSelection())))
        self.mvp_transmission_protocol.SetOwnBackgroundColour(wx.RED)
        self.settings_db.mvp_transmission_protocol = \
            self.mvp_transmission_protocol.GetString(self.mvp_transmission_protocol.GetSelection())
        self.update_data()
        
    def on_mvp_instrument_change(self, event):
        log.debug("MVP instrument: %d(%s)"
                  % (self.mvp_instrument.GetSelection(),
                     self.mvp_instrument.GetString(self.mvp_instrument.GetSelection())))
        self.mvp_instrument.SetOwnBackgroundColour(wx.RED)

    def on_apply_mvp_instrument(self, event):
        log.debug("Apply MVP instrument: %d(%s)"
                  % (self.mvp_instrument.GetSelection(),
                     self.mvp_instrument.GetString(self.mvp_instrument.GetSelection())))
        self.mvp_instrument.SetOwnBackgroundColour(wx.RED)
        self.settings_db.mvp_instrument = \
            self.mvp_instrument.GetString(self.mvp_instrument.GetSelection())
        self.update_data()

    def on_mvp_instrument_id_change(self, event):
        """ Method called when the waiting time is changed """
        log.debug("Changed Instrument ID: %s" % self.mvp_instrument_id.GetValue())
        self.mvp_instrument_id.SetForegroundColour(wx.RED)

    def on_apply_mvp_instrument_id(self, event):
        log.debug("Apply new Instrument ID: %s" % self.mvp_instrument_id.GetValue())
        self.settings_db.mvp_instrument_id = self.mvp_instrument_id.GetValue()
        self.mvp_instrument_id.SetForegroundColour(wx.BLACK)
        self.update_data()

    def on_mvp_format_change(self, event):
        log.debug("MVP format: %d(%s)"
                  % (self.mvp_format.GetSelection(),
                     self.mvp_format.GetString(self.mvp_format.GetSelection())))
        self.mvp_format.SetOwnBackgroundColour(wx.RED)

    def on_apply_mvp_format(self, event):
        log.debug("Apply MVP format: %d(%s)"
                  % (self.mvp_format.GetSelection(),
                     self.mvp_format.GetString(self.mvp_format.GetSelection())))
        self.mvp_format.SetOwnBackgroundColour(wx.RED)
        self.settings_db.mvp_format = \
            self.mvp_format.GetString(self.mvp_format.GetSelection())
        self.update_data()
        
    def on_mvp_winch_port_change(self, event):
        log.debug("Changed winch port: %d" % self.mvp_winch_port.GetValue())
        self.mvp_winch_port.SetColors(default_color=wx.RED)

    def on_apply_mvp_winch_port(self, event):
        log.debug("Apply new winch port: %d" % self.mvp_winch_port.GetValue())
        self.mvp_winch_port.SetColors(default_color=wx.BLACK)
        self.settings_db.mvp_winch_port = self.mvp_winch_port.GetValue()
        self.update_data()

    def on_mvp_fish_port_change(self, event):
        log.debug("Changed fish port: %d" % self.mvp_fish_port.GetValue())
        self.mvp_fish_port.SetColors(default_color=wx.RED)

    def on_apply_mvp_fish_port(self, event):
        log.debug("Apply new fish port: %d" % self.mvp_fish_port.GetValue())
        self.mvp_fish_port.SetColors(default_color=wx.BLACK)
        self.settings_db.mvp_fish_port = self.mvp_fish_port.GetValue()
        self.update_data()
        
    def on_mvp_nav_port_change(self, event):
        log.debug("Changed nav port: %d" % self.mvp_nav_port.GetValue())
        self.mvp_nav_port.SetColors(default_color=wx.RED)

    def on_apply_mvp_nav_port(self, event):
        log.debug("Apply new nav port: %d" % self.mvp_nav_port.GetValue())
        self.mvp_nav_port.SetColors(default_color=wx.BLACK)
        self.settings_db.mvp_nav_port = self.mvp_nav_port.GetValue()
        self.update_data()
        
    def on_mvp_system_port_change(self, event):
        log.debug("Changed system port: %d" % self.mvp_system_port.GetValue())
        self.mvp_system_port.SetColors(default_color=wx.RED)

    def on_apply_mvp_system_port(self, event):
        log.debug("Apply new system port: %d" % self.mvp_system_port.GetValue())
        self.mvp_system_port.SetColors(default_color=wx.BLACK)
        self.settings_db.mvp_system_port = self.mvp_system_port.GetValue()
        self.update_data()

    def on_mvp_sw_version_change(self, event):
        """ Method called when the waiting time is changed """
        log.debug("Changed MVP IP address: %s" % self.mvp_sw_version.GetValue())
        self.mvp_sw_version.SetForegroundColour(wx.RED)

    def on_apply_mvp_sw_version(self, event):
        log.debug("Apply new MVP IP address: %s" % self.mvp_sw_version.GetValue())
        if self.mvp_sw_version.GetValue() == "":
            self.settings_db.mvp_sw_version = "127.0.0.1"
        else:
            self.settings_db.mvp_sw_version = self.mvp_sw_version.GetValue()
        self.mvp_sw_version.SetForegroundColour(wx.BLACK)
        self.update_data()