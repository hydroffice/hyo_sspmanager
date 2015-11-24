from __future__ import absolute_import, division, print_function, unicode_literals

import sqlite3
import os
from datetime import datetime as dt
import numpy as np
import logging

log = logging.getLogger(__name__)

from osgeo import gdal
from osgeo import ogr
from hydroffice.base.gdal_aux import GdalAux

from matplotlib import rcParams
rcParams.update(
    {
        'font.family': 'sans-serif',
        'font.size': 9
    }
)
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes
from mpl_toolkits.axes_grid1.inset_locator import mark_inset

from hydroffice.base.base_objects import BaseDbObject
from hydroffice.base.helper import HyOError

from . import __version__
from .ssp_collection import SspCollection
from .ssp import SspData
from .ssp_dicts import Dicts
from .helper import Helper, SspError


class DbError(SspError):
    """ Error raised for db issues """
    def __init__(self, message, *args):
        self.message = message
        # allow users initialize misc. arguments as any other builtin Error
        super(DbError, self).__init__(message, *args)


class SspDb(BaseDbObject):
    """ class that stores SSPs in a SQLite db """

    def __init__(self, db_path=None):
        if not db_path:
            db_path = os.path.join(Helper.default_projects_folder(), "__data__.db")
        super(SspDb, self).__init__(db_path=db_path)
        self.tmp_data = None
        self.tmp_ssp_pk = None

        self.export_folder = os.path.join(Helper.default_projects_folder(), "db_export")
        if not os.path.exists(self.export_folder):
            os.makedirs(self.export_folder)

        self.plots_folder = os.path.join(Helper.default_projects_folder(), "plots")
        if not os.path.exists(self.plots_folder):
            os.makedirs(self.plots_folder)

        # define the output path
        self.export_ssp_view_path = os.path.join(self.export_folder, "ssp_view")

        self.reconnect_or_create()

    def build_tables(self):
        if not self.conn:
            log.error("missing db connection")
            return False

        try:
            with self.conn:
                if self.conn.execute("""
                                     PRAGMA foreign_keys
                                     """):
                    log.info("foreign keys active")
                else:
                    log.error("foreign keys not active")
                    return False

                self.conn.execute("""
                                  CREATE TABLE IF NOT EXISTS survey(
                                     survey_name text PRIMARY KEY NOT NULL,
                                     survey_creation timestamp NOT NULL,
                                     ssp_pkg_release text,
                                     comments text)
                                  """)

                self.conn.execute("""
                                  CREATE TABLE IF NOT EXISTS ssp_pk(
                                     id INTEGER PRIMARY KEY,
                                     cast_datetime timestamp NOT NULL,
                                     cast_position point NOT NULL)
                                  """)

                self.conn.execute("""
                                  CREATE TABLE IF NOT EXISTS ssp(
                                     pk integer NOT NULL,
                                     survey_name text NOT NULL,
                                     original_path text NOT NULL,
                                     sensor_type text NOT NULL,
                                     source_info text NOT NULL,
                                     driver text NOT NULL,
                                     PRIMARY KEY (pk),
                                     FOREIGN KEY(survey_name) REFERENCES survey(survey_name),
                                     FOREIGN KEY(pk) REFERENCES ssp_pk(id))
                                  """)

                self.conn.execute("""
                                  CREATE TABLE IF NOT EXISTS raw_samples(
                                     ssp_pk integer NOT NULL,
                                     depth real NOT NULL,
                                     speed real,
                                     temperature real,
                                     salinity real,
                                     source int NOT NULL DEFAULT  0,
                                     flag int NOT NULL DEFAULT 0,
                                     PRIMARY KEY (ssp_pk, depth),
                                     FOREIGN KEY(ssp_pk)
                                        REFERENCES ssp(pk))
                                  """)

                self.conn.execute("""
                                  CREATE TABLE IF NOT EXISTS mod_samples(
                                     ssp_pk integer NOT NULL,
                                     depth real NOT NULL,
                                     speed real,
                                     temperature real,
                                     salinity real,
                                     source int NOT NULL DEFAULT  0,
                                     flag int NOT NULL DEFAULT 0,
                                     PRIMARY KEY (ssp_pk, depth),
                                     FOREIGN KEY(ssp_pk)
                                        REFERENCES ssp(pk))
                                  """)

                self.conn.execute("""
                                  CREATE TABLE IF NOT EXISTS sis_samples(
                                     ssp_pk integer NOT NULL,
                                     depth real NOT NULL,
                                     speed real,
                                     temperature real,
                                     salinity real,
                                     source int NOT NULL DEFAULT  0,
                                     flag int NOT NULL DEFAULT 0,
                                     PRIMARY KEY (ssp_pk, depth),
                                     FOREIGN KEY(ssp_pk)
                                        REFERENCES ssp(pk))
                                  """)

                self.conn.execute("""
                                  CREATE VIEW IF NOT EXISTS ssp_view AS
                                     SELECT pk, cast_datetime, cast_position, survey_name, original_path, sensor_type,
                                        source_info, driver
                                        FROM ssp a LEFT OUTER JOIN ssp_pk b ON a.pk=b.id
                                  """)

            return True

        except sqlite3.Error as e:
            log.error("during building tables, %s: %s" % (type(e), e))
            return False

    def add_casts(self, ssp_coll):
        if not isinstance(ssp_coll, SspCollection):
            raise DbError("passed NOT a SspCollection instance")

        if not self.conn:
            log.error("missing db connection")
            return False

        with self.conn:
            for self.tmp_data in ssp_coll.data:

                log.info("got a new SSP to store:\n%s" % self.tmp_data)

                if not self._add_survey_if_missing():
                    log.error("unable to add survey: %s" % self.tmp_data.survey_name)
                    return False

                if not self._get_ssp_pk():
                    log.error("unable to get ssp pk: %s" % self.tmp_ssp_pk)
                    return False

                if not self._delete_old_ssp():
                    log.error("unable to clean ssp")
                    return False

                if not self._add_ssp():
                    log.error("unable to add ssp")
                    return False

                if not self._add_ssp_raw_samples():
                    log.error("unable to add ssp raw samples")
                    return False

                if not self._add_ssp_mod_samples():
                    log.error("unable to add ssp modified samples")
                    return False

                if self.tmp_data.sis_data is not None:
                    if not self._add_ssp_sis_samples():
                        log.error("unable to add ssp sis samples")
                        return False

        return True

    def _add_survey_if_missing(self):
        """add a survey row using the passed information (name) only if the survey is not present"""

        try:
            ret = self.conn.execute("""
                                    SELECT COUNT(survey_name) FROM survey WHERE survey_name=?
                                    """, (self.tmp_data.survey_name, )).fetchone()
            log.info("found %s survey named %s" % (ret[0], self.tmp_data.survey_name))

            if ret[0] == 0:
                srv_row = (self.tmp_data.survey_name, dt.now(), str(__version__), "")
                log.info("inserting: %s" % ", ".join(map(str, srv_row)))

                self.conn.execute("""
                                  INSERT INTO survey VALUES (?, ?, ?, ?)
                                  """, srv_row)

        except sqlite3.Error as e:
            log.error("%s: %s" % (type(e), e))
            return False

        return True

    def _get_ssp_pk(self):

        if not self.conn:
            log.error("missing db connection")
            return False

        try:
            # check if the ssp key is present
            ret = self.conn.execute("""
                                    SELECT COUNT(*) FROM ssp_pk WHERE cast_datetime=? AND cast_position=?
                                    """, (self.tmp_data.date_time,
                                          SspDb.Point(self.tmp_data.longitude, self.tmp_data.latitude),)).fetchone()
            # if not present, add it
            if ret[0] == 0:
                log.info("add new spp pk for %s @ %s"
                                % (self.tmp_data.date_time,
                                   SspDb.Point(self.tmp_data.longitude, self.tmp_data.latitude)))
                self.conn.execute("""
                                  INSERT INTO ssp_pk VALUES (NULL, ?, ?)
                                  """, (self.tmp_data.date_time,
                                        SspDb.Point(self.tmp_data.longitude, self.tmp_data.latitude)))
        except sqlite3.Error as e:
            log.error("during ssp pk check, %s: %s" % (type(e), e))
            return False

        try:
            # return the ssp pk
            ret = self.conn.execute("""
                                    SELECT rowid FROM ssp_pk WHERE cast_datetime=? AND cast_position=?
                                    """, (self.tmp_data.date_time,
                                          SspDb.Point(self.tmp_data.longitude, self.tmp_data.latitude),)).fetchone()
            log.info("spp pk: %s" % ret[b'id'])
            self.tmp_ssp_pk = ret[b'id']

        except sqlite3.Error as e:
            log.error("during ssp pk retrieve, %s: %s" % (type(e), e))
            return False

        return True

    def _delete_old_ssp(self, full=False):
        """Delete all the entries with the selected pk, with 'full' also the pk from ssp_pk"""

        try:
            self.conn.execute("""DELETE FROM raw_samples WHERE ssp_pk=?""", (self.tmp_ssp_pk, ))
            log.info("deleted %s pk entries from raw_samples" % self.tmp_ssp_pk)

        except sqlite3.Error as e:
            log.error("during deletion from raw_samples, %s: %s" % (type(e), e))
            return False

        try:
            self.conn.execute("""DELETE FROM mod_samples WHERE ssp_pk=?""", (self.tmp_ssp_pk, ))
            log.info("deleted %s pk entries from mod_samples" % self.tmp_ssp_pk)

        except sqlite3.Error as e:
            log.error("during deletion from mod_samples, %s: %s" % (type(e), e))
            return False

        try:
            self.conn.execute("""DELETE FROM sis_samples WHERE ssp_pk=?""", (self.tmp_ssp_pk, ))
            log.info("deleted %s pk entries from sis_samples" % self.tmp_ssp_pk)

        except sqlite3.Error as e:
            log.error("during deletion from sis_samples, %s: %s" % (type(e), e))
            return False

        try:
            self.conn.execute("""DELETE FROM ssp WHERE pk=?""", (self.tmp_ssp_pk, ))
            log.info("deleted %s pk entry from ssp" % self.tmp_ssp_pk)

        except sqlite3.Error as e:
            log.error("during deletion from ssp, %s: %s" % (type(e), e))
            return False

        if full:
            try:
                self.conn.execute("""DELETE FROM ssp_pk WHERE id=?""", (self.tmp_ssp_pk, ))
                log.info("deleted %s id entry from ssp_pk" % self.tmp_ssp_pk)

            except sqlite3.Error as e:
                log.error("during deletion from ssp_pk, %s: %s" % (type(e), e))
                return False

        return True

    def _add_ssp(self):

        try:
            self.conn.execute("""
                              INSERT INTO ssp VALUES (?, ?, ?, ?, ?, ?)
                              """, (self.tmp_ssp_pk,
                                    self.tmp_data.survey_name,
                                    self.tmp_data.original_path,
                                    self.tmp_data.sensor_type,
                                    self.tmp_data.source_info,
                                    self.tmp_data.driver))
            log.info("insert new %s pk in ssp" % self.tmp_ssp_pk)

        except sqlite3.Error as e:
            log.error("during ssp addition, %s: %s" % (type(e), e))
            return False

        return True

    def _add_ssp_raw_samples(self):

        sample_size = self.tmp_data.raw_data[Dicts.idx['depth'], :].size
        log.info("max raw samples to add: %s" % sample_size)

        added_samples = 0
        for i in range(sample_size):
            sample_row = self.tmp_data.raw_data[:, i]
            #print(sample_row)

            try:
                # first check if the sample is already present with exactly the same values
                self.conn.execute("""
                                  INSERT INTO raw_samples VALUES (?, ?, ?, ?, ?, ?, ?)
                                  """, (self.tmp_ssp_pk,
                                        sample_row[Dicts.idx['depth']],
                                        sample_row[Dicts.idx['speed']],
                                        sample_row[Dicts.idx['temperature']],
                                        sample_row[Dicts.idx['salinity']],
                                        sample_row[Dicts.idx['source']],
                                        sample_row[Dicts.idx['flag']],
                                        ))
                added_samples += 1
            except sqlite3.IntegrityError as e:
                log.info("skipping row #%s due to %s: %s" % (i, type(e), e))
                continue
            except sqlite3.Error as e:
                log.error("during adding ssp raw samples, %s: %s" % (type(e), e))
                return False

        log.info("added %s raw samples" % added_samples)
        return True

    def _add_ssp_mod_samples(self):

        sample_size = self.tmp_data.data[Dicts.idx['depth'], :].size
        log.info("max processed samples to add: %s" % sample_size)

        added_samples = 0
        for i in range(sample_size):
            sample_row = self.tmp_data.data[:, i]
            #print(sample_row)

            try:
                # first check if the sample is already present with exactly the same values
                self.conn.execute("""
                                  INSERT INTO mod_samples VALUES (?, ?, ?, ?, ?, ?, ?)
                                  """, (self.tmp_ssp_pk,
                                        sample_row[Dicts.idx['depth']],
                                        sample_row[Dicts.idx['speed']],
                                        sample_row[Dicts.idx['temperature']],
                                        sample_row[Dicts.idx['salinity']],
                                        sample_row[Dicts.idx['source']],
                                        sample_row[Dicts.idx['flag']],
                                        ))
                added_samples += 1

            except sqlite3.IntegrityError as e:
                log.info("skipping row #%s due to %s: %s" % (i, type(e), e))
                continue
            except sqlite3.Error as e:
                log.error("during adding ssp processed samples, %s: %s" % (type(e), e))
                return False

        log.info("added %s processed samples" % added_samples)
        return True

    def _add_ssp_sis_samples(self):

        sample_size = self.tmp_data.sis_data[Dicts.idx['depth'], :].size
        log.info("max sis samples to add: %s" % sample_size)

        added_samples = 0
        for i in range(sample_size):
            sample_row = self.tmp_data.sis_data[:, i]
            #print(sample_row)

            try:
                # first check if the sample is already present with exactly the same values
                self.conn.execute("""
                                  INSERT INTO sis_samples VALUES (?, ?, ?, ?, ?, ?, ?)
                                  """, (self.tmp_ssp_pk,
                                        sample_row[Dicts.idx['depth']],
                                        sample_row[Dicts.idx['speed']],
                                        sample_row[Dicts.idx['temperature']],
                                        sample_row[Dicts.idx['salinity']],
                                        sample_row[Dicts.idx['source']],
                                        sample_row[Dicts.idx['flag']],
                                        ))
                added_samples += 1

            except sqlite3.IntegrityError as e:
                log.info("skipping row #%s due to %s: %s" % (i, type(e), e))
                continue

            except sqlite3.Error as e:
                log.error("during adding ssp sis samples, %s: %s" % (type(e), e))
                return False

        log.info("added %s sis samples" % added_samples)
        return True

    def list_all_ssp_pks(self):
        if not self.conn:
            log.error("missing db connection")
            return None

        ssp_list = list()

        try:
            with self.conn:
                for row in self.conn.execute("""SELECT * FROM ssp_view"""):
                    ssp_list.append((row[b'pk'], row[b'cast_datetime'], row[b'cast_position'], row[b'survey_name'],
                                     row[b'sensor_type'],))

            return ssp_list

        except sqlite3.Error as e:
            log.error("%s: %s" % (type(e), e))
            return None

    def list_ssp_pks_by_survey_name(self, survey_name="default"):
        if not self.conn:
            log.error("missing db connection")
            return None

        ssp_list = list()
        log.info("get casts by survey name: %s" % survey_name)

        try:
            with self.conn:
                for row in self.conn.execute("""
                                             SELECT * FROM ssp_view WHERE survey_name=?
                                             """, (survey_name, )):
                    ssp_list.append((row[b'pk'], row[b'cast_datetime'], row[b'cast_position'], row[b'survey_name'],
                                     row[b'sensor_type'],))

        except sqlite3.Error as e:
            log.error("%s: %s" % (type(e), e))
            return None

        return ssp_list

    def get_ssp_by_pk(self, pk):
        if not self.conn:
            log.error("missing db connection")
            return None

        ssp_data = SspData()
        log.info("get ssp by primary key: %s" % pk)

        with self.conn:
            try:
                # ssp spatial timestamp
                ssp_idx = self.conn.execute("""
                                            SELECT * FROM ssp_pk WHERE id=?
                                            """, (pk, )).fetchone()
                ssp_data.date_time = ssp_idx[b'cast_datetime']
                ssp_data.longitude = ssp_idx[b'cast_position'].x
                ssp_data.latitude = ssp_idx[b'cast_position'].y

            except sqlite3.Error as e:
                log.error("reading ssp spatial timestamp for %s pk, %s: %s" % (pk, type(e), e))
                return None

            try:
                # ssp metadata
                ssp_hdr = self.conn.execute("""
                                            SELECT * FROM ssp WHERE pk=?
                                            """, (pk, )).fetchone()
                ssp_data.survey_name = ssp_hdr[b'survey_name']
                ssp_data.original_path = ssp_hdr[b'original_path']
                ssp_data.sensor_type = ssp_hdr[b'sensor_type']
                ssp_data.source_info = ssp_hdr[b'source_info']
                ssp_data.driver = ssp_hdr[b'driver']

            except sqlite3.Error as e:
                log.error("reading ssp metadata for %s pk, %s: %s" % (pk, type(e), e))
                return None

            try:
                # raw data
                ssp_samples = self.conn.execute("""
                                                SELECT * FROM raw_samples WHERE ssp_pk=?
                                                   ORDER BY depth
                                                """, (pk, )).fetchall()
                num_samples = len(ssp_samples)
                print("raw samples: %s" % num_samples)
                depths = np.zeros(num_samples)
                speeds = np.zeros(num_samples)
                temperatures = np.zeros(num_samples)
                salinities = np.zeros(num_samples)
                sources = np.zeros(num_samples)
                flags = np.zeros(num_samples)
                for i in range(num_samples):
                    #print(ssp_samples[i])
                    depths[i] = ssp_samples[i][b'depth']
                    speeds[i] = ssp_samples[i][b'speed']
                    temperatures[i] = ssp_samples[i][b'temperature']
                    salinities[i] = ssp_samples[i][b'salinity']
                    sources[i] = ssp_samples[i][b'source']
                    flags[i] = ssp_samples[i][b'flag']
                ssp_data.set_raw_samples(depth=depths, speed=speeds,
                                         temperature=temperatures, salinity=salinities,
                                         source=sources, flag=flags)
            except sqlite3.Error as e:
                log.error("reading raw samples for %s pk, %s: %s" % (pk, type(e), e))
                return None

            try:
                # processed data
                ssp_samples = self.conn.execute("""
                                                SELECT * FROM mod_samples WHERE ssp_pk=?
                                                   ORDER BY depth
                                                """, (pk, )).fetchall()
                num_samples = len(ssp_samples)
                print("samples: %s" % num_samples)
                depths = np.zeros(num_samples)
                speeds = np.zeros(num_samples)
                temperatures = np.zeros(num_samples)
                salinities = np.zeros(num_samples)
                sources = np.zeros(num_samples)
                flags = np.zeros(num_samples)
                for i in range(num_samples):
                    #print(ssp_samples[i])
                    depths[i] = ssp_samples[i][b'depth']
                    speeds[i] = ssp_samples[i][b'speed']
                    temperatures[i] = ssp_samples[i][b'temperature']
                    salinities[i] = ssp_samples[i][b'salinity']
                    sources[i] = ssp_samples[i][b'source']
                    flags[i] = ssp_samples[i][b'flag']
                ssp_data.set_samples(depth=depths, speed=speeds,
                                     temperature=temperatures, salinity=salinities,
                                     source=sources, flag=flags)
            except sqlite3.Error as e:
                log.error("reading processed samples for %s pk, %s: %s" % (pk, type(e), e))
                return None

            try:
                # sis data
                ssp_samples = self.conn.execute("""
                                                SELECT * FROM sis_samples WHERE ssp_pk=?
                                                   ORDER BY depth
                                                """, (pk, )).fetchall()
                num_samples = len(ssp_samples)
                print("sis samples: %s" % num_samples)
                depths = np.zeros(num_samples)
                speeds = np.zeros(num_samples)
                temperatures = np.zeros(num_samples)
                salinities = np.zeros(num_samples)
                sources = np.zeros(num_samples)
                flags = np.zeros(num_samples)
                for i in range(num_samples):
                    #print(ssp_samples[i])
                    depths[i] = ssp_samples[i][b'depth']
                    speeds[i] = ssp_samples[i][b'speed']
                    temperatures[i] = ssp_samples[i][b'temperature']
                    salinities[i] = ssp_samples[i][b'salinity']
                    sources[i] = ssp_samples[i][b'source']
                    flags[i] = ssp_samples[i][b'flag']
                ssp_data.set_sis_samples(depth=depths, speed=speeds,
                                         temperature=temperatures, salinity=salinities,
                                         source=sources, flag=flags)

            except sqlite3.Error as e:
                log.error("reading sis samples for %s pk, %s: %s" % (pk, type(e), e))
                return None

        return ssp_data

    def _get_all_ssp_view_rows(self):
        if not self.conn:
            log.error("missing db connection")
            return None

        with self.conn:
            try:
                # ssp spatial timestamp
                ssp_view = self.conn.execute("""
                                             SELECT * FROM ssp_view
                                             """).fetchall()
                log.info("retrieved %s rows from ssp view" % len(ssp_view))
                return ssp_view

            except sqlite3.Error as e:
                log.error("retrieving all ssp view rows, %s: %s" % (type(e), e))
                return None

    def _create_ogr_lyr_and_fields(self, ds):
        # create the only data layer
        lyr = ds.CreateLayer(b'ssp', None, ogr.wkbPoint)
        if lyr is None:
            log.error("Layer creation failed")
            return

        field_pk = ogr.FieldDefn(b'pk', ogr.OFTInteger)
        if lyr.CreateField(field_pk) != 0:
            raise DbError("Creating field failed.")

        field_datetime = ogr.FieldDefn(b'datetime', ogr.OFTString)
        if lyr.CreateField(field_datetime) != 0:
            raise DbError("Creating field failed.")

        field_survey = ogr.FieldDefn(b'survey', ogr.OFTString)
        field_survey.SetWidth(254)
        if lyr.CreateField(field_survey) != 0:
            raise DbError("Creating field failed.")

        field_org_path = ogr.FieldDefn(b'org_path', ogr.OFTString)
        field_org_path.SetWidth(254)
        if lyr.CreateField(field_org_path) != 0:
            raise DbError("Creating field failed.")

        field_type = ogr.FieldDefn(b'type', ogr.OFTString)
        field_type.SetWidth(254)
        if lyr.CreateField(field_type) != 0:
            raise DbError("Creating field failed.")

        field_source = ogr.FieldDefn(b'source', ogr.OFTString)
        field_source.SetWidth(254)
        if lyr.CreateField (field_source) != 0:
            raise DbError("Creating field failed.")

        field_driver = ogr.FieldDefn(b'driver', ogr.OFTString)
        field_driver.SetWidth(254)
        if lyr.CreateField(field_driver) != 0:
            raise DbError("Creating field failed.")

        return lyr

    def convert_ssp_view_to_ogr(self, ogr_format=GdalAux.ogr_formats[b'ESRI Shapefile']):

        GdalAux()

        # create the data source
        try:
            ds = GdalAux.create_ogr_data_source(ogr_format, self.export_ssp_view_path)
            lyr = self._create_ogr_lyr_and_fields(ds)

        except HyOError as e:
            log.error("%s" % e)
            return

        view_rows = self._get_all_ssp_view_rows()
        if view_rows is None:
            raise DbError("Unable to retrieve ssp view rows")

        for vr in view_rows:

            feat = ogr.Feature(lyr.GetLayerDefn())

            feat.SetField(b'pk', vr[b'pk'])
            feat.SetField(b'datetime', vr[b'cast_datetime'].isoformat())
            feat.SetField(b'source', vr[b'source_info'].split("/")[0].encode())
            feat.SetField(b'org_path', vr[b'original_path'].encode())
            feat.SetField(b'type', Dicts.first_match(Dicts.sensor_types, int(vr[b'sensor_type'])).encode())
            feat.SetField(b'driver', vr[b'driver'].encode())

            pt = ogr.Geometry(ogr.wkbPoint)
            pt.SetPoint_2D(0, vr[b'cast_position'].x, vr[b'cast_position'].y)

            feat.SetGeometry(pt)
            if lyr.CreateFeature(feat) != 0:
                raise DbError("Unable to create feature")
            feat.Destroy()

        ds = None
        return True

    def get_printable_ssp_view(self):

        view_rows = self._get_all_ssp_view_rows()
        if view_rows is None:
            raise DbError("Unable to retrieve ssp view rows")

        output = "%5s%22s%12s%12s%12s%8s\n" % ("id", "time stamp", "longitude", "latitude", "sensor", "type")

        for vr in view_rows:
            output += "%5s%22s%12.6f%12.6f%12s%8s\n" \
                      % (vr[b'pk'], vr[b'cast_datetime'],
                         vr[b'cast_position'].x, vr[b'cast_position'].y,
                         vr[b'source_info'].split("/")[0],
                         Dicts.first_match(Dicts.sensor_types, int(vr[b'sensor_type'])))

        return output

    @staticmethod
    def _world_draw_map():
        m = Basemap(resolution=None)
        # resolution c, l, i, h, f in that order
        m.bluemarble(zorder=0)
        return m

    @staticmethod
    def _set_inset_color(x, color):
        for m in x:
            for t in x[m][1]:
                t.set_color(color)

    @staticmethod
    def _inset_draw_map(llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat, ax_ins):

        m = Basemap(llcrnrlon=llcrnrlon, llcrnrlat=llcrnrlat, urcrnrlon=urcrnrlon, urcrnrlat=urcrnrlat,
                    resolution='i', ax=ax_ins)
        # resolution c, l, i, h, f in that order

        m.drawmapboundary(fill_color='aqua', zorder=2)
        m.fillcontinents(color='coral', lake_color='aqua', zorder=1)

        m.drawcoastlines(color='0.6', linewidth=0.5)
        m.drawcountries(color='0.6', linewidth=0.5)

        par = m.drawparallels(np.arange(-90., 91., 5.), labels=[1, 0, 0, 1], dashes=[1, 1], linewidth=0.4, color='.2')
        SspDb._set_inset_color(par, 'y')
        mer = m.drawmeridians(np.arange(0., 360., 5.), labels=[1, 0, 0, 1], dashes=[1, 1], linewidth=0.4, color='.2')
        SspDb._set_inset_color(mer, 'y')

        return m

    def map_ssp_view(self):
        """plot all the ssp in the database"""

        view_rows = self._get_all_ssp_view_rows()
        if view_rows is None:
            raise DbError("Unable to retrieve ssp view rows > Empty database?")
        if len(view_rows) == 0:
            raise DbError("Unable to retrieve ssp view rows > Empty database?")

        # prepare the data
        ssp_x = list()
        ssp_y = list()
        ssp_label = list()
        for vr in view_rows:
            ssp_x.append(vr[b'cast_position'].x)
            ssp_y.append(vr[b'cast_position'].y)
            ssp_label.append(vr[b'pk'])
        ssp_x_min = min(ssp_x)
        ssp_x_max = max(ssp_x)
        ssp_x_mean = (ssp_x_min + ssp_x_max) / 2
        ssp_x_delta = max(0.05, abs(ssp_x_max - ssp_x_min)/5)
        ssp_y_min = min(ssp_y)
        ssp_y_max = max(ssp_y)
        ssp_y_mean = (ssp_y_min + ssp_y_max) / 2
        ssp_y_delta = max(0.05, abs(ssp_y_max - ssp_y_min)/5)
        log.info("data boundary: %.4f, %.4f (%.4f) / %.4f, %.4f (%.4f)"
                        % (ssp_x_min, ssp_x_max, ssp_x_delta, ssp_y_min, ssp_y_max, ssp_y_delta))

        # make the world map
        fig = plt.figure()
        #plt.title("SSP Map (%s profiles)" % len(view_rows))
        ax = fig.add_subplot(111)
        plt.ioff()

        wm = self._world_draw_map()
        # x, y = wm(ssp_x_mean, ssp_y_mean)
        # wm.scatter(x, y, s=18, color='y')

        if ssp_x_mean > 0:
            ssp_loc = 2
        else:
            ssp_loc = 1
        ax_ins = zoomed_inset_axes(ax, 15, loc=ssp_loc)
        ax_ins.set_xlim((ssp_x_min - ssp_x_delta), (ssp_x_max + ssp_x_delta))
        ax_ins.set_ylim((ssp_y_min - ssp_y_delta), (ssp_y_max + ssp_y_delta))

        m = self._inset_draw_map(llcrnrlon=(ssp_x_min - ssp_x_delta), llcrnrlat=(ssp_y_min - ssp_y_delta),
                                 urcrnrlon=(ssp_x_max + ssp_x_delta), urcrnrlat=(ssp_y_max + ssp_y_delta),
                                 ax_ins=ax_ins)

        x, y = m(ssp_x, ssp_y)
        m.scatter(x, y, marker='o', s=16, color='r')
        m.scatter(x, y, marker='.', s=1, color='k')

        if ssp_x_mean > 0:
            mark_inset(ax, ax_ins, loc1=1, loc2=4, fc="none", ec='y')
        else:
            mark_inset(ax, ax_ins, loc1=2, loc2=3, fc="none", ec='y')

        ax_ins.tick_params(color='y', labelcolor='y')
        for spine in ax_ins.spines.values():
            spine.set_edgecolor('y')

        #fig.tight_layout()
        plt.show()

    def _get_timestamp_list(self):
        """Create and return the timestamp list (and the pk)"""

        if not self.conn:
            log.error("missing db connection")
            return None

        with self.conn:
            try:
                # ssp spatial timestamp
                ts_list = self.conn.execute("""
                                             SELECT cast_datetime, pk FROM ssp_view ORDER BY cast_datetime
                                             """).fetchall()
                log.info("retrieved %s timestamps from ssp view" % len(ts_list))
                return ts_list

            except sqlite3.Error as e:
                log.error("retrieving the time stamp list, %s: %s" % (type(e), e))
                return None

    def get_cleaned_raw_ssp_by_pk(self, pk):
        if not self.conn:
            log.error("missing db connection")
            return None

        ssp_data = SspData()
        log.info("get cleaned raw ssp by primary key: %s" % pk)

        with self.conn:
            try:
                # ssp spatial timestamp
                ssp_idx = self.conn.execute("""
                                            SELECT * FROM ssp_pk WHERE id=?
                                            """, (pk, )).fetchone()
                ssp_data.date_time = ssp_idx[b'cast_datetime']
                ssp_data.longitude = ssp_idx[b'cast_position'].x
                ssp_data.latitude = ssp_idx[b'cast_position'].y

            except sqlite3.Error as e:
                log.error("reading ssp spatial timestamp for %s pk, %s: %s" % (pk, type(e), e))
                return None

            try:
                # ssp metadata
                ssp_hdr = self.conn.execute("""
                                            SELECT * FROM ssp WHERE pk=?
                                            """, (pk, )).fetchone()
                ssp_data.survey_name = ssp_hdr[b'survey_name']
                ssp_data.original_path = ssp_hdr[b'original_path']
                ssp_data.sensor_type = ssp_hdr[b'sensor_type']
                ssp_data.source_info = ssp_hdr[b'source_info']
                ssp_data.driver = ssp_hdr[b'driver']

            except sqlite3.Error as e:
                log.error("reading ssp metadata for %s pk, %s: %s" % (pk, type(e), e))
                return None

            try:
                # processed data
                ssp_samples = self.conn.execute("""
                                                SELECT * FROM mod_samples WHERE ssp_pk=? AND source=0 AND flag=0
                                                   ORDER BY depth
                                                """, (pk, )).fetchall()
                num_samples = len(ssp_samples)
                print("samples: %s" % num_samples)
                depths = np.zeros(num_samples)
                speeds = np.zeros(num_samples)
                temperatures = np.zeros(num_samples)
                salinities = np.zeros(num_samples)
                sources = np.zeros(num_samples)
                flags = np.zeros(num_samples)
                for i in range(num_samples):
                    #print(ssp_samples[i])
                    depths[i] = ssp_samples[i][b'depth']
                    speeds[i] = ssp_samples[i][b'speed']
                    temperatures[i] = ssp_samples[i][b'temperature']
                    salinities[i] = ssp_samples[i][b'salinity']
                    sources[i] = ssp_samples[i][b'source']
                    flags[i] = ssp_samples[i][b'flag']
                ssp_data.set_samples(depth=depths, speed=speeds,
                                     temperature=temperatures, salinity=salinities,
                                     source=sources, flag=flags)
            except sqlite3.Error as e:
                log.error("reading cleaned raw samples for %s pk, %s: %s" % (pk, type(e), e))
                return None

        return ssp_data

    def create_daily_plots(self, save_fig=False):
        """plot all the SSPs by day"""

        ts_list = self._get_timestamp_list()
        if ts_list is None:
            raise DbError("Unable to retrieve the day list > Empty database?")
        if len(ts_list) == 0:
            raise DbError("Unable to retrieve the day list > Empty database?")

        day_count = 0
        ssp_count = 0
        current_date = None
        fig = None
        for ts_pk in ts_list:

            ssp_count += 1
            tmp_date = ts_pk[0].date()

            if (current_date is None) or (tmp_date > current_date):
                # end the previous figure
                if fig is not None:
                    plt.title("Day #%s: %s (profiles: %s)" % (day_count, current_date, ssp_count))
                    ax.set_xlim(1460, 1580)
                    ax.set_ylim(780, 0)
                    plt.xlabel('Sound Speed [m/s]', fontsize=10)
                    plt.ylabel('Depth [m]', fontsize=10)
                    plt.grid()
                    # Now add the legend with some customizations.
                    legend = ax.legend(loc='lower right', shadow=True)
                    # The frame is matplotlib.patches.Rectangle instance surrounding the legend.
                    frame = legend.get_frame()
                    frame.set_facecolor('0.90')

                    # Set the fontsize
                    for label in legend.get_texts():
                        label.set_fontsize('large')

                    for label in legend.get_lines():
                        label.set_linewidth(1.5)  # the legend line width

                    if save_fig:
                        plt.savefig(os.path.join(self.plots_folder, 'day_%s.png' % day_count), bbox_inches='tight')
                    else:
                        plt.show()
                    ssp_count = 0

                # start a new figure
                fig = plt.figure(day_count)
                ax = fig.add_subplot(111)
                ax.invert_yaxis()
                current_date = tmp_date
                log.info("day: %s" % day_count)
                day_count += 1

            tmp_ssp = self.get_cleaned_raw_ssp_by_pk(ts_pk[1])
            print(tmp_ssp)
            ax.plot(tmp_ssp.data[Dicts.idx['speed'], :],
                    tmp_ssp.data[Dicts.idx['depth'], :],
                    label='%s [%04d] ' % (ts_pk[0].time(), ts_pk[1]))
            ax.hold(True)

            # print(ts_pk[1], ts_pk[0])

        # last figure
        ssp_count += 1
        plt.title("Day #%s: %s (profiles: %s)" % (day_count, current_date, ssp_count))
        ax.set_xlim(1460, 1580)
        ax.set_ylim(780, 0)
        plt.xlabel('Sound Speed [m/s]', fontsize=10)
        plt.ylabel('Depth [m]', fontsize=10)
        plt.grid()
        # Now add the legend with some customizations.
        legend = ax.legend(loc='lower right', shadow=True)
        # The frame is matplotlib.patches.Rectangle instance surrounding the legend.
        frame = legend.get_frame()
        frame.set_facecolor('0.90')

        # Set the fontsize
        for label in legend.get_texts():
            label.set_fontsize('large')

        for label in legend.get_lines():
            label.set_linewidth(1.5)  # the legend line width

        if save_fig:
            plt.savefig(os.path.join(self.plots_folder, 'day_%s.png' % day_count), bbox_inches='tight')
        else:
            plt.show()

    def delete_ssp_by_pk(self, pk):
        """Delete all the entries related to a SSP primary key"""
        self.tmp_ssp_pk = pk

        with self.conn:
            if not self._delete_old_ssp(full=True):
                raise SspError("unable to delete ssp with pk: %s" % pk)

        self.tmp_ssp_pk = None
