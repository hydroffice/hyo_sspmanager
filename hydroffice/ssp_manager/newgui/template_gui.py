from __future__ import absolute_import, division, print_function, unicode_literals

import sys
from PySide import QtGui

from .. import helper
from . import mainwin


def gui():
    """ graphical user interface """
    print(helper.Helper.pkg_info())
    print("... gui launching\n")

    app = QtGui.QApplication(sys.argv)

    main = mainwin.MainWin()
    main.show()

    sys.exit(app.exec_())
