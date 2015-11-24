from __future__ import absolute_import, division, print_function, unicode_literals

import wx

import logging

log = logging.getLogger(__name__)

MENU_FILE = wx.NewId()
MENU_VIEW = wx.NewId()
MENU_INTERACT = wx.NewId()
MENU_PROC = wx.NewId()
MENU_DB = wx.NewId()
MENU_SERVER = wx.NewId()
MENU_TOOLS = wx.NewId()
MENU_HELP = wx.NewId()

MENU_FILE_IMP = wx.NewId()
MENU_FILE_IMP_DIGI_S = wx.NewId()
MENU_FILE_IMP_UNB = wx.NewId()
MENU_FILE_IMP_SIPPICAN = wx.NewId()
MENU_FILE_IMP_SEABIRD = wx.NewId()
MENU_FILE_IMP_VALEPORT = wx.NewId()
MENU_FILE_IMP_VALE_MIDAS = wx.NewId()
MENU_FILE_IMP_VALE_MON = wx.NewId()
MENU_FILE_IMP_VALE_MINIS = wx.NewId()
MENU_FILE_IMP_TURO = wx.NewId()
MENU_FILE_IMP_DIGIBAR = wx.NewId()
MENU_FILE_IMP_DIGI_PRO = wx.NewId()
MENU_FILE_IMP_CASTAWAY = wx.NewId()
MENU_FILE_IMP_IDRONAUT = wx.NewId()
MENU_FILE_IMP_SAIV = wx.NewId()
MENU_FILE_QUERY = wx.NewId()
MENU_FILE_QUERY_WOA = wx.NewId()
MENU_FILE_QUERY_RTOFS = wx.NewId()
MENU_FILE_QUERY_SIS = wx.NewId()
MENU_FILE_EXPORT = wx.NewId()
MENU_FILE_EXPORT_ASVP = wx.NewId()
MENU_FILE_EXPORT_VEL = wx.NewId()
MENU_FILE_EXPORT_HIPS = wx.NewId()
MENU_FILE_EXPORT_PRO = wx.NewId()
MENU_FILE_EXPORT_IXBLUE = wx.NewId()
MENU_FILE_EXPORT_UNB = wx.NewId()
MENU_FILE_EXPORT_ELAC = wx.NewId()
MENU_FILE_EXPORT_CSV = wx.NewId()
MENU_FILE_EXPORT_CAST = wx.NewId()
MENU_FILE_CLEAR = wx.NewId()
MENU_FILE_EXIT = wx.NewId()

MENU_PROC_INS_ZOOM = wx.NewId()
MENU_PROC_INS_FLAG = wx.NewId()
MENU_PROC_INS_UNFLAG = wx.NewId()
MENU_PROC_INS_INSERT = wx.NewId()

MENU_VIEW_RESET = wx.NewId()
MENU_VIEW_HIDE_WOA = wx.NewId()
MENU_VIEW_HIDE_FLAGGED = wx.NewId()
MENU_VIEW_HIDE_DEPTH = wx.NewId()

MENU_PROC_LOAD_SAL = wx.NewId()
MENU_PROC_LOAD_TEMP_SAL = wx.NewId()
MENU_PROC_LOAD_SURFSP = wx.NewId()
MENU_PROC_EXTEND_CAST = wx.NewId()
MENU_PROC_INSPECTION = wx.NewId()
MENU_PROC_PREVIEW_THINNING = wx.NewId()
MENU_PROC_SEND_PROFILE = wx.NewId()
MENU_PROC_STORE_SSP = wx.NewId()
MENU_PROC_REDO_SSP = wx.NewId()
MENU_PROC_LOG_METADATA = wx.NewId()
# MENU_PROC_EXPRESS = wx.NewId()

MENU_DB_QUERY = wx.NewId()
MENU_DB_QUERY_INTERNAL_DB = wx.NewId()
MENU_DB_QUERY_EXTERNAL_DB = wx.NewId()
MENU_DB_DELETE = wx.NewId()
MENU_DB_DELETE_INTERNAL_DB = wx.NewId()
MENU_DB_DELETE_EXTERNAL_DB = wx.NewId()
MENU_DB_EXPORT = wx.NewId()
MENU_DB_EXPORT_SHP = wx.NewId()
MENU_DB_EXPORT_KML = wx.NewId()
MENU_DB_EXPORT_CSV = wx.NewId()
MENU_DB_PLOT = wx.NewId()
MENU_DB_PLOT_MAP_SSP = wx.NewId()
MENU_DB_PLOT_DAILY_SSP = wx.NewId()
MENU_DB_SAVE_DAILY_SSP = wx.NewId()

MENU_TOOLS_SERVER = wx.NewId()
MENU_TOOLS_SET_REFERENCE_CAST = wx.NewId()
MENU_TOOLS_CLEAR_REFERENCE_CAST = wx.NewId()
MENU_TOOLS_EDIT_REFERENCE_CAST = wx.NewId()
MENU_TOOLS_REFERENCE = wx.NewId()
MENU_TOOLS_SETTINGS = wx.NewId()
MENU_TOOLS_REF_MON = wx.NewId()
MENU_TOOLS_GEO_MONITOR = wx.NewId()

MENU_SERVER_START = wx.NewId()
MENU_SERVER_SEND = wx.NewId()
MENU_SERVER_STOP = wx.NewId()
MENU_SERVER_LOG_METADATA = wx.NewId()
MENU_HELP_MANUAL = wx.NewId()
MENU_HELP_ABOUT = wx.NewId()

