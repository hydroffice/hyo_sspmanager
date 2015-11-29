from __future__ import absolute_import, division, print_function, unicode_literals

import wx
import os
import logging

log = logging.getLogger(__name__)

from hydroffice.ssp.settings.db import SettingsDb

from .main_panel import MainPanel
from .common_panel import CommonPanel
from .sources_panel import SourcesPanel
from .client_panel import ClientPanel
from .export_panel import ExportPanel
from .server_panel import ServerPanel
from .kongsberg_panel import KongsbergPanel
from .sippican_panel import SippicanPanel
from .mvp_panel import MVPPanel


class SSPSettings(wx.Frame):

    here = os.path.abspath(os.path.dirname(__file__))

    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.db = SettingsDb()
        self.selected_profile_id = 0
        self.selected_profile_name = 0

        self.SetTitle("SSP Settings")
        self.SetSize((800, 550))
        self.SetSizeHints(500, 400, 900, 600)
        favicon = wx.Icon(os.path.join(self.here, 'media', 'favicon.png'), wx.BITMAP_TYPE_PNG, 32, 32)
        wx.Frame.SetIcon(self, favicon)

        if os.name == 'nt':
            # This is needed to display the app icon on the taskbar on Windows 7
            import ctypes
            app_id = 'SSP Settings'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_page_change)

        p = wx.Panel(self)
        self.nb = wx.Notebook(p)
        self.nb.AddPage(MainPanel(parent=self.nb, parent_frame=self, db=self.db), "Main")
        self.nb.AddPage(CommonPanel(parent=self.nb, parent_frame=self, db=self.db), "Common")
        self.nb.AddPage(SourcesPanel(parent=self.nb, parent_frame=self, db=self.db), "Sources")
        self.nb.AddPage(ClientPanel(parent=self.nb, parent_frame=self, db=self.db), "Client")
        self.nb.AddPage(ExportPanel(parent=self.nb, parent_frame=self, db=self.db), "Export")
        self.nb.AddPage(ServerPanel(parent=self.nb, parent_frame=self, db=self.db), "Server")
        self.nb.AddPage(KongsbergPanel(parent=self.nb, parent_frame=self, db=self.db), "Kongsberg")
        self.nb.AddPage(SippicanPanel(parent=self.nb, parent_frame=self, db=self.db), "Sippican")
        self.nb.AddPage(MVPPanel(parent=self.nb, parent_frame=self, db=self.db), "MVP")

        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.ALL | wx.EXPAND, 3)
        p.SetSizer(sizer)

    def on_close(self, evt):
        log.debug("close")
        self.db.close()
        self.Destroy()

    def on_page_change(self, evt):
        page_id = evt.GetSelection()
        log.debug("Page change: %s" % page_id)
        self.nb.GetPage(page_id).update_data()


