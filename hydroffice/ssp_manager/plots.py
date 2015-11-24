from __future__ import absolute_import, division, print_function, unicode_literals

from . import wxmpl  # local version of this module, since Pydro's one has an issue


class WxPlots(wxmpl.PlotPanel):
    def __init__(self, parent, id=-1, size=(6.0, 3.70), dpi=120,
                 cursor=True, location=True, crosshairs=True,
                 selection=True, zoom=False, autoscaleUnzoom=True):
        wxmpl.PlotPanel.__init__(self, parent, id, size=size, dpi=dpi,
                                 cursor=cursor, location=location, crosshairs=crosshairs,
                                 selection=selection, zoom=zoom, autoscaleUnzoom=zoom)
        self.callback_right_click_up = self._empty_func
        self.callback_right_click_down = self._empty_func

    @classmethod
    def _empty_func(cls, evt):
        """empty callable to be overloaded"""
        print("overload me! %s" % evt)

    def _onRightButtonDown(self, evt):
        """
        Overrides the right-click event handler
        """
        if self.callback_right_click_down:
            #x, y = self._get_canvas_xy(evt)
            self.callback_right_click_down(evt)

    def _onRightButtonUp(self, evt):
        """
        Overrides the right-click-release event handler
        """
        if self.callback_right_click_up:
            self.callback_right_click_up(evt)


class PlotsSettings(object):
    sel_modes = {
        "Zoom": 0,
        "Flag": 1,
        "Insert": 2
    }

    def __init__(self):
        self.plots = None
        self.canvas = None
        self.cid = None
        self.speed_axes = None
        self.temp_axes = None
        self.sal_axes = None
        self.sel_mode = self.sel_modes["Zoom"]
        self.has_zoom_applied = False
        self.display_flagged = True
        self.display_woa = True
        self.display_reference = True
        self.display_depth = True
        self.min_depth = None
        self.max_depth = None
        self.min_speed = None
        self.max_speed = None
        self.min_temp = None
        self.max_temp = None
        self.min_sal = None
        self.max_sal = None
