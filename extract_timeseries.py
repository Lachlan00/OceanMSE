# oceanvar
# Perform model
import numpy as np
import pandas as pd
from os import listdir
from os.path import isfile, join
from netCDF4 import Dataset
from progressbar import ProgressBar

# user defined modules
from data_processes import *

def region_mean(var, fh, frame_time, frame_idx, eta_rho, xi_rho):
    # get temperature and salinity data in region of interest
    data = fh.variables[var][frame_idx,29,:,:][eta_rho, xi_rho]

    return [frame_time, data.mean()]

def region_mean_ts(ROMS_directory, var, region, grid=None, depthmax=1e10):
    """
    depthmax in meters (arbitarily large by default)
    """
    print('\nExtracting mean time series..')
    # get ROMS netCDF file list
    file_ls = [f for f in listdir(ROMS_directory) if isfile(join(ROMS_directory, f))]
    file_ls = list(filter(lambda x:'.nc' in x, file_ls))
    file_ls = sorted(file_ls)

    # get lats and lons
    nc_file = ROMS_directory + '/' + file_ls[0]
    fh = Dataset(nc_file, mode='r')
    lats = fh.variables['lat_rho'][:] 
    lons = fh.variables['lon_rho'][:]
    bath = fh.variables['h'][:]
    ocean_time = fh.variables['ocean_time'][:]
    array_dimensions = lons.shape

    # combine lat and lon to list of tuples
    point_tuple = zip(lats.ravel(), lons.ravel(), bath.ravel())
    # iterate over tuple points and keep every point that is in box
    point_list = []
    j = 0
    for i in point_tuple:
        if region[2] <= i[0] <= region[3] and region[0] <= i[1] <= region[1] and i[2] < depthmax:
            point_list.append(j)
        j = j + 1

    # make point list into tuple list of array coordinates
    eta_rho = []
    xi_rho = []
    for i in point_list:
        eta_rho.append(int(i/array_dimensions[1]))
        xi_rho.append(int(i%array_dimensions[1]))

    # set up progress bar
    pbar = ProgressBar(max_value=len(file_ls))

    # create data frame to hold count data
    df_mean = pd.DataFrame(np.nan, index=range(0,(len(file_ls)+1)*len(ocean_time)), columns=['dt', var])
    # extract count data from each netCDF file
    idx = 0
    print('Extracting the mean "'+var+'" for '+str(len(file_ls))+' netCDF files..')
    pbar.update(0)
    for i in range(0, len(file_ls)):
        # import file
        nc_file = ROMS_directory + '/' + file_ls[i]
        fh = Dataset(nc_file, mode='r')
        # extract time
        ocean_time = fh.variables['ocean_time'][:]
        # get data
        for j in range(0, len(ocean_time)):
            # get dt from ocean_time
            frame_time = oceantime_2_dt(ocean_time[j])
            # get counts and sub into data frame
            df_mean.iloc[idx] = region_mean(var, fh, frame_time, j, eta_rho, xi_rho)
            idx += 1
            # update progress
            pbar.update(i)

        # close file
        fh.close()

    # drop NaNs and return dataset
    return(df_mean.dropna())