MENUS_ALL = (MENU_FILE_IMP, MENU_FILE_IMP_CASTAWAY, MENU_FILE_IMP_DIGIBAR, MENU_FILE_IMP_DIGI_PRO, MENU_FILE_IMP_DIGI_S,
             MENU_FILE_IMP_IDRONAUT, MENU_FILE_IMP_SAIV, MENU_FILE_IMP_SEABIRD, MENU_FILE_IMP_SIPPICAN,
             MENU_FILE_IMP_TURO, MENU_FILE_IMP_UNB, MENU_FILE_IMP_VALEPORT,
             MENU_FILE_IMP_VALE_MIDAS, MENU_FILE_IMP_VALE_MON, MENU_FILE_IMP_VALE_MINIS,
             MENU_FILE_QUERY,
             MENU_FILE_EXPORT, MENU_FILE_EXPORT_CAST,
             MENU_FILE_EXPORT_ASVP, MENU_FILE_EXPORT_PRO, MENU_FILE_EXPORT_HIPS, MENU_FILE_EXPORT_IXBLUE,
             MENU_FILE_EXPORT_VEL, MENU_FILE_EXPORT_UNB, MENU_FILE_EXPORT_ELAC, MENU_FILE_EXPORT_CSV,
             MENU_FILE_CLEAR,
             MENU_VIEW_RESET, MENU_VIEW_HIDE_WOA, MENU_VIEW_HIDE_FLAGGED, MENU_VIEW_HIDE_DEPTH,
             MENU_PROC_LOAD_SAL, MENU_PROC_LOAD_TEMP_SAL, MENU_PROC_LOAD_SURFSP, MENU_PROC_EXTEND_CAST,
             MENU_PROC_INSPECTION, MENU_PROC_INS_ZOOM, MENU_PROC_INS_FLAG, MENU_PROC_INS_UNFLAG, MENU_PROC_INS_INSERT,
             # MENU_PROC_EXPRESS,
             MENU_PROC_PREVIEW_THINNING, MENU_PROC_SEND_PROFILE,
             MENU_PROC_STORE_SSP, MENU_PROC_REDO_SSP, MENU_PROC_LOG_METADATA,
             MENU_DB_QUERY,
             MENU_DB_DELETE,
             MENU_DB_EXPORT,
             MENU_DB_PLOT,
             MENU_SERVER_START, MENU_SERVER_SEND, MENU_SERVER_STOP, MENU_SERVER_LOG_METADATA,
             MENU_TOOLS_GEO_MONITOR, MENU_TOOLS_REF_MON,
             MENU_TOOLS_SET_REFERENCE_CAST, MENU_TOOLS_EDIT_REFERENCE_CAST, MENU_TOOLS_CLEAR_REFERENCE_CAST,
             MENU_TOOLS_SETTINGS)

MENUS_DISABLED_ON_CLOSED = (
    MENU_FILE_EXPORT_CAST, MENU_FILE_CLEAR,
    MENU_VIEW_RESET, MENU_VIEW_HIDE_WOA, MENU_VIEW_HIDE_FLAGGED, MENU_VIEW_HIDE_DEPTH,
    MENU_PROC_LOAD_SAL, MENU_PROC_LOAD_TEMP_SAL, MENU_PROC_LOAD_SURFSP,
    MENU_PROC_EXTEND_CAST, MENU_PROC_INSPECTION,
    MENU_PROC_INS_ZOOM, MENU_PROC_INS_FLAG, MENU_PROC_INS_INSERT, MENU_PROC_INS_UNFLAG,
    MENU_PROC_PREVIEW_THINNING, MENU_PROC_SEND_PROFILE,
    MENU_PROC_STORE_SSP, MENU_PROC_REDO_SSP,
    # MENU_PROC_EXPRESS,
    MENU_TOOLS_SET_REFERENCE_CAST,
    MENU_SERVER_SEND, MENU_SERVER_STOP)

MENUS_DISABLED_ON_OPEN = (MENU_SERVER_SEND, MENU_SERVER_STOP)

MENUS_DISABLED_ON_SERVER = (
    MENU_FILE_IMP,  # all import
    MENU_FILE_QUERY,  # all query
    MENU_FILE_EXPORT,  # all export
    MENU_FILE_CLEAR,
    MENU_PROC_LOG_METADATA, MENU_TOOLS_SET_REFERENCE_CAST, MENU_TOOLS_EDIT_REFERENCE_CAST,
    MENU_TOOLS_CLEAR_REFERENCE_CAST, MENU_FILE_IMP_DIGI_S, MENU_FILE_IMP_SEABIRD,
    # MENU_PROC_EXPRESS,
    MENU_PROC_LOAD_SAL, MENU_PROC_LOAD_TEMP_SAL, MENU_PROC_LOAD_SURFSP, MENU_PROC_EXTEND_CAST,
    MENU_PROC_INSPECTION, MENU_PROC_PREVIEW_THINNING, MENU_PROC_SEND_PROFILE, MENU_PROC_REDO_SSP,
    MENU_DB_QUERY,
    MENU_DB_DELETE,
    MENU_DB_EXPORT,
    MENU_DB_PLOT,
    MENU_SERVER_START)


