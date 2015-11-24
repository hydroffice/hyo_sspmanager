from __future__ import absolute_import, division, print_function, unicode_literals

import pytest


class TestSSPError(object):

    from hydroffice.ssp.helper import SspError
    err = SspError("test")

    def test_is_instance(self):
        assert isinstance(self.err, Exception)
        from hydroffice.base.helper import HyOError
        assert isinstance(self.err, HyOError)

    def test_raise(self):
        from hydroffice.ssp.helper import SspError
        try:
            raise self.err
        except SspError as e:
            assert "test" in str(e)

    def test_has_message(self):
        assert hasattr(self.err, 'message')


class TestHelper(object):

    from hydroffice.ssp.helper import Helper
    hlp = Helper()

    def test_helper_has_explore_folder(self):
        from hydroffice.base.helper import Helper
        import inspect
        # class method
        assert inspect.ismethod(Helper.explore_folder) and (Helper.explore_folder.__self__ is Helper)

    def test_is_windows(self):
        assert isinstance(self.hlp.is_windows(), bool)

    def test_default_projects_folder(self):
        import os
        assert os.path.exists(self.hlp.default_projects_folder())

    def test_pkg_info(self):
        output = self.hlp.pkg_info()
        assert "gmasetti@ccom.unh.edu" in str(output)

    def test_is_64bit_os(self):
        assert isinstance(self.hlp.is_64bit_os(), bool)

    def test_is_64bit_python(self):
        assert isinstance(self.hlp.is_64bit_python(), bool)

    def test_list_hydro_packages(self):
        assert len(self.hlp.list_hydro_packages()) >= 1  # at least one

    def test_is_python_less_than(self):
        assert not self.hlp.is_python_less_than(2, 6)  # Python 2.6

    def test_get_root_path(self):
        assert len(self.hlp.get_root_path()) >= 1  # at least /
        assert len(self.hlp.get_root_path()) <= 3  # maxixum C:\

    # ### END OF SHARED WITH BASE.HELPER ###
