from __future__ import absolute_import, division, print_function, unicode_literals

import os

from PySide import QtGui
from PySide import QtCore

from ...base.gui.gui_settings import GuiSettings
from .. import helper
from ..helper import Helper


class SettingsTool(QtGui.QDialog):
    """
    Settings tool
    """

    here = os.path.abspath(os.path.dirname(__file__))  # to be overloaded

    def __init__(self, prj, verbose=False):
        QtGui.QDialog.__init__(self)

        vbox = QtGui.QHBoxLayout()
        self.setLayout(vbox)

        self.tabs = QtGui.QTabWidget()
        vbox.addWidget(self.tabs)

        self.prj = prj
        self.verbose = verbose

        self.tabs.setMinimumWidth(600)
        self.setWindowTitle('Settings')

        icon_info = QtCore.QFileInfo(self.here + '/media/favicon.png')
        print(icon_info.absoluteFilePath())
        self.setWindowIcon(QtGui.QIcon(icon_info.absoluteFilePath()))

        if Helper.is_windows():  # to display the app icon on the taskbar on Win7
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Settings')

        # tabs
        self.export_tab = None
        self.export_layout = None
        self.server_tab = None
        self.server_layout = None

        self.make_ui()

    def make_ui(self):
        """
        Create all the tabs
        """
        self.make_export_tab()
        self.make_server_tab()

    def make_server_tab(self):
        """Make the Server tab"""
        self.prj.server_tab = QtGui.QFrame(self)
        self.tabs.addTab(self.prj.server_tab, "Server")
        self.server_layout = QtGui.QVBoxLayout(self.server_tab)

        hbox_1 = QtGui.QHBoxLayout()
        self.server_layout.addLayout(hbox_1)
        text_1 = QtGui.QLabel("Append Caris file:")
        hbox_1.addWidget(text_1)
        text_1.setFixedHeight(GuiSettings.single_line_height())
        edit_1 = QtGui.QTextEdit("")
        hbox_1.addWidget(edit_1)
        edit_1.setFixedHeight(GuiSettings.single_line_height())
        edit_1.setReadOnly(True)
        edit_1.setFont(GuiSettings.small_font())
        edit_1.setTextColor(GuiSettings.console_fg_color())
        edit_1.setText("%s" % self.prj.s.server_append_caris_file)

        hbox_2 = QtGui.QHBoxLayout()
        self.server_layout.addLayout(hbox_2)
        text_2 = QtGui.QLabel("Caris filename:")
        hbox_2.addWidget(text_2)
        text_2.setFixedHeight(GuiSettings.single_line_height())
        edit_2 = QtGui.QTextEdit("")
        hbox_2.addWidget(edit_2)
        edit_2.setFixedHeight(GuiSettings.single_line_height())
        edit_2.setReadOnly(True)
        edit_2.setFont(GuiSettings.small_font())
        edit_2.setTextColor(GuiSettings.console_fg_color())
        edit_2.setText("%s" % self.prj.s.server_caris_filename)

        hbox_3 = QtGui.QHBoxLayout()
        self.server_layout.addLayout(hbox_3)
        text_3 = QtGui.QLabel("Export directory:")
        hbox_3.addWidget(text_3)
        text_3.setFixedHeight(GuiSettings.single_line_height())
        edit_3 = QtGui.QTextEdit("")
        hbox_3.addWidget(edit_3)
        edit_3.setFixedHeight(GuiSettings.single_line_height())
        edit_3.setReadOnly(True)
        edit_3.setFont(GuiSettings.small_font())
        edit_3.setTextColor(GuiSettings.console_fg_color())
        edit_3.setText("%s" % self.prj.s.server_export_directory)

    def make_export_tab(self):
        """Make the Export tab"""
        self.export_tab = QtGui.QFrame(self)
        self.tabs.addTab(self.export_tab, "Export")
        self.export_layout = QtGui.QVBoxLayout(self.export_tab)

        hbox_1 = QtGui.QHBoxLayout()
        self.export_layout.addLayout(hbox_1)
        text_1 = QtGui.QLabel("Append Caris file:")
        hbox_1.addWidget(text_1)
        text_1.setFixedHeight(GuiSettings.single_line_height())
        edit_1 = QtGui.QTextEdit("")
        hbox_1.addWidget(edit_1)
        edit_1.setFixedHeight(GuiSettings.single_line_height())
        edit_1.setReadOnly(True)
        edit_1.setFont(GuiSettings.small_font())
        edit_1.setTextColor(GuiSettings.console_fg_color())
        edit_1.setText("%s" % self.prj.s.user_append_caris_file)

        hbox_2 = QtGui.QHBoxLayout()
        self.export_layout.addLayout(hbox_2)
        text_2 = QtGui.QLabel("Export prompt for filename:")
        hbox_2.addWidget(text_2)
        text_2.setFixedHeight(GuiSettings.single_line_height())
        edit_2 = QtGui.QTextEdit("")
        hbox_2.addWidget(edit_2)
        edit_2.setFixedHeight(GuiSettings.single_line_height())
        edit_2.setReadOnly(True)
        edit_2.setFont(GuiSettings.small_font())
        edit_2.setTextColor(GuiSettings.console_fg_color())
        edit_2.setText("%s" % self.prj.s.user_export_prompt_filename)

        hbox_3 = QtGui.QHBoxLayout()
        self.export_layout.addLayout(hbox_3)
        text_3 = QtGui.QLabel("Export directory:")
        hbox_3.addWidget(text_3)
        text_3.setFixedHeight(GuiSettings.single_line_height())
        edit_3 = QtGui.QTextEdit("")
        hbox_3.addWidget(edit_3)
        edit_3.setFixedHeight(GuiSettings.single_line_height())
        edit_3.setReadOnly(True)
        edit_3.setFont(GuiSettings.small_font())
        edit_3.setTextColor(GuiSettings.console_fg_color())
        edit_3.setText("%s" % self.prj.s.user_export_directory)

        hbox_4 = QtGui.QHBoxLayout()
        self.export_layout.addLayout(hbox_4)
        text_4 = QtGui.QLabel("Filename prefix:")
        hbox_4.addWidget(text_4)
        text_4.setFixedHeight(GuiSettings.single_line_height())
        edit_4 = QtGui.QTextEdit("")
        hbox_4.addWidget(edit_4)
        edit_4.setFixedHeight(GuiSettings.single_line_height())
        edit_4.setReadOnly(True)
        edit_4.setFont(GuiSettings.small_font())
        edit_4.setTextColor(GuiSettings.console_fg_color())
        edit_4.setText("%s" % self.prj.s.user_filename_prefix)
