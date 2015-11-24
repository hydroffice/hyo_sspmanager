from __future__ import absolute_import, division, print_function, unicode_literals

import os

from matplotlib.backends.qt_compat import QtGui, QtCore
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvas
from matplotlib import rcParams

from hydroffice.base import gui  # for the base folder
from hydroffice.base.gui.base.gui_settings import GuiSettings


class WdgMenu(object):
    """
    Cluster the menu and sub-menus
    """

    class InteractionMenu(object):
        def __init__(self):
            self.menu = None
            self.bar = None
            self.zoom_action = None
            self.sep_0 = None
            self.flag_action = None
            self.unflag_action = None
            self.insert_action = None

    def __init__(self):
        self.menu = None
        self.interaction = WdgMenu.InteractionMenu()


class Widget(QtGui.QMainWindow):

    base_dir = os.path.abspath(os.path.dirname(gui.__file__))
    here = os.path.abspath(os.path.dirname(__file__))  # to be overloaded

    selection_modes = {"Zoom": 0, "Flag": 1, "Insert": 2}

    def __init__(self, prj, verbose=False):
        self.verbose = verbose
        super(Widget, self).__init__()
        self.prj = prj

        rcParams.update(
            {
                'font.family': 'sans-serif',
                'font.size': 9
            }
        )

        # menus and toolbars
        self.m = WdgMenu()

        self.figure = Figure(facecolor='None', edgecolor='None')
        canvas = FigureCanvas(self.figure)

        self.speed_axes = None
        self.temperature_axes = None
        self.salinity_axes = None
        self.selection_mode = self.selection_modes["Zoom"]

        self.setCentralWidget(canvas)

        self._menu()

        self.update_plot()

    def update_plot(self):
        self.print_info("update plots")

        bg_color = 'g'

        self.figure.clf()
        self.speed_axes = self.figure.add_subplot(131, axisbg=bg_color)
        self.speed_axes.invert_yaxis()
        self.temperature_axes = self.figure.add_subplot(132, sharey=self.speed_axes, axisbg=bg_color)
        self.temperature_axes.invert_yaxis()
        self.salinity_axes = self.figure.add_subplot(133, sharey=self.speed_axes, axisbg=bg_color)
        self.salinity_axes.invert_yaxis()

    def reset_limits(self):
        self._print_info("reset limits")

    def _menu(self):
        """
        build actions and menu bar
        """
        self.print_info("make menu")

        # make it flat
        self.setStyleSheet(""
                           "QToolBar QToolButton {"
                           "padding : 1px;"
                           "border : 1px;"
                           "margin : 1px;"
                           "}"
                           "QToolBar QToolButton:hover {"
                           "background-color : rgba(200, 200, 200, 200);"
                           "border-radius : 5px;"
                           "}"
                           "QToolBar QToolButton:pressed {"
                           "border : 1px;"
                           "}")

        self.m.menu = self.menuBar()
        self.m.interaction.menu = self.m.menu.addMenu('&Interaction')

        self.m.interaction.bar = self.addToolBar('Interaction')
        self.m.interaction.bar.setObjectName('Interaction')
        self.m.interaction.bar.setIconSize(GuiSettings.toolbar_icon_size())

        self._actions()

    def _actions(self):
        """
        Build some actions
        """

        # Interaction menu
        ag = QtGui.QActionGroup(self, exclusive=True)

        self.m.interaction.zoom_action = ag.addAction(QtGui.QAction('&Zoom', self, checkable=True))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(os.path.join(self.here, 'media', 'zoom.png')), state=QtGui.QIcon.On)
        icon.addPixmap(QtGui.QPixmap(os.path.join(self.here, 'media', 'zoom_disabled.png')), state=QtGui.QIcon.Off)
        self.m.interaction.zoom_action.setIcon(icon)
        self.m.interaction.zoom_action.setIconVisibleInMenu(False)
        self.m.interaction.zoom_action.setShortcut('Ctrl+Z')
        self.m.interaction.zoom_action.setStatusTip('Zoom area')
        self.m.interaction.zoom_action.triggered.connect(self._activate_zoom)
        self.m.interaction.menu.addAction(self.m.interaction.zoom_action)
        self.m.interaction.bar.addAction(self.m.interaction.zoom_action)
        # set the checked actions
        self.m.interaction.zoom_action.setChecked(True)

        self.m.interaction.flag_action = ag.addAction(QtGui.QAction('&Flag', self, checkable=True))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(os.path.join(self.here, 'media', 'flag.png')), state=QtGui.QIcon.On)
        icon.addPixmap(QtGui.QPixmap(os.path.join(self.here, 'media', 'flag_disabled.png')), state=QtGui.QIcon.Off)
        self.m.interaction.flag_action.setIcon(icon)
        self.m.interaction.flag_action.setIconVisibleInMenu(False)
        self.m.interaction.flag_action.setShortcut('Ctrl+F')
        self.m.interaction.flag_action.setStatusTip('Flag samples')
        self.m.interaction.flag_action.triggered.connect(self._activate_flag)
        self.m.interaction.menu.addAction(self.m.interaction.flag_action)
        self.m.interaction.bar.addAction(self.m.interaction.flag_action)

        self.m.interaction.unflag_action = ag.addAction(QtGui.QAction('&Unflag', self, checkable=True))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(os.path.join(self.here, 'media', 'unflag.png')), state=QtGui.QIcon.On)
        icon.addPixmap(QtGui.QPixmap(os.path.join(self.here, 'media', 'unflag_disabled.png')), state=QtGui.QIcon.Off)
        self.m.interaction.unflag_action.setIcon(icon)
        self.m.interaction.unflag_action.setIconVisibleInMenu(False)
        self.m.interaction.unflag_action.setShortcut('Ctrl+U')
        self.m.interaction.unflag_action.setStatusTip('Unflag samples')
        self.m.interaction.unflag_action.triggered.connect(self._activate_unflag)
        self.m.interaction.menu.addAction(self.m.interaction.unflag_action)
        self.m.interaction.bar.addAction(self.m.interaction.unflag_action)

        self.m.interaction.insert_action = ag.addAction(QtGui.QAction('&Insert', self, checkable=True))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(os.path.join(self.here, 'media', 'insert.png')), state=QtGui.QIcon.On)
        icon.addPixmap(QtGui.QPixmap(os.path.join(self.here, 'media', 'insert_disabled.png')), state=QtGui.QIcon.Off)
        self.m.interaction.insert_action.setIcon(icon)
        self.m.interaction.insert_action.setIconVisibleInMenu(False)
        self.m.interaction.insert_action.setShortcut('Ctrl+I')
        self.m.interaction.insert_action.setStatusTip('Insert samples')
        self.m.interaction.insert_action.triggered.connect(self._activate_insert)
        self.m.interaction.menu.addAction(self.m.interaction.insert_action)
        self.m.interaction.bar.addAction(self.m.interaction.insert_action)

    def _activate_zoom(self):
        self.print_info("activate zoom")

        self.selection_mode = self.selection_modes["Zoom"]
        self.prj.s.flag = 0
        self.prj.s.clear_user_samples()
        self.update_plot()

    def _activate_flag(self):
        self.print_info("activate flag")

        self.selection_mode = self.selection_modes["Flag"]
        self.prj.s.flag = 1  # '1' -> flag data
        self.prj.s.clear_user_samples()
        self.update_plot()

    def _activate_unflag(self):
        self.print_info("activate unflag")

        self.selection_mode = self.selection_modes["Flag"]
        self.prj.s.flag = 3  # '3' -> unflag data
        self.prj.s.clear_user_samples()
        self.update_plot()

    def _activate_insert(self):
        self.print_info("activate insert")

        self.selection_mode = self.selection_modes["Insert"]
        self.prj.s.flag = 0
        self.prj.s.clear_user_samples()
        self.update_plot()

    def print_info(self, info):
        if self.verbose:
            print("PLT > %s" % info)

    def print_error(self, info):
        if self.verbose:
            print("PLT > ERROR > %s" % info)