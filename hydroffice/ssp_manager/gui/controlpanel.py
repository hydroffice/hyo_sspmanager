from __future__ import absolute_import, division, print_function, unicode_literals

import os
import datetime
from io import open

from PySide import QtGui
from PySide import QtCore

from hydroffice.base.gui.base import controlpanel

from ..helper import Helper
from ..plot import widget


class ControlPanel(controlpanel.ControlPanel):

    here = os.path.abspath(os.path.dirname(__file__))

    def __init__(self, parent_win):
        super(ControlPanel, self).__init__(parent_win)

        self.pw = None

        self.init_ui()

    # ################################ gui building ###################################

    def init_ui(self):
        """
        build user interface
        """

        self.vbox = QtGui.QVBoxLayout()
        self.setLayout(self.vbox)

        self.pw = widget.Widget(prj=self.parent_win.prj, verbose=True)
        self.vbox.addWidget(self.pw)

        self.initially_disabled()

    def initially_disabled(self):
        """
        Enable/disable initial commands
        """
        pass

    # ################################ action slots ###################################

    # ################################### cleaning ####################################

    def clean_project(self):
        """clean up the project"""
        if self.verbose:
            self.parent_win.console.append('> cleaning project')

        # nothing to do
        if not self.parent_win.prj:
            return

        # delete project object
        self.parent_win.prj = None
        # cleaning panel
        self.initially_disabled()