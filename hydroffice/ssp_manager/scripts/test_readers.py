from __future__ import absolute_import, division, print_function, unicode_literals

from ..cast_reader import CastReader
from ..ssp_dicts import Dicts

if __name__ == "__main__":

    rdr = CastReader()
    rdr.test_drivers()
    print("\ntotal casts: %s" % rdr.total_read_casts())
    print("successfully read: %s" % rdr.good_count)
    print("failures: %s" % rdr.fail_count)
    print(rdr.casts)

    # rdr = CastReader()
    # rdr.read_casts_in_folder("Z:\\raw\\XBT", Dicts.import_formats["SIPPICAN"])
    # print("\ntotal casts: %s" % rdr.total_read_casts())
    # print("successfully read: %s" % rdr.good_count)
    # print("failures: %s" % rdr.fail_count)
    # print(rdr.casts)
    #
    # rdr.read_cast("Z:\\raw\\XBT\\C3_00010.EDF", Dicts.import_formats["SIPPICAN"])
    # print("\ntotal casts: %s" % rdr.total_read_casts())
    # print("successfully read: %s" % rdr.good_count)
    # print("failures: %s" % rdr.fail_count)
    # rdr.casts.date_time_sort()
    # print(rdr.casts)