class SVPEditorBase(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        # Menu Bar
        self.SVPEditorFrame_menubar = wx.MenuBar()

        # ### FILE ###
        self.FileMenu = wx.Menu()

        # File/Import
        FileImp = wx.Menu()
        self.FileImpCastaway = wx.MenuItem(FileImp, MENU_FILE_IMP_CASTAWAY, "Castaway (.csv)",
                                           "Import a Castaway cast", wx.ITEM_NORMAL)
        FileImp.AppendItem(self.FileImpCastaway)
        FileImpDigi = wx.Menu()
        self.FileImpDigibarPro = wx.MenuItem(FileImpDigi, MENU_FILE_IMP_DIGI_PRO, "Digibar Pro (.txt)",
                                             "Import a Digibar Pro cast", wx.ITEM_NORMAL)
        FileImpDigi.AppendItem(self.FileImpDigibarPro)
        self.FileImpDigibarS = wx.MenuItem(FileImpDigi, MENU_FILE_IMP_DIGI_S, "Digibar S (.csv)",
                                           "Import a Digibar S cast", wx.ITEM_NORMAL)
        FileImpDigi.AppendItem(self.FileImpDigibarS)
        FileImp.AppendMenu(MENU_FILE_IMP_DIGIBAR, "Digibar", FileImpDigi, "Import Digibar formats")
        self.FileImpIdronaut = wx.MenuItem(FileImp, MENU_FILE_IMP_IDRONAUT, "Idronaut (*.txt)",
                                           "Import an Idronaut cast", wx.ITEM_NORMAL)
        FileImp.AppendItem(self.FileImpIdronaut)
        self.FileImpSaiv = wx.MenuItem(FileImp, MENU_FILE_IMP_SAIV, "Saiv (*.txt)",
                                       "Import a Saiv cast", wx.ITEM_NORMAL)
        FileImp.AppendItem(self.FileImpSaiv)
        self.FileImpSeabird = wx.MenuItem(FileImp, MENU_FILE_IMP_SEABIRD, "Seabird (.cnv)",
                                          "Import a Seabird cast", wx.ITEM_NORMAL)
        FileImp.AppendItem(self.FileImpSeabird)
        self.FileImpSippican = wx.MenuItem(FileImp, MENU_FILE_IMP_SIPPICAN, "Sippican (.edf)",
                                           "Import a Sippican cast", wx.ITEM_NORMAL)
        FileImp.AppendItem(self.FileImpSippican)
        self.FileImpTuro = wx.MenuItem(FileImp, MENU_FILE_IMP_TURO, "Turo (.nc)",
                                       "Import a Turo cast", wx.ITEM_NORMAL)
        FileImp.AppendItem(self.FileImpTuro)
        self.FileImpUNB = wx.MenuItem(FileImp, MENU_FILE_IMP_UNB, "UNB (.unb)",
                                      "Import a UNB cast", wx.ITEM_NORMAL)
        FileImp.AppendItem(self.FileImpUNB)
        FileImpVale = wx.Menu()
        self.FileImpValeMidas = wx.MenuItem(FileImpVale, MENU_FILE_IMP_VALE_MIDAS, "Midas (.000)",
                                            "Import a Valeport Midas cast", wx.ITEM_NORMAL)
        FileImpVale.AppendItem(self.FileImpValeMidas)
        self.FileImpValeMonitor = wx.MenuItem(FileImpVale, MENU_FILE_IMP_VALE_MON, "Monitor (.000)",
                                              "Import a Valeport Monitor cast", wx.ITEM_NORMAL)
        FileImpVale.AppendItem(self.FileImpValeMonitor)
        self.FileImpValeMiniS = wx.MenuItem(FileImpVale, MENU_FILE_IMP_VALE_MINIS, "MiniSVP (.txt)",
                                            "Import a Valeport MiniSVP cast", wx.ITEM_NORMAL)
        FileImpVale.AppendItem(self.FileImpValeMiniS)
        FileImp.AppendMenu(MENU_FILE_IMP_VALEPORT, "Valeport", FileImpVale, "Import Valeport formats")
        self.FileMenu.AppendMenu(MENU_FILE_IMP, "Import cast", FileImp, "Import an SSP cast")

        # File/Query
        FileQuery = wx.Menu()
        self.FileQuerySis = wx.MenuItem(FileQuery, MENU_FILE_QUERY_SIS, "Kongsberg SIS",
                                        "Retrieve the SSP cast in use by SIS", wx.ITEM_NORMAL)
        FileQuery.AppendItem(self.FileQuerySis)
        self.FileQueryRtofs = wx.MenuItem(FileQuery, MENU_FILE_QUERY_RTOFS, "RTOFS atlas",
                                          "Retrieve a predicted RTOFS-based SSP", wx.ITEM_NORMAL)
        FileQuery.AppendItem(self.FileQueryRtofs)
        self.FileQueryWoa = wx.MenuItem(FileQuery, MENU_FILE_QUERY_WOA, "WOA09 atlas",
                                        "Retrieve statistical info about the SSP in the area", wx.ITEM_NORMAL)
        FileQuery.AppendItem(self.FileQueryWoa)
        self.FileMenu.AppendMenu(MENU_FILE_QUERY, "Query from", FileQuery,
                                 "Retrieve SSP info from external sources")

        # File / Export
        FileExp = wx.Menu()
        self.FileExpCast = wx.MenuItem(FileExp, MENU_FILE_EXPORT_CAST, "Export selected formats",
                                       "Export the current SSP in the selected formats", wx.ITEM_NORMAL)
        FileExp.AppendItem(self.FileExpCast)
        FileExp.AppendSeparator()
        self.FileExpHips = wx.MenuItem(FileExp, MENU_FILE_EXPORT_HIPS, "Caris HIPS (.svp)",
                                       "Export the current SSP as Caris HIPS format", wx.ITEM_CHECK)
        FileExp.AppendItem(self.FileExpHips)
        self.FileExpCsv = wx.MenuItem(FileExp, MENU_FILE_EXPORT_CSV, "Comma-separated (.csv)",
                                      "Export the current SSP as comma-separated format", wx.ITEM_CHECK)
        FileExp.AppendItem(self.FileExpCsv)
        self.FileExpElac = wx.MenuItem(FileExp, MENU_FILE_EXPORT_ELAC, "Elac (.sva)",
                                       "Export the current SSP as Elac format", wx.ITEM_CHECK)
        FileExp.AppendItem(self.FileExpElac)
        self.FileExpVel = wx.MenuItem(FileExp, MENU_FILE_EXPORT_VEL, "Hypack (.vel)",
                                      "Export the current SSP as Hypack format", wx.ITEM_CHECK)
        FileExp.AppendItem(self.FileExpVel)
        self.FileExpIxblue = wx.MenuItem(FileExp, MENU_FILE_EXPORT_IXBLUE, "IXBLUE (.txt)",
                                         "Export the current SSP as IXBLUE format", wx.ITEM_CHECK)
        FileExp.AppendItem(self.FileExpIxblue)
        self.FileExpAsvp = wx.MenuItem(FileExp, MENU_FILE_EXPORT_ASVP, "Kongsberg (.asvp)",
                                       "Export the current SSP as Kongsberg format", wx.ITEM_CHECK)
        FileExp.AppendItem(self.FileExpAsvp)
        self.FileExpPro = wx.MenuItem(FileExp, MENU_FILE_EXPORT_PRO, "Sonardyne (.pro)",
                                      "Export the current SSP as Sonardyne format", wx.ITEM_CHECK)
        FileExp.AppendItem(self.FileExpPro)
        self.FileExpUnb = wx.MenuItem(FileExp, MENU_FILE_EXPORT_UNB, "UNB (.unb)",
                                      "Export the current SSP as UNB format", wx.ITEM_CHECK)
        FileExp.AppendItem(self.FileExpUnb)
        self.FileMenu.AppendMenu(MENU_FILE_EXPORT, "Export SSP", FileExp,
                                 "Export the current SSP")

        self.FileClear = wx.MenuItem(self.FileMenu, MENU_FILE_CLEAR, "Clear",
                                     "Clear the loaded cast", wx.ITEM_NORMAL)
        self.FileMenu.AppendItem(self.FileClear)
        self.FileMenu.AppendSeparator()

        self.FileExit = wx.MenuItem(self.FileMenu, MENU_FILE_EXIT, "Exit",
                                    "Quit SSP Manager", wx.ITEM_NORMAL)
        self.FileMenu.AppendItem(self.FileExit)
        self.SVPEditorFrame_menubar.Append(self.FileMenu, "File")

        # ### VIEW ###
        self.ViewMenu = wx.Menu()
        self.ResetView = wx.MenuItem(self.ViewMenu, MENU_VIEW_RESET, "Reset plot view",
                                     "Reset the plot view", wx.ITEM_NORMAL)
        self.ViewMenu.AppendItem(self.ResetView)
        self.ViewMenu.AppendSeparator()
        self.ViewHideWOA = wx.MenuItem(self.ViewMenu, MENU_VIEW_HIDE_WOA, "Hide WOA info",
                                       "Hide the visualization of WOA info", wx.ITEM_CHECK)
        self.ViewMenu.AppendItem(self.ViewHideWOA)
        self.HideFlagged = wx.MenuItem(self.ViewMenu, MENU_VIEW_HIDE_FLAGGED, "Hide flagged data",
                                       "Hide all the flagged data", wx.ITEM_CHECK)
        self.ViewMenu.AppendItem(self.HideFlagged)
        self.HideDepth = wx.MenuItem(self.ViewMenu, MENU_VIEW_HIDE_DEPTH, "Hide depth",
                                     "Hide the depth visualization on the plot", wx.ITEM_CHECK)
        self.ViewMenu.AppendItem(self.HideDepth)
        self.SVPEditorFrame_menubar.Append(self.ViewMenu, "View")

        # ### Process ###
        self.ProcessMenu = wx.Menu()
        self.ProcessLoadSal = wx.MenuItem(self.ProcessMenu, MENU_PROC_LOAD_SAL, "Load salinity",
                                          "Load salinity from reference cast [XBT only]", wx.ITEM_NORMAL)
        self.ProcessMenu.AppendItem(self.ProcessLoadSal)
        self.ProcessLoadTempSal = wx.MenuItem(self.ProcessMenu, MENU_PROC_LOAD_TEMP_SAL,
                                              "Load temperature/salinity",
                                              "Load temperature and salinity from reference cast [SVP and XBT only]",
                                              wx.ITEM_NORMAL)
        self.ProcessMenu.AppendItem(self.ProcessLoadTempSal)
        self.ProcessLoadSurfSpeed = wx.MenuItem(self.ProcessMenu, MENU_PROC_LOAD_SURFSP, "Get surface sound speed",
                                                "Get the surface sound speed value from SIS", wx.ITEM_NORMAL)
        self.ProcessMenu.AppendItem(self.ProcessLoadSurfSpeed)
        self.ProcessMenu.AppendSeparator()
        self.ProcessExtend = wx.MenuItem(self.ProcessMenu, MENU_PROC_EXTEND_CAST, "Extend cast",
                                         "Extend the cast using the reference cast", wx.ITEM_NORMAL)
        self.ProcessMenu.AppendItem(self.ProcessExtend)
        self.ProcessInspection = wx.Menu()
        self.PlotZoom = wx.MenuItem(self.ProcessInspection, MENU_PROC_INS_ZOOM, "Zoom",
                                    "Zoom on plot by mouse selection", wx.ITEM_RADIO)
        self.ProcessInspection.AppendItem(self.PlotZoom)
        self.PlotFlag = wx.MenuItem(self.ProcessInspection, MENU_PROC_INS_FLAG, "Flag",
                                    "Flag samples on plot by mouse selection", wx.ITEM_RADIO)
        self.ProcessInspection.AppendItem(self.PlotFlag)
        self.PlotUnflag = wx.MenuItem(self.ProcessInspection, MENU_PROC_INS_UNFLAG, "Unflag",
                                      "Unflag samples on plot by mouse selection", wx.ITEM_RADIO)
        self.ProcessInspection.AppendItem(self.PlotUnflag)
        self.PlotInsert = wx.MenuItem(self.ProcessInspection, MENU_PROC_INS_INSERT, "Insert",
                                      "Insert a sample by mouse clicking", wx.ITEM_RADIO)
        self.ProcessInspection.AppendItem(self.PlotInsert)
        self.ProcessMenu.AppendMenu(MENU_PROC_INSPECTION, "Visual inspection", self.ProcessInspection,
                                    "Visual inspection of the resulting profile")
        self.ProcessMenu.AppendSeparator()
        self.ProcessPreviewThinning = wx.MenuItem(self.ProcessMenu, MENU_PROC_PREVIEW_THINNING, "Preview thinning",
                                                  "Preview the thinning required by some client types", wx.ITEM_NORMAL)
        self.ProcessMenu.AppendItem(self.ProcessPreviewThinning)
        self.ProcessSendProfile = wx.MenuItem(self.ProcessMenu, MENU_PROC_SEND_PROFILE, "Send SSP",
                                              "Send the current SSP to the clients", wx.ITEM_NORMAL)
        self.ProcessMenu.AppendItem(self.ProcessSendProfile)
        self.ProcessMenu.AppendSeparator()
        self.ProcessStoreDb = wx.MenuItem(self.ProcessMenu, MENU_PROC_STORE_SSP, "Store SSP",
                                          "Locally store the current SSP data", wx.ITEM_NORMAL)
        self.ProcessMenu.AppendItem(self.ProcessStoreDb)
        self.ProcessRedoSsp = wx.MenuItem(self.ProcessMenu, MENU_PROC_REDO_SSP, "Redo processing",
                                          "Redo the processing by reloading the stored raw data", wx.ITEM_NORMAL)
        self.ProcessMenu.AppendItem(self.ProcessRedoSsp)
        self.ProcessLogMetadata = wx.MenuItem(self.ProcessMenu, MENU_PROC_LOG_METADATA, "Log processing metadata",
                                              "Store the processing metadata in the log DB", wx.ITEM_CHECK)
        self.ProcessMenu.AppendItem(self.ProcessLogMetadata)
        # self.ProcessMenu.AppendSeparator()
        # self.ProcessExpressMode = wx.MenuItem(self.ProcessMenu, MENU_PROC_EXPRESS, "Express mode",
        #                                       "Activate the express mode (be careful!)", wx.ITEM_NORMAL)
        # self.ProcessMenu.AppendItem(self.ProcessExpressMode)
        self.SVPEditorFrame_menubar.Append(self.ProcessMenu, "Process")

        # ### DATABASE ###
        self.DbMenu = wx.Menu()
        # Query
        DbQuery = wx.Menu()
        self.DbQueryInternalDb = wx.MenuItem(DbQuery, MENU_DB_QUERY_INTERNAL_DB, "Internal DB",
                                             "Retrieve the locally stored SSP", wx.ITEM_NORMAL)
        DbQuery.AppendItem(self.DbQueryInternalDb)
        self.DbQueryExternalDb = wx.MenuItem(DbQuery, MENU_DB_QUERY_EXTERNAL_DB, "External DB",
                                             "Retrieve a SSP stored in the select DB", wx.ITEM_NORMAL)
        DbQuery.AppendItem(self.DbQueryExternalDb)
        self.DbMenu.AppendMenu(MENU_DB_QUERY, "Query from", DbQuery,
                               "Retrieve SSP info from databases")
        # Db/Delete
        DbDelete = wx.Menu()
        self.DbDeleteInternalDb = wx.MenuItem(DbDelete, MENU_DB_DELETE_INTERNAL_DB, "Internal DB",
                                              "Delete a locally stored SSP", wx.ITEM_NORMAL)
        DbDelete.AppendItem(self.DbDeleteInternalDb)
        self.DbDeleteExternalDb = wx.MenuItem(DbDelete, MENU_DB_DELETE_EXTERNAL_DB, "External DB",
                                              "Delete a SSP stored in the select DB", wx.ITEM_NORMAL)
        DbDelete.AppendItem(self.DbDeleteExternalDb)
        self.DbMenu.AppendMenu(MENU_DB_DELETE, "Delete SSP", DbDelete, "")

        # Db/Export
        DbExport = wx.Menu()
        self.DbExportShp = wx.MenuItem(DbExport, MENU_DB_EXPORT_SHP, "Shapefile",
                                       "Export all the stored SSPs as a Shapefile", wx.ITEM_NORMAL)
        DbExport.AppendItem(self.DbExportShp)
        self.DbExportKml = wx.MenuItem(DbExport, MENU_DB_EXPORT_KML, "KML",
                                       "Export all the stored SSPs as a KML file", wx.ITEM_NORMAL)
        DbExport.AppendItem(self.DbExportKml)
        self.DbExportCsv = wx.MenuItem(DbExport, MENU_DB_EXPORT_CSV, "CSV",
                                       "Export all the stored SSPs as a Comma-Separated file", wx.ITEM_NORMAL)
        DbExport.AppendItem(self.DbExportCsv)
        self.DbMenu.AppendMenu(MENU_DB_EXPORT, "Export", DbExport, "")

        # Db/Plot
        DbPlot = wx.Menu()
        self.DbPlotMapSsp = wx.MenuItem(DbPlot, MENU_DB_PLOT_MAP_SSP, "Map all SSPs",
                                        "Create a map with all the stored SSPs", wx.ITEM_NORMAL)
        DbPlot.AppendItem(self.DbPlotMapSsp)
        self.DbPlotDailySsp = wx.MenuItem(DbPlot, MENU_DB_PLOT_DAILY_SSP, "Create daily plot",
                                          "Create a SSP plot for each day", wx.ITEM_NORMAL)
        DbPlot.AppendItem(self.DbPlotDailySsp)
        self.DbSaveDailySsp = wx.MenuItem(DbPlot, MENU_DB_SAVE_DAILY_SSP, "Save daily plot",
                                          "Save a SSP plot for each day", wx.ITEM_NORMAL)
        DbPlot.AppendItem(self.DbSaveDailySsp)
        self.DbMenu.AppendMenu(MENU_DB_PLOT, "Plot", DbPlot, "")

        self.SVPEditorFrame_menubar.Append(self.DbMenu, "Database")

        # ### Tools ###
        self.ToolsMenu = wx.Menu()
        ServerMenu = wx.Menu()
        self.ToolsServerStart = wx.MenuItem(ServerMenu, MENU_SERVER_START, "Start server",
                                            "Start SIS server mode", wx.ITEM_NORMAL)
        ServerMenu.AppendItem(self.ToolsServerStart)
        self.ToolsServerSend = wx.MenuItem(ServerMenu, MENU_SERVER_SEND, "Force send",
                                           "Force to send a SSP", wx.ITEM_NORMAL)
        ServerMenu.AppendItem(self.ToolsServerSend)
        self.ToolsServerStop = wx.MenuItem(ServerMenu, MENU_SERVER_STOP, "Stop server",
                                           "Stop SIS server mode", wx.ITEM_NORMAL)
        ServerMenu.AppendItem(self.ToolsServerStop)
        ServerMenu.AppendSeparator()
        self.ServerLogMetadata = wx.MenuItem(ServerMenu, MENU_SERVER_LOG_METADATA, "Log server metadata",
                                             "Store the server metadata in the log DB", wx.ITEM_CHECK)
        ServerMenu.AppendItem(self.ServerLogMetadata)
        self.ToolsMenu.AppendMenu(MENU_TOOLS_SERVER, "Server", ServerMenu, "")
        self.ToolsMenu.AppendSeparator()

        self.ToolsRefMon = wx.MenuItem(self.ToolsMenu, MENU_TOOLS_REF_MON, "Refraction Monitor",
                                       "Open the refraction monitor", wx.ITEM_NORMAL)
        self.ToolsMenu.AppendItem(self.ToolsRefMon)
        self.ToolsGeoMap = wx.MenuItem(self.ToolsMenu, MENU_TOOLS_GEO_MONITOR, "Geo Monitor",
                                       "Open the Geo Monitor", wx.ITEM_NORMAL)
        self.ToolsMenu.AppendItem(self.ToolsGeoMap)
        self.ToolsMenu.AppendSeparator()

        ReferenceMenu = wx.Menu()
        self.ToolsSetReferenceCast = wx.MenuItem(self.ToolsMenu, MENU_TOOLS_SET_REFERENCE_CAST,
                                                 "Set as reference cast",
                                                 "Set the current SSP as reference cast", wx.ITEM_NORMAL)
        ReferenceMenu.AppendItem(self.ToolsSetReferenceCast)
        self.ToolsEditReferenceCast = wx.MenuItem(self.ToolsMenu, MENU_TOOLS_EDIT_REFERENCE_CAST,
                                                  "Edit the reference cast",
                                                  "Edit the current reference cast", wx.ITEM_NORMAL)
        ReferenceMenu.AppendItem(self.ToolsEditReferenceCast)
        self.ToolsClearReferenceCast = wx.MenuItem(self.ToolsMenu, MENU_TOOLS_CLEAR_REFERENCE_CAST,
                                                   "Clear the reference cast",
                                                   "Clear the current reference cast", wx.ITEM_NORMAL)
        ReferenceMenu.AppendItem(self.ToolsClearReferenceCast)
        self.ToolsInfoSettings = wx.MenuItem(self.ToolsMenu, MENU_TOOLS_SETTINGS, "Info settings",
                                             "Provide settings information", wx.ITEM_NORMAL)
        self.ToolsMenu.AppendMenu(MENU_TOOLS_REFERENCE, "Reference cast", ReferenceMenu,
                                  "Actions about a reference cast")
        self.ToolsMenu.AppendSeparator()
        self.ToolsMenu.AppendItem(self.ToolsInfoSettings)
        self.SVPEditorFrame_menubar.Append(self.ToolsMenu, "Tools")

        self.HelpMenu = wx.Menu()
        self.HelpManual = wx.MenuItem(self.HelpMenu, MENU_HELP_MANUAL, "Manual",
                                      "Open the manual", wx.ITEM_NORMAL)
        self.HelpMenu.AppendItem(self.HelpManual)
        self.HelpMenu.AppendSeparator()
        self.HelpAbout = wx.MenuItem(self.HelpMenu, MENU_HELP_ABOUT, "About",
                                     "Info about the application", wx.ITEM_NORMAL)
        self.HelpMenu.AppendItem(self.HelpAbout)
        self.SVPEditorFrame_menubar.Append(self.HelpMenu, "Help")
        self.SetMenuBar(self.SVPEditorFrame_menubar)

        self.frame_statusbar = self.CreateStatusBar(2, 0)
        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_MENU, self.on_file_import_castaway, self.FileImpCastaway)
        self.Bind(wx.EVT_MENU, self.on_file_import_digibar_pro, self.FileImpDigibarPro)
        self.Bind(wx.EVT_MENU, self.on_file_import_digibar_s, self.FileImpDigibarS)
        self.Bind(wx.EVT_MENU, self.on_file_import_sippican, self.FileImpSippican)
        self.Bind(wx.EVT_MENU, self.on_file_import_seabird, self.FileImpSeabird)
        self.Bind(wx.EVT_MENU, self.on_file_import_turo, self.FileImpTuro)
        self.Bind(wx.EVT_MENU, self.on_file_import_unb, self.FileImpUNB)
        self.Bind(wx.EVT_MENU, self.on_file_import_valeport_midas, self.FileImpValeMidas)
        self.Bind(wx.EVT_MENU, self.on_file_import_valeport_monitor, self.FileImpValeMonitor)
        self.Bind(wx.EVT_MENU, self.on_file_import_valeport_minisvp, self.FileImpValeMiniS)
        self.Bind(wx.EVT_MENU, self.on_file_import_idronaut, self.FileImpIdronaut)
        self.Bind(wx.EVT_MENU, self.on_file_import_saiv, self.FileImpSaiv)

        self.Bind(wx.EVT_MENU, self.on_file_query_woa09, self.FileQueryWoa)
        self.Bind(wx.EVT_MENU, self.on_file_query_rtofs, self.FileQueryRtofs)
        self.Bind(wx.EVT_MENU, self.on_file_query_sis, self.FileQuerySis)

        self.Bind(wx.EVT_MENU, self.on_file_export_cast, self.FileExpCast)
        self.Bind(wx.EVT_MENU, self.on_file_export_asvp, self.FileExpAsvp)
        self.Bind(wx.EVT_MENU, self.on_file_export_pro, self.FileExpPro)
        self.Bind(wx.EVT_MENU, self.on_file_export_vel, self.FileExpVel)
        self.Bind(wx.EVT_MENU, self.on_file_export_ixblue, self.FileExpIxblue)
        self.Bind(wx.EVT_MENU, self.on_file_export_hips, self.FileExpHips)
        self.Bind(wx.EVT_MENU, self.on_file_export_unb, self.FileExpUnb)
        self.Bind(wx.EVT_MENU, self.on_file_export_elac, self.FileExpElac)
        self.Bind(wx.EVT_MENU, self.on_file_export_csv, self.FileExpCsv)
        self.Bind(wx.EVT_MENU, self.on_file_clear, self.FileClear)
        self.Bind(wx.EVT_MENU, self.on_file_exit, self.FileExit)

        self.Bind(wx.EVT_MENU, self.on_plot_zoom, self.PlotZoom)
        self.Bind(wx.EVT_MENU, self.on_plot_flag, self.PlotFlag)
        self.Bind(wx.EVT_MENU, self.on_plot_unflag, self.PlotUnflag)
        self.Bind(wx.EVT_MENU, self.on_plot_insert, self.PlotInsert)

        self.Bind(wx.EVT_MENU, self.on_reset_view, self.ResetView)
        self.Bind(wx.EVT_MENU, self.on_view_hide_woa, self.ViewHideWOA)
        self.Bind(wx.EVT_MENU, self.on_view_hide_flagged, self.HideFlagged)
        self.Bind(wx.EVT_MENU, self.on_view_hide_depth, self.HideDepth)

        self.Bind(wx.EVT_MENU, self.on_process_load_salinity, self.ProcessLoadSal)
        self.Bind(wx.EVT_MENU, self.on_process_load_temp_and_sal, self.ProcessLoadTempSal)
        self.Bind(wx.EVT_MENU, self.on_process_load_surface_ssp, self.ProcessLoadSurfSpeed)
        self.Bind(wx.EVT_MENU, self.on_process_extend, self.ProcessExtend)
        self.Bind(wx.EVT_MENU, self.on_process_preview_thinning, self.ProcessPreviewThinning)
        self.Bind(wx.EVT_MENU, self.on_process_send_profile, self.ProcessSendProfile)
        self.Bind(wx.EVT_MENU, self.on_process_store_db, self.ProcessStoreDb)
        self.Bind(wx.EVT_MENU, self.on_process_redo_processing, self.ProcessRedoSsp)
        self.Bind(wx.EVT_MENU, self.on_process_log_metadata, self.ProcessLogMetadata)
        # self.Bind(wx.EVT_MENU, self.on_process_express_mode, self.ProcessExpressMode)

        self.Bind(wx.EVT_MENU, self.on_db_query_internal_db, self.DbQueryInternalDb)
        self.Bind(wx.EVT_MENU, self.on_db_query_external_db, self.DbQueryExternalDb)
        self.Bind(wx.EVT_MENU, self.on_db_delete_internal, self.DbDeleteInternalDb)
        self.Bind(wx.EVT_MENU, self.on_db_delete_external, self.DbDeleteExternalDb)
        self.Bind(wx.EVT_MENU, self.on_db_export_shp, self.DbExportShp)
        self.Bind(wx.EVT_MENU, self.on_db_export_kml, self.DbExportKml)
        self.Bind(wx.EVT_MENU, self.on_db_export_csv, self.DbExportCsv)
        self.Bind(wx.EVT_MENU, self.on_db_plot_map_ssp, self.DbPlotMapSsp)
        self.Bind(wx.EVT_MENU, self.on_db_plot_daily_ssp, self.DbPlotDailySsp)
        self.Bind(wx.EVT_MENU, self.on_db_save_daily_ssp, self.DbSaveDailySsp)

        self.Bind(wx.EVT_MENU, self.on_tools_refraction_monitor, self.ToolsRefMon)
        self.Bind(wx.EVT_MENU, self.on_tools_geo_monitor, self.ToolsGeoMap)
        self.Bind(wx.EVT_MENU, self.on_tools_server_start, self.ToolsServerStart)
        self.Bind(wx.EVT_MENU, self.on_tools_server_send, self.ToolsServerSend)
        self.Bind(wx.EVT_MENU, self.on_tools_server_stop, self.ToolsServerStop)
        self.Bind(wx.EVT_MENU, self.on_tools_server_log_metadata, self.ServerLogMetadata)
        self.Bind(wx.EVT_MENU, self.on_tools_set_reference_cast, self.ToolsSetReferenceCast)
        self.Bind(wx.EVT_MENU, self.on_tools_edit_reference_cast, self.ToolsEditReferenceCast)
        self.Bind(wx.EVT_MENU, self.on_tools_clear_reference_cast, self.ToolsClearReferenceCast)
        self.Bind(wx.EVT_MENU, self.on_tools_info_settings, self.ToolsInfoSettings)

        self.Bind(wx.EVT_MENU, self.on_help_manual, self.HelpManual)
        self.Bind(wx.EVT_MENU, self.on_help_about, self.HelpAbout)

    def __set_properties(self):
        self.SetTitle("SSP Manager")
        self.SetSize((1000, 800))
        self.frame_statusbar.SetStatusWidths([-1, 400])
        SSPManFrame_statusbar_fields = ["", ""]
        for i in range(len(SSPManFrame_statusbar_fields)):
            self.frame_statusbar.SetStatusText(SSPManFrame_statusbar_fields[i], i)

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer_1)
        self.Layout()
        self.SetSize((1000, 800))

    def on_file_query_woa09(self, event):
        log.info("Event handler 'on_file_query_woa09' not implemented!")
        event.Skip()

    def on_file_query_rtofs(self, event):
        log.info("Event handler 'on_file_query_rtofs' not implemented!")
        event.Skip()

    def on_file_query_sis(self, event):
        log.info("Event handler 'on_file_query_sis' not implemented!")
        event.Skip()

    def on_process_store_db(self, event):
        log.info("Event handler 'on_process_store_db' not implemented!")
        event.Skip()

    def on_process_log_metadata(self, event):
        log.info("Event handler 'on_process_log_metadata' not implemented!")
        event.Skip()

    def on_tools_set_reference_cast(self, event):
        log.info("Event handler 'on_tools_set_reference_cast' not implemented!")
        event.Skip()

    def on_tools_edit_reference_cast(self, event):
        log.info("Event handler 'on_tools_edit_reference_cast' not implemented!")
        event.Skip()

    def on_tools_clear_reference_cast(self, event):
        log.info("Event handler 'on_tools_clear_reference_cast' not implemented!")
        event.Skip()

    def on_file_import_castaway(self, event):
        log.info("Event handler 'on_file_import_castaway' not implemented!")
        event.Skip()

    def on_file_import_digibar_pro(self, event):
        log.info("Event handler 'on_file_import_digibar_pro' not implemented!")
        event.Skip()

    def on_file_import_digibar_s(self, event):
        log.info("Event handler 'on_file_import_digibar_s' not implemented!")
        event.Skip()

    def on_file_import_sippican(self, event):
        log.info("Event handler 'on_file_import_sippican' not implemented!")
        event.Skip()

    def on_file_import_seabird(self, event):
        log.info("Event handler 'on_file_import_seabird' not implemented!")
        event.Skip()

    def on_file_import_turo(self, event):
        log.info("Event handler 'on_file_import_turo' not implemented!")
        event.Skip()

    def on_file_import_unb(self, event):
        log.info("Event handler 'on_file_import_unb' not implemented!")
        event.Skip()

    def on_file_import_valeport_midas(self, event):
        log.info("Event handler 'on_file_import_valeport_midas' not implemented!")
        event.Skip()

    def on_file_import_valeport_monitor(self, event):
        log.info("Event handler 'on_file_import_valeport_monitor' not implemented!")
        event.Skip()

    def on_file_import_valeport_minisvp(self, event):
        log.info("Event handler 'on_file_import_valeport_minisvp' not implemented!")
        event.Skip()

    def on_file_import_idronaut(self, event):
        log.info("Event handler 'on_file_import_idronaut' not implemented!")
        event.Skip()

    def on_file_import_saiv(self, event):
        log.info("Event handler 'on_file_import_saiv' not implemented!")
        event.Skip()

    def on_file_export_cast(self, event):
        log.info("Event handler 'on_file_export_cast' not implemented!")
        event.Skip()

    def on_file_export_asvp(self, event):
        log.info("Event handler 'on_file_export_asvp' not implemented!")
        event.Skip()

    def on_file_export_pro(self, event):
        log.info("Event handler 'on_file_export_pro' not implemented!")
        event.Skip()

    def on_file_export_vel(self, event):
        log.info("Event handler 'on_file_export_vel' not implemented!")
        event.Skip()

    def on_file_export_ixblue(self, event):
        log.info("Event handler 'on_file_export_ixblue' not implemented!")
        event.Skip()

    def on_file_export_hips(self, event):
        log.info("Event handler 'on_file_export_hips' not implemented!")
        event.Skip()

    def on_file_export_unb(self, event):
        log.info("Event handler 'on_file_export_unb' not implemented!")
        event.Skip()

    def on_file_export_elac(self, event):
        log.info("Event handler 'on_file_export_elac' not implemented!")
        event.Skip()

    def on_file_export_csv(self, event):
        log.info("Event handler 'on_file_export_csv' not implemented!")
        event.Skip()

    def on_file_clear(self, event):
        log.info("Event handler 'on_file_clear' not implemented!")
        event.Skip()

    def on_file_exit(self, event):
        log.info("Event handler 'on_file_exit' not implemented!")
        event.Skip()

    def on_plot_zoom(self, event):
        log.info("Event handler 'on_plot_zoom' not implemented!")
        event.Skip()

    def on_plot_flag(self, event):
        log.info("Event handler 'on_plot_flag' not implemented!")
        event.Skip()

    def on_plot_unflag(self, event):
        log.info("Event handler 'on_plot_unflag' not implemented!")
        event.Skip()

    def on_plot_insert(self, event):
        log.info("Event handler 'on_plot_insert' not implemented!")
        event.Skip()

    def on_reset_view(self, event):
        log.info("Event handler 'on_reset_view' not implemented!")
        event.Skip()

    def on_view_hide_woa(self, event):
        log.info("Event handler 'on_view_hide_woa' not implemented!")
        event.Skip()

    def on_view_hide_flagged(self, event):
        log.info("Event handler 'on_view_hide_flagged' not implemented!")
        event.Skip()

    def on_view_hide_depth(self, event):
        log.info("Event handler 'on_view_hide_depth' not implemented!")
        event.Skip()

    def on_tools_refraction_monitor(self, event):
        log.info("Event handler 'on_tools_refraction_monitor' not implemented!")
        event.Skip()

    def on_tools_geo_monitor(self, event):
        log.info("Event handler 'on_tools_geo_monitor' not implemented!")
        event.Skip()

    # def on_process_express_mode(self, event):
    # log.info("Event handler `OnToolsExpress' not implemented!")
    #     event.Skip()

    def on_process_load_salinity(self, event):
        log.info("Event handler 'on_process_load_salinity' not implemented!")
        event.Skip()

    def on_process_load_temp_and_sal(self, event):
        log.info("Event handler 'on_process_load_temp_and_sal' not implemented!")
        event.Skip()

    def on_process_load_surface_ssp(self, event):
        log.info("Event handler 'on_process_load_surface_ssp' not implemented!")
        event.Skip()

    def on_process_extend(self, event):
        log.info("Event handler 'on_process_extend' not implemented!")
        event.Skip()

    def on_process_preview_thinning(self, event):
        log.info("Event handler 'on_process_preview_thinning' not implemented!")
        event.Skip()

    def on_process_send_profile(self, event):
        log.info("Event handler 'on_process_send_profile' not implemented!")
        event.Skip()

    def on_process_redo_processing(self, event):
        log.info("Event handler 'on_process_redo_processing' not implemented!")
        event.Skip()

    def on_db_query_internal_db(self, event):
        log.info("Event handler 'on_db_query_internal' not implemented!")
        event.Skip()

    def on_db_query_external_db(self, event):
        log.info("Event handler 'on_db_query_external' not implemented!")
        event.Skip()

    def on_db_delete_internal(self, event):
        log.info("Event handler 'on_db_delete_internal' not implemented!")
        event.Skip()

    def on_db_delete_external(self, event):
        log.info("Event handler 'on_db_delete_external' not implemented!")
        event.Skip()

    def on_db_export_shp(self, event):
        log.info("Event handler 'on_db_export_shp' not implemented!")
        event.Skip()

    def on_db_export_kml(self, event):
        log.info("Event handler 'on_db_export_kml' not implemented!")
        event.Skip()

    def on_db_export_csv(self, event):
        log.info("Event handler 'on_db_export_csv' not implemented!")
        event.Skip()

    def on_db_plot_map_ssp(self, event):
        log.info("Event handler 'on_db_plot_map_ssp' not implemented!")
        event.Skip()

    def on_db_plot_daily_ssp(self, event):
        log.info("Event handler 'on_db_plot_daily_ssp' not implemented!")
        event.Skip()

    def on_db_save_daily_ssp(self, event):
        log.info("Event handler 'on_db_save_daily_ssp' not implemented!")
        event.Skip()

    def on_tools_info_settings(self, event):
        log.info("Event handler 'on_tools_info_settings' not implemented!")
        event.Skip()

    def on_tools_server_start(self, event):
        log.info("Event handler 'on_tools_server_start' not implemented!")
        event.Skip()

    def on_tools_server_send(self, event):
        log.info("Event handler 'on_tools_server_send' not implemented!")
        event.Skip()

    def on_tools_server_stop(self, event):
        log.info("Event handler 'on_tools_server_stop' not implemented!")
        event.Skip()

    def on_tools_server_log_metadata(self, event):
        log.info("Event handler 'on_tools_server_log_metadata' not implemented!")
        event.Skip()

    def on_help_manual(self, event):
        log.info("Event handler 'on_help_manual' not implemented!")
        event.Skip()

    def on_help_about(self, event):
        log.info("Event handler 'on_help_about' not implemented!")
        event.Skip()
