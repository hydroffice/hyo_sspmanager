from __future__ import absolute_import, division, print_function, unicode_literals

import wx
import os
import logging

log = logging.getLogger(__name__)

from hydroffice.ssp.settings.db import SettingsDb, DbSettingsError


class ClientPanel(wx.Panel):
    def __init__(self, parent_frame, db, *args, **kwargs):
        """ This panel provides user interaction to common settings """
        super(ClientPanel, self).__init__(*args, **kwargs)

        # Store an handle to the Settings DB
        self.parent_frame = parent_frame
        self.settings_db = db
        self.selected_client_item = 0
        self.selected_client_id = 0
        self.selected_client_name = None

        # Main box
        main_box = wx.StaticBox(self)
        main_box_szr = wx.StaticBoxSizer(main_box, wx.VERTICAL)

        #
        # List clients
        #
        lst_clients_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        lst_clients_txt_szr = wx.BoxSizer(wx.VERTICAL)
        lst_clients_txt = wx.StaticText(self, label="Available Clients", style=wx.ALIGN_CENTER)
        lst_clients_txt.Wrap(width=100)
        lst_clients_txt_szr.AddStretchSpacer()
        lst_clients_txt_szr.Add(lst_clients_txt, 0, wx.EXPAND)
        lst_clients_txt_szr.AddStretchSpacer()

        # list
        self.lst_clients = wx.ListCtrl(main_box, style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SINGLE_SEL)
        self.lst_clients.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        self.lst_clients.InsertColumn(0, 'ID')
        self.lst_clients.InsertColumn(1, 'Name', width=120)
        self.lst_clients.InsertColumn(2, 'IP')
        self.lst_clients.InsertColumn(3, 'Port')
        self.lst_clients.InsertColumn(4, 'Protocol')
        # print(self.settings_db.settings_list)

        # buttons
        lst_clients_buttons_szr = wx.BoxSizer(wx.VERTICAL)
        new_client_btn = wx.Button(main_box, label="New Client")
        new_client_btn.SetToolTipString("Create a new client")
        new_client_btn.Bind(wx.EVT_BUTTON, self.on_new_client)
        lst_clients_buttons_szr.Add(new_client_btn, 0, wx.EXPAND)
        del_client_btn = wx.Button(main_box, label="Delete Client")
        del_client_btn.SetToolTipString("Delete the selected client")
        del_client_btn.Bind(wx.EVT_BUTTON, self.on_delete_client)
        lst_clients_buttons_szr.Add(del_client_btn, 0, wx.EXPAND)
        update_data_btn = wx.Button(main_box, label="Refresh")
        update_data_btn.SetToolTipString("Refresh client list")
        update_data_btn.Bind(wx.EVT_BUTTON, self.update_data)
        lst_clients_buttons_szr.Add(update_data_btn, 0, wx.EXPAND)

        lst_clients_szr.Add(lst_clients_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        lst_clients_szr.Add(self.lst_clients, 3, wx.EXPAND | wx.ALL, 5)
        lst_clients_szr.Add(lst_clients_buttons_szr, 1, wx.EXPAND | wx.ALL, 5)

        # Add rows to the main box
        main_box_szr.Add(lst_clients_szr, 0, wx.EXPAND)

        # Set the main box sizer and fit
        self.SetSizer(main_box_szr)
        self.Layout()

        # Update the data content
        self.update_data()

    def update_data(self, event=None):
        """ Update the data from the database """
        # update the list of profiles
        self.lst_clients.DeleteAllItems()
        index = 0
        for settings in self.settings_db.client_list:
            self.lst_clients.InsertStringItem(index, "%02d" % settings[0])

            self.lst_clients.SetStringItem(index, 1, settings[1])
            self.lst_clients.SetStringItem(index, 2, settings[2])
            self.lst_clients.SetStringItem(index, 3, "%d" % settings[3])
            self.lst_clients.SetStringItem(index, 4, settings[4])

            index += 1
        # set the selected item
        # check for inconsistencies
        if self.selected_client_item >= self.lst_clients.ItemCount:
            self.selected_client_item = 0
        self.lst_clients.Select(self.selected_client_item, True)

    def on_item_selected(self, event):
        """ On change of the profile seleted, updated the panels """
        self.selected_client_item = event.m_itemIndex
        self.selected_client_id = int(self.lst_clients.GetItem(self.selected_client_item, 0).GetText())
        self.selected_client_name = self.lst_clients.GetItem(self.selected_client_item, 1).GetText()
        log.debug("selected client item: %d (%s #%d)"
                  % (self.selected_client_item, self.selected_client_name, self.selected_client_id))

    def on_new_client(self, event):
        """ Create a new client """
        log.debug("Create a new client")

        while True:
            dlg = wx.TextEntryDialog(self, 'New client name:','New client', '', style=wx.OK)
            dlg.ShowModal()
            new_client_name = dlg.GetValue()
            dlg.Destroy()
            log.debug("User selected name: %s" % new_client_name)

            if len(new_client_name) == 0:
                dlg = wx.MessageDialog(self, 'Invalid empty string for client name!',
                                       'Invalid input', wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                continue
            elif self.settings_db.client_exists(new_client_name):
                dlg = wx.MessageDialog(self, 'A client with the same name (\"%s\") already exists' % new_client_name,
                                       'Invalid input', wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                continue
            else:
                ip = self._get_client_ip()
                port = self._get_client_port()
                protocol = self._get_client_protocol()

                try:
                    self.settings_db.add_client(new_client_name, ip, port, protocol)
                except DbSettingsError as e:
                    dlg = wx.MessageDialog(self, '%s' % e, 'Client creation error', wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                break

        self.update_data()

    def _get_client_ip(self):
        while True:
            dlg = wx.TextEntryDialog(self, 'New client IP (e.g., 127.0.0.1):', 'New IP', '', style=wx.OK)
            dlg.ShowModal()
            new_client_IP = dlg.GetValue()
            dlg.Destroy()
            log.debug("User selected IP: %s" % new_client_IP)

            if len(new_client_IP) == 0:
                dlg = wx.MessageDialog(self, 'Invalid empty string for client IP!',
                                       'Invalid input', wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                continue
            elif not self._valid_IP(new_client_IP):
                dlg = wx.MessageDialog(self, 'Invalid string for client IP!',
                                       'Invalid input', wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                continue
            else:
                return new_client_IP

    def _valid_IP(self, ip):
        tokens = ip.split('.')
        if len(tokens) != 4:
            return False
        for token in tokens:
            try:
                int_token = int(token)
                if (int_token < 0) or (int_token > 255):
                    return False
            except ValueError:
                return False
        return True

    def _get_client_port(self):
        while True:
            dlg = wx.TextEntryDialog(self, 'New client Port (e.g., 4001):', 'New Port', '', style=wx.OK)
            dlg.ShowModal()
            new_client_port = dlg.GetValue()
            dlg.Destroy()
            log.debug("User selected port: %s" % new_client_port)

            try:
                new_client_port = int(new_client_port)
            except ValueError:
                dlg = wx.MessageDialog(self, 'Invalid input for client port!',
                                       'Invalid input', wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                continue

            if (new_client_port < 0) or (new_client_port > 999999):
                dlg = wx.MessageDialog(self, 'Invalid input for client port!',
                                       'Invalid input', wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                continue
            else:
                return new_client_port

    def _get_client_protocol(self):
        while True:
            dlg = wx.TextEntryDialog(self, 'Protocol (input SIS, HYPACK, PDS2000, or QINSY):', 'New Protocol', '', style=wx.OK)
            dlg.ShowModal()
            new_client_protocol = dlg.GetValue()
            dlg.Destroy()
            log.debug("User selected protocol: %s" % new_client_protocol)

            if new_client_protocol not in ("SIS", "HYPACK", "PDS2000", "QINSY"):
                dlg = wx.MessageDialog(self, 'Invalid input for client protocol!',
                                       'Invalid input', wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                continue
            else:
                return new_client_protocol

    def on_delete_client(self, event):
        """ Delete an existing client """
        log.debug("Delete existing client: %s" % self.selected_client_name)

        try:
            self.settings_db.delete_client(self.selected_client_name)
        except DbSettingsError as e:
            dlg = wx.MessageDialog(self, '%s' % e, 'Client deletion error', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        self.update_data()
