from __future__ import absolute_import, division, print_function, unicode_literals

import wx
import logging

log = logging.getLogger(__name__)

from . import sspmanager


def gui():
    app = wx.App(False)
    svp_editor = sspmanager.SSPManager()
    app.SetTopWindow(svp_editor)
    svp_editor.Show()
    app.MainLoop()

