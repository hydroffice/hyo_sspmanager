from __future__ import absolute_import, division, print_function, unicode_literals

import os

from ..cast_reader import CastReader
from ..ssp_db import SspDb
from ..ssp_dicts import Dicts
from ...base.gdal_aux import GdalAux


if __name__ == "__main__":

    # rdr = CastReader()
    # # rdr.read_cast("Z:\\raw\\XBT\\C3_00010.EDF", Dicts.import_formats["SIPPICAN"])
    # # rdr.read_cast("Z:\\raw\\XBT\\T7_00005.EDF", Dicts.import_formats["SIPPICAN"])
    # rdr.read_casts_in_folder("Z:\\raw\\XBT", Dicts.import_formats["SIPPICAN"])
    # print("successfully read: %s" % rdr.good_count)
    # print("failures: %s" % rdr.fail_count)
    # rdr.casts.date_time_sort()
    # print(rdr.casts)

    here = os.path.abspath(os.path.dirname(__file__))
    test_db = SspDb(db_path=os.path.join(here, "tmp", "test.db"))
    # ret0 = test_db.add_casts(rdr.casts)
    # print("added cast: %s" % ret0)

    ret0 = test_db.list_all_ssp_pks()
    print(len(ret0))

    ret0 = test_db.list_ssp_pks_by_survey_name()
    print(len(ret0))

    # if len(ret0) > 0:
    #     ssp_data = test_db.get_ssp_by_pk(ret0[0][0])
    #     print(ssp_data)
    #
    # print("\ntotal ssp rows: %s" % test_db.check_table_total_rows('ssp', True))
    # test_db.check_table_cols_settings('ssp', True)
    # test_db.check_tables_values_in_cols('ssp', True)

    # print("\ndelete ssp")
    # test_db.delete_ssp_by_pk(ret0[0][0])

    # retrieve printable ssp view rows
    ret0 = test_db.get_printable_ssp_view()
    print("ssp view rows:\n%s" % ret0)

    # # convert ssp view to ogr
    # test_db.convert_ssp_view_to_ogr()
    # test_db.convert_ssp_view_to_ogr(GdalAux.ogr_formats[b'KML'])
    # test_db.convert_ssp_view_to_ogr(GdalAux.ogr_formats[b'CSV'])

    #test_db.map_ssp_view()

    test_db.create_daily_plots()

    # close db
    print("\nclose db")
    test_db.close()
