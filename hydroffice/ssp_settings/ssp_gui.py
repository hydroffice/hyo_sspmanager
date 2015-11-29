from __future__ import absolute_import, division, print_function, unicode_literals

import wx
import logging

log = logging.getLogger(__name__)

from . import ssp_settings

from wx.lib.mixins.inspection import InspectionMixin

def gui():
    app = wx.App(False, InspectionMixin)
    svp_editor = ssp_settings.SSPSettings(parent=None)
    app.SetTopWindow(svp_editor)
    svp_editor.Show()
    app.MainLoop()

