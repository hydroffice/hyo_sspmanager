from __future__ import absolute_import, division, print_function, unicode_literals

import wx
import os


class SettingsViewerBase(wx.Frame):

    here = os.path.abspath(os.path.dirname(__file__))

    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        
        # Menu Bar
        self.SettingsViewerFrame_menubar = wx.MenuBar()
        self.SetMenuBar(self.SettingsViewerFrame_menubar)
        # Menu Bar end
        self.SettingsViewerFrame_statusbar = self.CreateStatusBar(2, 0)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        favicon = wx.Icon(os.path.join(self.here, 'favicon.ico'), wx.BITMAP_TYPE_ICO, 32, 32)
        wx.Frame.SetIcon(self, favicon)

        if os.name == 'nt':
            # This is needed to display the app icon on the taskbar on Windows 7
            import ctypes
            app_id = 'SSP Manager - Setting Viewer'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

        self.SetTitle("Settings Viewer")
        self.SetSize((500, 500))
        self.SettingsViewerFrame_statusbar.SetStatusWidths([-1, 400])
        # statusbar fields
        SettingsViewerFrame_statusbar_fields = ["", ""]
        for i in range(len(SettingsViewerFrame_statusbar_fields)):
            self.SettingsViewerFrame_statusbar.SetStatusText(SettingsViewerFrame_statusbar_fields[i], i)

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer_1)
        self.Layout()
        self.SetSize((500, 500))
