from __future__ import absolute_import, division, print_function, unicode_literals

import os
from PySide import QtGui
from PySide import QtCore

from hydroffice.base.gui.base import template
from hydroffice.base.gui.base.gui_settings import GuiSettings

from . import mainmenu
from . import controlpanel
from .. import __doc__
from .. import __version__
from .. import __name__
from .. import __author__
from .. import __license__
from ..helper import Helper, SspError
from ..project import Project


class MainWin(template.MainWin):
    """ Main window """

    here = os.path.abspath(os.path.dirname(__file__))

    ssp_state = {
        "OPEN": 0,
        "CLOSED": 1,
        "SERVER": 2
    }

    def __init__(self, hyo_win=None):
        super(MainWin, self).__init__(hyo_win, build_menu=False)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # retrieve and overwrite information
        self.name = __doc__
        self.version = __version__
        self.pkg_name = __name__
        self.author = __author__
        self.license = __license__

        # set the application name
        app = QtCore.QCoreApplication.instance()
        app.setApplicationName('%s v.%s' % (__doc__, __version__))

        self.m = mainmenu.SspMenu()
        self.init_ui()

        # retrieve application settings from previous run
        self._load_view_settings()

        # setup default project folder
        self.projects_folder = Helper.default_projects_folder()

        # create a project
        with_woa09 = True
        with_rtofs = False
        with_listeners = False
        self.prj = Project(with_listeners=with_listeners,
                           with_woa09=with_woa09,
                           with_rtofs=with_rtofs,
                           verbose=True,
                           verbose_config=False,
                           callback_debug_print=self.console.append)
        self.statusBar().showMessage("SSP project created", 3000)

        # check listeners
        if not self.prj.has_running_listeners() and with_listeners:
            msg = 'Kongsberg and/or Sippican and/or MVP network I/O cannot bind to ports.\n' \
                  'Is there another instance of SSP running already?'
            ret = QtGui.QMessageBox.warning(self, "Listeners Error", msg,
                                            QtGui.QMessageBox.Ignore | QtGui.QMessageBox.Close,
                                            QtGui.QMessageBox.Close)
            if ret == QtGui.QMessageBox.Close:
                self.close()

        # check woa09 atlas
        if not self.prj.woa09_atlas_loaded and with_woa09:
            msg = 'Failure on World Ocean Atlas grid file loading.'
            ret = QtGui.QMessageBox.warning(self, "WOA09 atlas", msg,
                                            QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)

        # check rtofs atlas
        if not self.prj.rtofs_atlas_loaded and with_rtofs:
            msg = 'Failure on RTOFS atlas loading (internet connectivity required)'
            ret = QtGui.QMessageBox.warning(self, "RTOFS atlas", msg,
                                            QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)

    def init_ui(self):
        """
        build user interface
        """
        self.setWindowTitle('%s v.%s' % (__doc__, __version__))

        # adding the control panel
        hbox = QtGui.QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(0)
        self.panel_frame.setLayout(hbox)
        self.panel = controlpanel.ControlPanel(parent_win=self)
        self.panel.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.panel)

        self.init_menu()

    def init_menu(self):
        """
        take care of menu and toolbars
        """
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
        self.m.file.menu = self.m.menu.addMenu('&File')
        self.m.file_import.menu = self.m.file.menu.addMenu('Import')
        self.m.file_query.menu = self.m.file.menu.addMenu('Query')
        self.m.file_export.menu = self.m.file.menu.addMenu('Export')
        self.m.view.menu = self.m.menu.addMenu('&View')
        self.m.process.menu = self.m.menu.addMenu('&Process')
        self.m.tools.menu = self.m.menu.addMenu('&Tools')
        self.m.help.menu = self.m.menu.addMenu('&Help')

        self.m.file.bar = self.addToolBar('File')
        self.m.file.bar.setObjectName('File')
        self.m.file.bar.setIconSize(GuiSettings.toolbar_icon_size())
        self.m.view.bar = self.addToolBar('View')
        self.m.view.bar.setObjectName('View')
        self.m.view.bar.setIconSize(GuiSettings.toolbar_icon_size())
        self.m.process.bar = self.addToolBar('Process')
        self.m.process.bar.setObjectName('Process')
        self.m.process.bar.setIconSize(GuiSettings.toolbar_icon_size())
        self.m.tools.bar = self.addToolBar('Tools')
        self.m.tools.bar.setObjectName('Tools')
        self.m.tools.bar.setIconSize(GuiSettings.toolbar_icon_size())
        self.m.help.bar = self.addToolBar('Help')
        self.m.help.bar.setObjectName('Help')
        self.m.help.bar.setIconSize(GuiSettings.toolbar_icon_size())

        self.make_actions()

    def make_actions(self):
        """
        Build some actions
        """

        self.m.file_import.castaway_action = QtGui.QAction('Castaway (.csv)', self)
        self.m.file_import.castaway_action.setStatusTip('Import Castaway cast')
        self.m.file_import.castaway_action.triggered.connect(self.import_castaway)
        self.m.file_import.menu.addAction(self.m.file_import.castaway_action)
        self.m.file_import_digibar.menu = self.m.file_import.menu.addMenu('Digibar')
        self.m.file_import_digibar.digibar_pro_action = QtGui.QAction('Pro (.txt)', self)
        self.m.file_import_digibar.digibar_pro_action.setStatusTip('Import Digibar Pro cast')
        self.m.file_import_digibar.digibar_pro_action.triggered.connect(self.import_digibar_pro)
        self.m.file_import_digibar.menu.addAction(self.m.file_import_digibar.digibar_pro_action)
        self.m.file_import_digibar.digibar_s_action = QtGui.QAction('S (.csv)', self)
        self.m.file_import_digibar.digibar_s_action.setStatusTip('Import Digibar S cast')
        self.m.file_import_digibar.digibar_s_action.triggered.connect(self.import_digibar_s)
        self.m.file_import_digibar.menu.addAction(self.m.file_import_digibar.digibar_s_action)
        self.m.file_import.idronaut_action = QtGui.QAction('Idronaut (.txt)', self)
        self.m.file_import.idronaut_action.setStatusTip('Import Idronaut cast')
        self.m.file_import.idronaut_action.triggered.connect(self.import_idronaut)
        self.m.file_import.menu.addAction(self.m.file_import.idronaut_action)
        self.m.file_import.saiv_action = QtGui.QAction('Saiv (.txt)', self)
        self.m.file_import.saiv_action.setStatusTip('Import Saiv cast')
        self.m.file_import.saiv_action.triggered.connect(self.import_saiv)
        self.m.file_import.menu.addAction(self.m.file_import.saiv_action)
        self.m.file_import.seabird_action = QtGui.QAction('Seabird (.cnv)', self)
        self.m.file_import.seabird_action.setStatusTip('Import Seabird cast')
        self.m.file_import.seabird_action.triggered.connect(self.import_seabird)
        self.m.file_import.menu.addAction(self.m.file_import.seabird_action)
        self.m.file_import.sippican_action = QtGui.QAction('Sippican (.edf)', self)
        self.m.file_import.sippican_action.setStatusTip('Import Sippican cast')
        self.m.file_import.sippican_action.triggered.connect(self.import_sippican)
        self.m.file_import.menu.addAction(self.m.file_import.sippican_action)
        self.m.file_import.turo_action = QtGui.QAction('Turo (.nc)', self)
        self.m.file_import.turo_action.setStatusTip('Import Turo cast')
        self.m.file_import.turo_action.triggered.connect(self.import_turo)
        self.m.file_import.menu.addAction(self.m.file_import.turo_action)
        self.m.file_import.unb_action = QtGui.QAction('UNB (.unb)', self)
        self.m.file_import.unb_action.setStatusTip('Import UNB cast')
        self.m.file_import.unb_action.triggered.connect(self.import_unb)
        self.m.file_import.menu.addAction(self.m.file_import.unb_action)
        self.m.file_import_valeport.menu = self.m.file_import.menu.addMenu('Valeport')
        self.m.file_import_valeport.valeport_midas_action = QtGui.QAction('Midas (.000)', self)
        self.m.file_import_valeport.valeport_midas_action.setStatusTip('Import Valeport Midas cast')
        self.m.file_import_valeport.valeport_midas_action.triggered.connect(self.import_valeport_midas)
        self.m.file_import_valeport.menu.addAction(self.m.file_import_valeport.valeport_midas_action)
        self.m.file_import_valeport.valeport_mini_svp_action = QtGui.QAction('MiniSVP (.txt)', self)
        self.m.file_import_valeport.valeport_mini_svp_action.setStatusTip('Import Valeport MiniSVP cast')
        self.m.file_import_valeport.valeport_mini_svp_action.triggered.connect(self.import_valeport_mini_svp)
        self.m.file_import_valeport.menu.addAction(self.m.file_import_valeport.valeport_mini_svp_action)
        self.m.file_import_valeport.valeport_monitor_action = QtGui.QAction('Monitor (.000)', self)
        self.m.file_import_valeport.valeport_monitor_action.setStatusTip('Import Valeport Monitor cast')
        self.m.file_import_valeport.valeport_monitor_action.triggered.connect(self.import_valeport_monitor)
        self.m.file_import_valeport.menu.addAction(self.m.file_import_valeport.valeport_monitor_action)

        self.m.file.sep_0 = self.m.file.menu.addSeparator()
        self.m.file.bar.addAction(self.m.file.sep_0)

        self.m.file.exit_action = QtGui.QAction(QtGui.QIcon(self.base_dir + '/media/quit.png'), '&Quit', self)
        self.m.file.exit_action.setShortcut('Ctrl+Q')
        self.m.file.exit_action.setStatusTip('Quit app')
        self.m.file.exit_action.triggered.connect(self.close)
        self.m.file.menu.addAction(self.m.file.exit_action)
        self.m.file.bar.addAction(self.m.file.exit_action)

    # ####### FILE ########

    # Import

    def import_castaway(self):
        self._open_data_file('CASTAWAY')

    def import_digibar_pro(self):
        self._open_data_file('DIGIBAR_PRO')

    def import_digibar_s(self):
        self._open_data_file('DIGIBAR_S')

    def import_idronaut(self):
        self._open_data_file('IDRONAUT')

    def import_saiv(self):
        self._open_data_file('SAIV')

    def import_seabird(self):
        self._open_data_file('SEABIRD')

    def import_sippican(self):
        self._open_data_file('SIPPICAN')

    def import_turo(self):
        self._open_data_file('TURO')

    def import_unb(self):
        self._open_data_file('UNB')

    def import_valeport_midas(self):
        self._open_data_file('VALEPORT_MIDAS')

    def import_valeport_mini_svp(self):
        self._open_data_file('VALEPORT_MINI_SVP')

    def import_valeport_monitor(self):
        self._open_data_file('VALEPORT_MONITOR')

    def _open_data_file(self, filetype):
        # clean up if a file is already loaded
        if self.prj.has_ssp_loaded:
            self.prj.clean_project()
            self.clear_app()

        # additional check.. it should be useless
        try:
            ext = self.prj.ssp_data.import_extensions[filetype]
        except KeyError:
            raise SspError("unsupported import file type: %s" % filetype)

        # ask the file path to the user
        selection_filter = "%s files (*.%s *.%s);;All files (*.*)" % (filetype, ext, ext.upper())
        filename, _ = QtGui.QFileDialog.getOpenFileName(self, "File selection", "",
                                                        selection_filter, None,
                                                        QtGui.QFileDialog.DontUseNativeDialog)
        if not filename:
            return
        self._print_info("filename: %s" % filename)

        date = None  # some formats have not information about date or position
        lat = None
        long = None
        if filetype == "DIGIBAR_PRO":
            date = self.get_date("Date required for database lookup.")
        elif filetype == "VALEPORT_MIDAS" or filetype == "VALEPORT_MONITOR" or filetype == "VALEPORT_MINI_SVP":
            lat, long = self.get_position("Geographic location required for pressure/depth conversion.")

        try:
            ssp = self.prj.open_file_format(filename, filetype, date, lat, long)
        except SspError as e:
            QtGui.QMessageBox.critical(self, "Data import error", e, QtGui.QMessageBox.Ok)
            return

        self._update_state(self.ssp_states['OPEN'])
        self.panel.pw.reset_view_limits()
        self.panel.pw.update_plot()
        self.statusBar().showMessage("Loaded %s" % self.prj.filename, 3000)

    def clear_app(self):
        pass

    def delete_project(self):
        """
        delete a project
        """
        if self.verbose:
            self.console.append("> delete project")

        reply = self.do_you_really_want("Delete", "clean the current project")
        if reply == QtGui.QMessageBox.Yes:
            self.panel.clean_project()

    def closeEvent(self, event):
        """
        called at quit time, save the settings
        """

        # release timers and listeners
        self.prj.release()

        # save application settings for next run
        self._save_view_settings()

        super(MainWin, self).closeEvent(event)

    def _make_about_string(self):
        """
        function overload to provide additional information
        """
        import platform
        import PySide

        text_string = "<p align='center'><b>%s</b> v. %s</p>" % (self.pkg_name, self.version)
        text_string += "<p>" \
                       "- os: %s [%sbit] <br>" \
                       "- python: %s [%sbit] <br>" \
                       "- pyside: %s <br>" \
                       "</p>" % \
                       (
                           os.name, "64" if Helper.is_64bit_os() else "32",
                           platform.python_version(), "64" if Helper.is_64bit_python() else "32",
                           PySide.__version__,
                       )
        return text_string

    def _print_info(self, info):
        if self.verbose:
            self.console.append("GUI > %" % info)

    def _print_error(self, info):
        if self.verbose:
            self.console.append("GUI > ERROR > %" % info)

    def _update_state(self, state):
        if not isinstance(state, self.ssp_state):
            self._print_error("invalid passed state: %s" % state)

        self._print_info("change state: %s" % state)


