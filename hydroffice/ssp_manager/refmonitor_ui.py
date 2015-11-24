from __future__ import absolute_import, division, print_function, unicode_literals

import wx
import os


class RefMonitorBase(wx.Frame):

    here = os.path.abspath(os.path.dirname(__file__))

    def __init__(self, *args, **kwds):
        # begin wxGlade: RefractionMonitorBase.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        
        # Menu Bar
        self.RefractionMonitorFrame_menubar = wx.MenuBar()
        self.SetMenuBar(self.RefractionMonitorFrame_menubar)
        # Menu Bar end
        self.RefractionMonitorFrame_statusbar = self.CreateStatusBar(2, 0)
        self.SVCorrectorSlider = wx.Slider(self, -1, 0, -100, 100,
                                           style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
        self.SVCorrectorSlider.SetTickFreq(10, 1)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_COMMAND_SCROLL, self.on_ssp_scroll, self.SVCorrectorSlider)
        # end wxGlade

    def __set_properties(self):
        favicon = wx.Icon(os.path.join(self.here, 'favicon.ico'), wx.BITMAP_TYPE_ICO, 32, 32)
        wx.Frame.SetIcon(self, favicon)

        if os.name == 'nt':
            # This is needed to display the app icon on the taskbar on Windows 7
            import ctypes
            app_id = 'SSP Manager - Refraction Monitor'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

        # begin wxGlade: RefractionMonitorBase.__set_properties
        self.SetTitle("Refraction Monitor")
        self.SetSize((700, 700))
        self.RefractionMonitorFrame_statusbar.SetStatusWidths([-1, 400])
        # statusbar fields
        RefractionMonitorFrame_statusbar_fields = ["", ""]
        for i in range(len(RefractionMonitorFrame_statusbar_fields)):
            self.RefractionMonitorFrame_statusbar.SetStatusText(RefractionMonitorFrame_statusbar_fields[i], i)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: RefractionMonitorBase.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer_1)
        self.Layout()
        self.SetSize((700, 700))
        # end wxGlade

    def on_ssp_scroll(self, event):  # wxGlade: RefractionMonitorBase.<event_handler>
        print("Event handler `OnSVScroll' not implemented!")
        event.Skip()


if __name__ == "__main__":
    app = wx.App(False)
    RefractionMonitorFrame = RefMonitorBase(None, -1, "")
    app.SetTopWindow(RefractionMonitorFrame)
    RefractionMonitorFrame.Show()
    app.MainLoop()
