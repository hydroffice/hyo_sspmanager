from __future__ import absolute_import, division, print_function, unicode_literals

import pytest


class TestProject(object):

    from hydroffice.ssp.project import Project
    import os
    prj = Project(with_listeners=False, with_woa09=False, with_rtofs=False)
    prj.release()

    def test_is_instance(self):
        from hydroffice.base.project import Project
        assert isinstance(self.prj, Project)

    def test_setting_getting_output_folder(self):
        import os
        test_dir = os.path.curdir
        self.prj.set_output_folder(test_dir)
        assert self.prj.get_output_folder() == test_dir

