from __future__ import absolute_import, division, print_function, unicode_literals

import math
import numpy as np
import netCDF4
import logging

log = logging.getLogger(__name__)

from .base_atlas import Atlas, AtlasError
from ..ssp import SspData
from ..ssp_dicts import Dicts
from .. import __version__


class Woa09(Atlas):
    """WOA class that deals with WOA queries"""

    def __init__(self):
        super(Woa09, self).__init__()

        self.name = "W09"
        self.source_info = "World Ocean Atlas 2009"

        self.woa_path = ""

        self.temperature_annual = None
        self.temperature_monthly = None
        self.temperature_seasonal = None

        self.salinity_annual = None
        self.salinity_monthly = None
        self.salinity_seasonal = None

        self.landsea = None
        self.basin = None

        self.lat_step = None
        self.lat_1 = None
        self.lon_step = None
        self.lon_1 = None

        self.num_levels = None

        # How far are we willing to look for solutions? This is the size of the search box in grid nodes
        self.woa_search_window = 3  # > unused??

        self.month_index = 0
        self.season_index = 0

    def load_grids(self, path):
        self.woa_path = path

        try:
            self.temperature_annual = netCDF4.Dataset(self.woa_path + "/temperature_annual_1deg.nc")
            self.temperature_monthly = netCDF4.Dataset(self.woa_path + "/temperature_monthly_1deg.nc")
            self.temperature_seasonal = netCDF4.Dataset(self.woa_path + "/temperature_seasonal_1deg.nc")
            self.salinity_annual = netCDF4.Dataset(self.woa_path + "/salinity_annual_1deg.nc")
            self.salinity_monthly = netCDF4.Dataset(self.woa_path + "/salinity_monthly_1deg.nc")
            self.salinity_seasonal = netCDF4.Dataset(self.woa_path + "/salinity_seasonal_1deg.nc")
            self.landsea = np.genfromtxt(self.woa_path + "/landsea.msk").reshape((180, 360))
            self.basin = np.genfromtxt(self.woa_path + "/basin.msk").reshape((33, 180, 360))
        except:
            raise AtlasError("issue in reading the netCDF data")

        # What's our grid interval in lat/long
        self.lat_step = self.temperature_monthly.variables['lat'][1] - self.temperature_monthly.variables['lat'][0]
        self.lat_1 = self.temperature_monthly.variables['lat'][0]
        self.lon_step = self.temperature_monthly.variables['lon'][1] - self.temperature_monthly.variables['lon'][0]
        self.lon_1 = self.temperature_monthly.variables['lon'][0]

        # How many depth levels do we have?
        self.num_levels = len(self.temperature_seasonal.variables['depth'])

    def grid_coords(self, latitude, longitude):
        # This does a nearest neighbour lookup 
        lat_index = int(round((latitude - self.lat_1) / self.lat_step, 0))
        lon_index = int(round((longitude - self.lon_1) / self.lon_step, 0))
        return lat_index, lon_index

    def get_depth(self, latitude, longitude):
        lat_index, lon_index = self.grid_coords(latitude, longitude)
        t_profile = self.temperature_annual.variables['t_an'][0, :, lat_index, lon_index]

        # There is a more pythonic way to do this now but my internet connection is too slow
        # to help me google my way to such a solution.
        index = 0
        for sample in range(len(t_profile)):
            if t_profile[sample] != 9.96921E36:
                index = sample

        depth = self.temperature_annual.variables['depth'][index]

        return depth

    def query(self, latitude, longitude, date_time):
        log.info("query: %s @ (%.6f, %.6f)" % (date_time, longitude, latitude))

        if (latitude is None) or (longitude is None) or (date_time is None):
            return None, None, None

        # Make ssp objects to be returned
        ssp_data = SspData()
        ssp_min = SspData()
        ssp_max = SspData()

        # Make all longitudes positive
        if longitude < 0:
            longitude += 360.0

        jday = int(date_time.strftime("%j"))

        # figure out which month based on jday
        min_value = 367
        i = 0
        for d in self.temperature_monthly.variables['time'][:]:
            if math.fabs(d - jday) < min_value:
                min_value = math.fabs(d - jday)
                self.month_index = int(i)
            i += 1

        # figure out which season based on jday
        min_value = 367
        i = 0
        for d in self.temperature_seasonal.variables['time'][:]:
            if math.fabs(d - jday) < min_value:
                min_value = math.fabs(d - jday)
                self.season_index = int(i)
            i += 1

        # Find the nearest grid node
        lat_base_index, lon_base_index = self.grid_coords(latitude, longitude)
        lat_offsets = range(lat_base_index - 1, lat_base_index + 2)
        lon_offsets = range(lon_base_index - 1, lon_base_index + 2)

        # These keep track of the closest node found, this will also
        # be used to populate lat/lon of the cast to be delivered
        lat_index = -1
        lon_index = -1

        # Search all grid nodes surrounding the requested position
        # to find the closest non-land grid node
        temperatures = np.zeros(self.num_levels)
        salinities = np.zeros(self.num_levels)
        temperatures_min = np.zeros(self.num_levels)
        salinities_min = np.zeros(self.num_levels)
        temperatures_max = np.zeros(self.num_levels)
        salinities_max = np.zeros(self.num_levels)

        distances = np.zeros(self.num_levels)
        distances_t_sd = np.zeros(self.num_levels)
        distances_s_sd = np.zeros(self.num_levels)
        distances[:] = 99999999
        distances_t_sd[:] = 99999999
        distances_s_sd[:] = 99999999
        min_dist = 999999999
        num_visited = 0
        for lat_offset in lat_offsets:
            for lon_offset in lon_offsets:

                this_lat_index = lat_offset
                this_lon_index = lon_offset

                if this_lon_index >= self.temperature_monthly.variables['lon'].size:
                    this_lon_index = this_lon_index - self.temperature_monthly.variables['lon'].size

                # Check to see if we're at sea or on land
                if self.landsea[this_lat_index][this_lon_index] == 1:
                    continue

                # calculate the distance to the grid node
                # print(longitude, latitude, self.temperature_monthly.variables['lon'][this_lon_index],
                #       self.temperature_monthly.variables['lat'][this_lat_index])
                dist = self.g.distance(longitude, latitude,
                                       self.temperature_monthly.variables['lon'][this_lon_index],
                                       self.temperature_monthly.variables['lat'][this_lat_index])

                # Keep track of the closest valid grid node
                # as this will provide the reported position of this
                # pseudo-cast
                if dist < min_dist:
                    min_dist = dist
                    lat_index = this_lat_index
                    lon_index = this_lon_index

                # Extract monthly temperature and salinity profile for this location
                t_profile = self.temperature_monthly.variables['t_an'][self.month_index, :,
                                                                       this_lat_index, this_lon_index]
                s_profile = self.salinity_monthly.variables['s_an'][self.month_index, :, this_lat_index, this_lon_index]

                # Extract seasonal temperature and salinity profile for this location
                t_profile2 = self.temperature_seasonal.variables['t_an'][self.season_index, :,
                                                                         this_lat_index, this_lon_index]
                s_profile2 = self.salinity_seasonal.variables['s_an'][self.season_index, :,
                                                                      this_lat_index, this_lon_index]

                # Now do the same for the standard deviation profiles
                t_sd_profile = self.temperature_monthly.variables['t_sd'][self.month_index, :,
                                                                          this_lat_index, this_lon_index]
                s_sd_profile = self.salinity_monthly.variables['s_sd'][self.month_index, :,
                                                                       this_lat_index, this_lon_index]
                t_sd_profile2 = self.temperature_seasonal.variables['t_sd'][self.season_index, :,
                                                                            this_lat_index, this_lon_index]
                s_sd_profile2 = self.salinity_seasonal.variables['s_sd'][self.season_index, :,
                                                                         this_lat_index, this_lon_index]

                # Overwrite the top of the seasonal profiles with the monthly profiles
                t_profile2[0:len(t_profile)] = t_profile
                s_profile2[0:len(s_profile)] = s_profile
                t_sd_profile2[0:len(t_sd_profile)] = t_sd_profile
                s_sd_profile2[0:len(s_sd_profile)] = s_sd_profile

                # Now examine each element in the profile and
                # only keep those whose distance is closer than values
                # found from previous iterations (maintain the closest value
                # at each depth level)
                for count in range(len(t_profile2)):
                    if (dist < distances[count]) and (t_profile2[count] < 50.0) \
                            and (s_profile2[count] < 500.0) and (s_profile2[count] >= 0):
                        temperatures[count] = t_profile2[count]
                        salinities[count] = s_profile2[count]
                        distances[count] = dist

                # Now do the same thing for the temperature standard deviations
                for count in range(len(t_sd_profile2)):
                    if (dist < distances_t_sd[count]) and (t_sd_profile2[count] < 50.0) \
                            and (t_sd_profile2[count] > -2):
                        temperatures_min[count] = t_profile2[count] - t_sd_profile2[count]
                        # can't have overly cold water
                        if temperatures_min[count] < -2.0:
                            temperatures_min[count] = -2.0
                        temperatures_max[count] = t_profile2[count] + t_sd_profile2[count]
                        distances_t_sd[count] = dist

                # Now do the same thing for the salinity standard deviations
                for count in range(len(s_sd_profile2)):
                    if (dist < distances_s_sd[count]) and (s_sd_profile2[count] < 500.0) \
                            and (s_sd_profile2[count] >= 0):
                        salinities_min[count] = s_profile2[count] - s_sd_profile2[count]
                        # Can't have a negative salinity
                        if salinities_min[count] < 0:
                            salinities_min[count] = 0
                        salinities_max[count] = s_profile2[count] + s_sd_profile2[count]
                        distances_s_sd[count] = dist

                num_visited += 1

        if (lat_index == -1) and (lon_index == -1):
            log.info("possible request on land")
            return None, None, None

        lat_out = self.temperature_monthly.variables['lat'][lat_index]
        lon_out = self.temperature_monthly.variables['lon'][lon_index]

        ssp_data.set_position(lat_out, lon_out)
        ssp_min.set_position(lat_out, lon_out)
        ssp_max.set_position(lat_out, lon_out)
        ssp_data.set_time(date_time)
        ssp_min.set_time(date_time)
        ssp_max.set_time(date_time)

        # this is how you do basin lookup
        # basin[0][lat_index][lon_index]
        # This is how you can plot it
        # im = plt.imshow(basin[0][:][:],origin='lower')

        # Isolate realistic values
        i = distances != 99999999
        num_values = len(temperatures[i])
        speed = np.zeros(num_values)
        source = np.zeros(num_values)
        flag = np.zeros(num_values)

        # Add data to sv
        ssp_data.set_samples(depth=self.temperature_seasonal.variables['depth'][0:len(temperatures[i])],
                             speed=speed, temperature=temperatures[i], salinity=salinities[i],
                             source=source, flag=flag)
        # And calculate the sound speed
        ssp_data.calc_speed()

        # Isolate realistic values
        for smp in range(len(temperatures_min)):
            if distances_t_sd[smp] == 99999999 or distances_s_sd[smp] == 99999999:
                num_values = smp
                break

        if num_values > 0:
            speed = np.zeros(num_values)
            source = np.zeros(num_values)
            flag = np.zeros(num_values)

            # Add data to sv
            ssp_min.set_samples(depth=self.temperature_seasonal.variables['depth'][0:num_values],
                                speed=speed, temperature=temperatures_min[0:num_values],
                                salinity=salinities_min[0:num_values],
                                source=source, flag=flag)
            ssp_max.set_samples(depth=self.temperature_seasonal.variables['depth'][0:num_values],
                                speed=speed, temperature=temperatures_max[0:num_values],
                                salinity=salinities_max[0:num_values],
                                source=source, flag=flag)

            # Calculate sound speed profiles
            ssp_min.calc_speed()
            ssp_max.calc_speed()

        else:
            ssp_min = None
            ssp_max = None

        # Set metadata
        ssp_data.sensor_type = Dicts.sensor_types['Synthetic']
        ssp_data.source_info = self.source_info
        ssp_data.driver = self.name + "." + __version__

        return ssp_data, ssp_min, ssp_max

    def close_files(self):
        log.info("close")
        self.temperature_monthly.close()
        self.temperature_seasonal.close()
        self.salinity_monthly.close()
        self.salinity_seasonal.close()
