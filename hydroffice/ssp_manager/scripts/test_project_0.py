from __future__ import absolute_import, division, print_function, unicode_literals

from .. import project

prj = project.Project(with_listeners=False, with_woa09=False, with_rtofs=False,
                      verbose=True, verbose_config=False,
                      callback_debug_print=None)
prj.release()


