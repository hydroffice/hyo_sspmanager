from __future__ import absolute_import, division, print_function

import sys
from PySide import QtGui

from . import mainwin


def gui(verbose=False):
    """create the main windows and the event loop"""

    app = QtGui.QApplication(sys.argv)

    main = mainwin.MainWin(verbose=True)
    main.show()

    sys.exit(app.exec_())
