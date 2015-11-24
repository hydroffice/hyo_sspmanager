from __future__ import absolute_import, division, print_function, unicode_literals


class SspMenu(object):
    """
    Cluster the menu and sub-menus
    """

    class FileMenu(object):
        def __init__(self):
            self.menu = None
            self.bar = None
            self.sep_0 = None
            self.exit_action = None

    class FileMenuImport(object):
        def __init__(self):
            self.menu = None
            self.bar = None
            self.castaway_action = None
            self.idronaut_action = None
            self.saiv_action = None
            self.seabird_action = None
            self.sippican_action = None
            self.turo_action = None
            self.unb_action = None

    class FileMenuImportDigibar(object):
        def __init__(self):
            self.menu = None
            self.bar = None
            self.digibar_pro_action = None
            self.digibar_s_action = None

    class FileMenuImportValeport(object):
        def __init__(self):
            self.menu = None
            self.bar = None
            self.valeport_midas_action = None
            self.valeport_monitor_action = None
            self.valeport_mini_svp_action = None

    class FileMenuQuery(object):
        def __init__(self):
            self.menu = None
            self.bar = None

    class FileMenuExport(object):
        def __init__(self):
            self.menu = None
            self.bar = None

    class ViewMenu(object):
        def __init__(self):
            self.menu = None
            self.bar = None

    class ProcessMenu(object):
        def __init__(self):
            self.menu = None
            self.bar = None
            self.query_action = None
            self.sep_0 = None

    class ToolsMenu(object):
        def __init__(self):
            self.menu = None
            self.bar = None
            self.server_start_action = None
            self.server_stop_action = None
            self.server_force_action = None
            self.sep_0 = None
            self.settings_action = None

    class HelpMenu(object):
        def __init__(self):
            self.menu = None
            self.bar = None
            self.manual_action = None
            self.help_action = None
            self.sep_0 = None
            self.qt_about_action = None
            self.about_action = None

    def __init__(self):
        self.menu = None
        self.file = SspMenu.FileMenu()
        self.file_import = SspMenu.FileMenuImport()
        self.file_import_digibar = SspMenu.FileMenuImportDigibar()
        self.file_import_valeport = SspMenu.FileMenuImportValeport()
        self.file_query = SspMenu.FileMenuQuery()
        self.file_export = SspMenu.FileMenuExport()
        self.view = SspMenu.ViewMenu()
        self.process = SspMenu.ProcessMenu()
        self.tools = SspMenu.ToolsMenu()
        self.help = SspMenu.HelpMenu()