from __future__ import absolute_import, division, print_function, unicode_literals

import wx
import os


class GeoMonitorBase(wx.Frame):

    here = os.path.abspath(os.path.dirname(__file__))

    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        
        # Menu Bar
        self.GeographicMonitorFrame_menubar = wx.MenuBar()
        self.SetMenuBar(self.GeographicMonitorFrame_menubar)
        # Menu Bar end
        self.GeographicMonitorFrame_statusbar = self.CreateStatusBar(2, 0)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        favicon = wx.Icon(os.path.join(self.here, 'favicon.ico'), wx.BITMAP_TYPE_ICO, 32, 32)
        wx.Frame.SetIcon(self, favicon)

        if os.name == 'nt':
            # This is needed to display the app icon on the taskbar on Windows 7
            import ctypes
            app_id = 'SSP Manager - GeoMonitor'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

        self.SetTitle("GeoMonitor")
        self.SetSize((500, 500))
        self.GeographicMonitorFrame_statusbar.SetStatusWidths([-1, 400])
        # statusbar fields
        GeographicMonitorFrame_statusbar_fields = ["", ""]
        for i in range(len(GeographicMonitorFrame_statusbar_fields)):
            self.GeographicMonitorFrame_statusbar.SetStatusText(GeographicMonitorFrame_statusbar_fields[i], i)

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer_1)
        self.Layout()
        self.SetSize((500, 500))
