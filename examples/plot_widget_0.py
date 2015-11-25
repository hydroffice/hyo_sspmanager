from __future__ import absolute_import, division, print_function, unicode_literals

from ..plot import widget
from ..project import Project

import sys
from matplotlib.backends.qt_compat import QtGui, QtCore

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    win = QtGui.QMainWindow()
    win.setWindowTitle("Plot")

    prj = Project(verbose=True, verbose_config=False)

    plot_widget = widget.Widget(prj=prj, verbose=True)
    win.setCentralWidget(plot_widget)
    win.show()

    sys.exit(app.exec_())

