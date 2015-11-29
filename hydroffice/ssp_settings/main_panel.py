from __future__ import absolute_import, division, print_function, unicode_literals

import wx
import os
import logging

log = logging.getLogger(__name__)

from hydroffice.ssp.settings.db import SettingsDb, DbSettingsError


class MainPanel(wx.Panel):
    def __init__(self, parent_frame, db, *args, **kwargs):
        """ This panel provides user interaction with Settings profiles at high level """
        super(MainPanel, self).__init__(*args, **kwargs)

        # Store an handle to the Settings DB
        self.parent_frame = parent_frame
        self.settings_db = db
        self.selected_profile_item = 0

        # Main box
        main_box = wx.StaticBox(self)
        main_box_szr = wx.StaticBoxSizer(main_box, wx.VERTICAL)

        #
        # Active profile
        #
        act_profile_szr = wx.BoxSizer(wx.HORIZONTAL)
        self.act_profile = wx.StaticText(self, label="Settings from Active Profile:", style=wx.ALIGN_CENTER)
        act_profile_szr.AddStretchSpacer()
        act_profile_szr.Add(self.act_profile, 0, wx.EXPAND)
        act_profile_szr.AddStretchSpacer()

        #
        # List profiles
        #
        lst_profiles_szr = wx.BoxSizer(wx.HORIZONTAL)

        # text
        lst_profiles_txt_szr = wx.BoxSizer(wx.VERTICAL)
        lst_profiles_txt = wx.StaticText(self, label="Available Settings Profiles", style=wx.ALIGN_CENTER)
        lst_profiles_txt.Wrap(width=100)
        lst_profiles_txt_szr.AddStretchSpacer()
        lst_profiles_txt_szr.Add(lst_profiles_txt, 0, wx.EXPAND)
        lst_profiles_txt_szr.AddStretchSpacer()

        # list
        self.lst_profiles = wx.ListCtrl(main_box, style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SINGLE_SEL)
        self.lst_profiles.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        self.lst_profiles.InsertColumn(0, 'ID')
        self.lst_profiles.InsertColumn(1, 'Name', width=120)
        self.lst_profiles.InsertColumn(2, 'Status')
        # print(self.settings_db.settings_list)

        # buttons
        lst_profiles_buttons_szr = wx.BoxSizer(wx.VERTICAL)
        new_profile_btn = wx.Button(main_box, label="New Profile")
        new_profile_btn.SetToolTipString("Create a new profile")
        new_profile_btn.Bind(wx.EVT_BUTTON, self.on_new_profile)
        lst_profiles_buttons_szr.Add(new_profile_btn, 0, wx.EXPAND)
        del_profile_btn = wx.Button(main_box, label="Delete Profile")
        del_profile_btn.SetToolTipString("Delete the selected profile")
        del_profile_btn.Bind(wx.EVT_BUTTON, self.on_delete_profile)
        lst_profiles_buttons_szr.Add(del_profile_btn, 0, wx.EXPAND)
        activate_profile_btn = wx.Button(main_box, label="Activate Profile")
        activate_profile_btn.SetToolTipString("Activate the selected profile")
        activate_profile_btn.Bind(wx.EVT_BUTTON, self.on_activate_profile)
        lst_profiles_buttons_szr.Add(activate_profile_btn, 0, wx.EXPAND)
        update_data_btn = wx.Button(main_box, label="Refresh")
        update_data_btn.SetToolTipString("Refresh client list")
        update_data_btn.Bind(wx.EVT_BUTTON, self.update_data)
        lst_profiles_buttons_szr.Add(update_data_btn, 0, wx.EXPAND)

        lst_profiles_szr.Add(lst_profiles_txt_szr, 1, wx.EXPAND | wx.ALL, 5)
        lst_profiles_szr.Add(self.lst_profiles, 2, wx.EXPAND | wx.ALL, 5)
        lst_profiles_szr.Add(lst_profiles_buttons_szr, 1, wx.EXPAND | wx.ALL, 5)

        # Add rows to the main box
        main_box_szr.Add(act_profile_szr, 0, wx.EXPAND)
        main_box_szr.Add(lst_profiles_szr, 0, wx.EXPAND)

        # Set the main box sizer and fit
        self.SetSizer(main_box_szr)
        self.Layout()

        # Update the data content
        self.update_data()

    def update_data(self, event=None):
        """ Update the data from the database """
        # update the active profile
        self.act_profile.SetLabel("Settings from Active Profile: %s [#%02d]"
                                  % (self.settings_db.active_profile_name,
                                     self.settings_db.active_profile_id))

        # update the list of profiles
        self.lst_profiles.DeleteAllItems()
        index = 0
        for settings in self.settings_db.profiles_list:
            self.lst_profiles.InsertStringItem(index, "%02d" % settings[0])

            self.lst_profiles.SetStringItem(index, 1, settings[1])
            self.lst_profiles.SetStringItem(index, 2, settings[2])

            index += 1
        # set the selected item
        # check for inconsistencies
        if self.selected_profile_item >= self.lst_profiles.ItemCount:
            self.selected_profile_item = 0
        self.lst_profiles.Select(self.selected_profile_item, True)

    def on_item_selected(self, event):
        """ On change of the profile seleted, updated the panels """
        self.selected_profile_item = event.m_itemIndex
        self.parent_frame.selected_profile_id = int(self.lst_profiles.GetItem(self.selected_profile_item, 0).GetText())
        self.parent_frame.selected_profile_name = self.lst_profiles.GetItem(self.selected_profile_item, 1).GetText()
        log.debug("selected profile item: %d (%s #%d)"
                  % (self.selected_profile_item, self.parent_frame.selected_profile_name,
                     self.parent_frame.selected_profile_id))

    def on_new_profile(self, event):
        """ Create a new profile """
        log.debug("Create a new profile")

        while True:
            dlg = wx.TextEntryDialog(self, 'New profile name:','New profile', '', style=wx.OK)
            dlg.ShowModal()
            new_profile_name = dlg.GetValue()
            dlg.Destroy()
            log.debug("User selected name: %s" % new_profile_name)

            if len(new_profile_name) == 0:
                dlg = wx.MessageDialog(self, 'Invalid empty string for profile name!',
                                       'Invalid input', wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                continue
            elif self.settings_db.profile_exists(new_profile_name):
                dlg = wx.MessageDialog(self, 'A profile with the same name (\"%s\") already exists' % new_profile_name,
                                       'Invalid input', wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                continue
            else:
                try:
                    self.settings_db.add_profile(new_profile_name)
                except DbSettingsError as e:
                    dlg = wx.MessageDialog(self, '%s' % e, 'Profile creation error', wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                break

        self.update_data()

    def on_delete_profile(self, event):
        """ Delete an existing profile """
        log.debug("Delete existing profile: %s" % self.parent_frame.selected_profile_name)

        if self.parent_frame.selected_profile_name == self.settings_db.active_profile_name:
            dlg = wx.MessageDialog(self, 'The profile \"%s\" is active!' % self.parent_frame.selected_profile_name,
                                   'Invalid deletion', wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            try:
                self.settings_db.delete_profile(self.parent_frame.selected_profile_name)
            except DbSettingsError as e:
                dlg = wx.MessageDialog(self, '%s' % e, 'Profile deletion error', wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
        self.update_data()

    def on_activate_profile(self, event):
        """ Activate an existing profile """
        log.debug("Activate profile: %s" % self.parent_frame.selected_profile_name)

        if self.parent_frame.selected_profile_name == self.settings_db.active_profile_name:
            dlg = wx.MessageDialog(self, 'The profile \"%s\" is already active!'
                                   % self.parent_frame.selected_profile_name,
                                   'Invalid activation', wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            try:
                self.settings_db.activate_profile(self.parent_frame.selected_profile_name)
            except DbSettingsError as e:
                dlg = wx.MessageDialog(self, '%s' % e, 'Profile activation error', wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
        self.update_data()


