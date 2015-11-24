from __future__ import absolute_import, division, print_function, unicode_literals

import datetime as dt
import numpy as np
import netCDF4
import logging

log = logging.getLogger(__name__)

from .base_atlas import Atlas, AtlasError
from .. import oceanography
from ..ssp import SspData
from ..ssp_dicts import Dicts
from .. import __version__


class RTOFS(Atlas):
    """RTOFS class to deal with RTOFS queries"""

    def __init__(self):
        super(RTOFS, self).__init__()
        self.name = "RTO"
        self.source_info = "Global Real-Time Ocean Forecast System"

        # For a given queried date, we need to use the forecast from the previous
        # day since the current nowcast doesn't hold data for today (this problem
        # has been acknowledged and is being worked on). -- JDB, 20111201
        self.use_yesterday_grids = True
        if self.use_yesterday_grids:
            log.info("init > forcing the use of yesterday grids")

        # Going to keep track of whether or not grids are "loaded" (netCDF files are opened)
        self.grids_loaded = False
        # Some silly day in the past to start
        self.last_day_loaded = dt.datetime(1900, 1, 1, 0, 0, 0).strftime("%Y%m%d")

        # How far are we willing to look for solutions?
        # This is the size of the search box in number of grid nodes
        self.search_window = 5
        self.search_half_window = self.search_window // 2

        # 2000 dbar is the reference depth associated with the potential temperatures in the grid (sigma-2)
        self.reference_pressure = 2000

        self.depths = None
        self.latitudes = None
        self.longitudes = None
        self.num_levels = None
        self.lat_step = None
        self.lat_1 = None
        self.lon_step = None
        self.lon_1 = None

    @staticmethod
    def _build_urls(input_date, use_backup=False):
        """make up the url to use for salinity and temperature (using or not the backup servers)"""
        input_date_str = input_date.strftime("%Y%m%d")

        if not use_backup:
            # Primary server
            # http://nomads.ncep.noaa.gov:9090/dods/rtofs
            url_temp = 'http://nomads.ncep.noaa.gov:9090/dods/rtofs/rtofs_global%s/rtofs_glo_3dz_nowcast_daily_temp' \
                       % input_date_str
            url_sal = 'http://nomads.ncep.noaa.gov:9090/dods/rtofs/rtofs_global%s/rtofs_glo_3dz_nowcast_daily_salt' \
                      % input_date_str
        else:
            # Backup server
            # http://nomad3.ncep.noaa.gov:9090/dods/rtofs_global/
            url_temp = 'http://nomad3.ncep.noaa.gov:9090/dods/rtofs_global/rtofs.%s/rtofs_glo_3dz_nowcast_daily_temp' \
                       % input_date_str
            url_sal = 'http://nomad3.ncep.noaa.gov:9090/dods/rtofs_global/rtofs.%s/rtofs_glo_3dz_nowcast_daily_salt' \
                      % input_date_str
        return url_temp, url_sal

    def _close_files(self):
        if self.grids_loaded:
            self.file_temp.clean_project()
            self.file_salinity.clean_project()
        self.grids_loaded = False
        self.last_day_loaded = dt.datetime(1900, 1, 1, 0, 0, 0).strftime("%Y%m%d")

    def _open_files(self, input_date):
        # log.info("opening")

        if self.grids_loaded:
            if self.last_day_loaded == input_date.strftime("%Y%m%d"):
                log.info("open grids already loaded for %s" % input_date)
                return
        else:
            log.info("open last day loaded %s, but queried %s " % (self.last_day_loaded, input_date))
            self._close_files()

        if self.use_yesterday_grids:
            try:
                yesterday = input_date - dt.timedelta(days=1)
                url_temp, url_sal = self._build_urls(yesterday)
                log.info("open url -> %s" % url_temp)
                log.info("open url -> %s" % url_sal)
                file_temp = netCDF4.Dataset(url_temp)
                file_salinity = netCDF4.Dataset(url_sal)
                day_index = 1
            except RuntimeError:
                raise AtlasError("unable to access data")
        else:
            log.info("open using standard UNTESTED operational mode (today is today!)")
            # This is the way it SHOULD be done, but the 0'th time slice is always missing data
            # (this is a problem acknowledged by the RTOFS folks).  Until it is resolved,
            # we have no choice but to access "yesterday's" nowcast and to take the
            # 1'th time slice, which is effectively a short range forecast for today.
            try:
                url_temp, url_salinity = self._build_urls(input_date)
                log.info("open url: %s" % url_temp)
                log.info("open url: %s" % url_salinity)
                # Try out today's grids
                file_temp = netCDF4.Dataset(url_temp)
                file_salinity = netCDF4.Dataset(url_salinity)
                day_index = 0
            except RuntimeError:
                # If today's grids don't exist, then try yesterdays (today's grids don't get uploaded until ~6AM UTC)
                yesterday = input_date - dt.timedelta(days=1)
                url_temp, url_salinity = self._build_urls(yesterday)
                log.info("open grids unavailable > trying %s" % yesterday)
                log.info("open url: %s" % url_temp)
                log.info("open url: %s" % url_salinity)

                try:
                    file_temp = netCDF4.Dataset(url_temp)
                    file_salinity = netCDF4.Dataset(url_salinity)
                    day_index = 1
                except RuntimeError:
                    raise AtlasError("unable to access data")

        self.grids_loaded = True
        self.last_day_loaded = input_date.strftime("%Y%m%d")
        self.file_temp = file_temp
        self.file_salinity = file_salinity
        self.day_index = day_index

    def load_grids(self, input_date):
        """ used to load lat/long/depth """

        # log.info("loading")

        try:
            self._open_files(input_date)
        except:
            raise AtlasError("troubles in RTOFS URL access for date %s" % input_date)

        try:
            # Now get latitudes, longitudes and depths for x,y,z referencing
            # log.info("load depth")
            self.depths = self.file_temp.variables['lev'][:]
            # log.info("load latitude")
            self.latitudes = self.file_temp.variables['lat'][:]
            # log.info("load longitude")
            self.longitudes = self.file_temp.variables['lon'][:]
        except:
            raise AtlasError("troubles in variable lookup for lat/long grid and/or depth")

        # How many depth levels do we have?
        self.num_levels = self.depths.size

        self.lat_step = self.latitudes[1] - self.latitudes[0]
        self.lat_1 = self.latitudes[0]
        self.lon_step = self.longitudes[1] - self.longitudes[0]
        self.lon_1 = self.longitudes[0]

        log.info("load (lat1, lon1): (%s, %s); steps: %s, %s"
                 % (self.lat_1, self.lon_1, self.lat_step, self.lon_step))

    def grid_coords(self, latitude, longitude):
        # make longitude "safe" since RTOFS grid starts at east longitude 70-ish degrees
        while longitude < self.lon_1:
            longitude += 360.0

        # This does a nearest neighbour lookup
        lat_index = int(round((latitude - self.lat_1) / self.lat_step, 0))
        lon_index = int(round((longitude - self.lon_1) / self.lon_step, 0))

        return lat_index, lon_index

    def query(self, latitude, longitude, date_time):

        log.info("query: %s @ (%.6f, %.6f)" % (date_time, longitude, latitude))

        if (latitude is None) or (longitude is None) or (date_time is None):
            return None, None, None

        # Try to open files
        try:
            self._open_files(date_time)
        except AtlasError as e:
            raise AtlasError("troubles in URL access for %s: %s" % (date_time, e))

        # Make all longitudes safe
        while longitude < self.lon_1:
            longitude += 360.0
            log.info("query: adjusting longitude to %s" % longitude)

        latitudes = np.zeros((self.search_window, self.search_window))
        longitudes = np.zeros((self.search_window, self.search_window))
        distances = np.zeros((self.file_temp.variables['lev'].size, self.search_window, self.search_window))
        temperatures_potential = np.zeros(self.num_levels)
        temperatures_in_situ = np.zeros(self.num_levels)
        depths = np.zeros(self.num_levels)
        salinities = np.zeros(self.num_levels)

        lat_index, lon_index = self.grid_coords(latitude, longitude)
        num_lons = self.file_temp.variables['temperature'].shape[3]
        # num_lats = self.file_temp.variables['temperature'].shape[2]

        lat_s_idx = lat_index - self.search_half_window
        lat_n_idx = lat_index + self.search_half_window

        lats = self.latitudes[lat_s_idx:lat_n_idx + 1]

        for i in range(self.search_window):
            latitudes[:, i] = lats

        lon_w_idx = lon_index - self.search_half_window
        lon_e_idx = lon_index + self.search_half_window

        if (lon_e_idx < num_lons) and (lon_w_idx >= 0):
            log.info("safe case")
            log.info("using indices -> %s %s %s %s"
                     % (lat_s_idx, lat_n_idx, lon_w_idx, lon_e_idx))

            # Need +1 on the north and east indices since it is the "stop" value in these slices
            t = self.file_temp.variables['temperature'][1, :, lat_s_idx:lat_n_idx + 1, lon_w_idx:lon_e_idx + 1]
            s = self.file_salinity.variables['salinity'][1, :, lat_s_idx:lat_n_idx + 1, lon_w_idx:lon_e_idx + 1]

            # Set 'unfilled' elements to NANs (BUT when the entire array has valid data, it returns numpy.ndarray)
            if isinstance(t, np.ma.core.MaskedArray):
                t_mask = t.mask
                t[t_mask] = np.nan
            if isinstance(s, np.ma.core.MaskedArray):
                s_mask = s.mask
                s[s_mask] = np.nan

            lons = self.longitudes[lon_w_idx:lon_e_idx + 1]

            for i in range(self.search_window):
                longitudes[i, :] = lons
        else:
            log.info("split case")

            # Do the left portion of the array first, this will run into the wrap
            # longitude so limit it accordingly
            lon_e_idx = num_lons - 1

            # lon_west_index can be negative if lon_index is on the westernmost end of the array
            while lon_w_idx < 0:
                lon_w_idx = lon_w_idx + num_lons

            log.info("using lon west/east indices -> %s %s"
                     % (lon_w_idx, lon_e_idx))

            # Need +1 on the north and east indices since it is the "stop" value in these slices
            t_left = self.file_temp.variables['temperature'][1, :, lat_s_idx:lat_n_idx + 1, lon_w_idx:lon_e_idx + 1]
            s_left = self.file_salinity.variables['salinity'][1, :, lat_s_idx:lat_n_idx + 1, lon_w_idx:lon_e_idx + 1]

            # Set 'unfilled' elements to NANs (BUT when the entire array has valid data, it returns numpy.ndarray)
            if isinstance(t_left, np.ma.core.MaskedArray):
                t_mask = t_left.mask
                t_left[t_mask] = np.nan
            if isinstance(s_left, np.ma.core.MaskedArray):
                s_mask = s_left.mask
                s_left[s_mask] = np.nan

            lons_left = self.longitudes[lon_w_idx:lon_e_idx + 1]

            for i in range(self.search_window):
                longitudes[i, 0:lons_left.size] = lons_left

            log.info("longitudes are now: %s" % longitudes)

            # Do the right portion of the array first, this will run into the wrap
            # longitude so limit it accordingly
            lon_w_idx = 0

            lon_e_idx = self.search_window - lons_left.size - 1

            # Need +1 on the north and east indices since it is the "stop" value in these slices
            t_right = self.file_temp.variables['temperature'][1, :, lat_s_idx:lat_n_idx + 1, lon_w_idx:lon_e_idx + 1]
            s_right = self.file_salinity.variables['salinity'][1, :, lat_s_idx:lat_n_idx + 1, lon_w_idx:lon_e_idx + 1]

            # Set 'unfilled' elements to NANs (BUT when the entire array has valid data, it returns numpy.ndarray)
            if isinstance(t_right, np.ma.core.MaskedArray):
                t_mask = t_right.mask
                t_right[t_mask] = np.nan
            if isinstance(s_right, np.ma.core.MaskedArray):
                s_mask = s_right.mask
                s_right[s_mask] = np.nan

            lons_right = self.longitudes[lon_w_idx:lon_e_idx + 1]

            for i in range(self.search_window):
                longitudes[i, lons_left.size:self.search_window] = lons_right

            t = np.zeros((self.file_temp.variables['lev'].size, self.search_window, self.search_window))
            t[:, :, 0:lons_left.size] = t_left
            t[:, :, lons_left.size:self.search_window] = t_right
            s = np.zeros((self.file_temp.variables['lev'].size, self.search_window, self.search_window))
            s[:, :, 0:lons_left.size] = s_left
            s[:, :, lons_left.size:self.search_window] = s_right

        log.info("done data retrieval > calculating nodes distance")

        # Calculate distances from requested position to each of the grid node locations
        for i in range(self.search_window):
            for j in range(self.search_window):
                dist = self.g.distance(longitudes[i, j], latitudes[i, j], longitude, latitude)
                distances[:, i, j] = dist
        #         log.info("node %s, pos: %3.1f, %3.1f, dist: %3.1f"
        #                         % (i, latitudes[i, j], longitudes[i, j], distances[0, i, j]))
        # log.info("distance array:\n%s" % distances[0])

        # Get mask of "no data" elements and replace these with NaNs
        # in distance array
        t_mask = np.isnan(t)
        distances[t_mask] = np.nan
        s_mask = np.isnan(s)
        distances[s_mask] = np.nan

        log.info("reference pressure: %s dbar" % self.reference_pressure)
        log.info("doing depth levels: %s" % range(t.shape[0]))

        # Spin through all the depth levels
        num_values = 0
        for i in range(t.shape[0]):
            t_level = t[i]
            s_level = s[i]
            d_level = distances[i]

            try:
                ind = np.nanargmin(d_level)
            except ValueError:
                log.info("%s: all-NaN slices" % i)
                continue

            if np.isnan(ind):
                log.info("%s: bottom of valid data" % i)
                break

            ind2 = np.unravel_index(ind, t_level.shape)

            t_closest = t_level[ind2]
            s_closest = s_level[ind2]
            d_closest = d_level[ind2]

            temperatures_potential[i] = t_closest
            salinities[i] = s_closest
            depths[i] = self.depths[i]

            # Calculate in-situ temperature
            pressure = oceanography.depth2press(depths[i], latitude)
            temperatures_in_situ[i] = oceanography.insitu_temperature(t_closest, salinities[i], pressure,
                                                                      self.reference_pressure)

            log.info("%02d: %6.1f %6.1f > T/S/Dist: %3.1f %3.1f %3.1f [pot.temp. %3.1f]"
                     % (i, depths[i], pressure, temperatures_in_situ[i], s_closest, d_closest, t_closest))

            num_values += 1

        if num_values == 0:
            log.info("no data from lookup!")
            return None

        ind = np.nanargmin(distances[0])
        ind2 = np.unravel_index(ind, distances[0].shape)

        lat_out = latitudes[ind2]
        lon_out = longitudes[ind2]

        while lon_out > 180.0:
            lon_out -= 360.0

        # Make a new SV object to return our query in
        ssp_data = SspData()
        ssp_data.set_position(lat_out, lon_out)
        ssp_data.set_time(date_time)
        speed = np.zeros(num_values)
        source = np.zeros(num_values)
        flag = np.zeros(num_values)
        # Add data to sv
        ssp_data.set_samples(depth=depths[0:num_values], speed=speed,
                             temperature=temperatures_in_situ[0:num_values], salinity=salinities[0:num_values],
                             source=source, flag=flag)
        ssp_data.calc_speed()

        # set metadata
        ssp_data.sensor_type = Dicts.sensor_types['Synthetic']
        ssp_data.source_info = self.source_info
        ssp_data.driver = self.name + "." + __version__

        return ssp_data

    def close(self):
        self._close_files()
