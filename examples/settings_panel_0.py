from __future__ import absolute_import, division, print_function, unicode_literals

from ..gui.settings_tool import SettingsTool
from ..project import Project

import sys
from matplotlib.backends.qt_compat import QtGui, QtCore

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    prj = Project(verbose=True, verbose_config=False)

    settings_widget = SettingsTool(prj=prj, verbose=True)
    settings_widget.show()

    sys.exit(app.exec_())


