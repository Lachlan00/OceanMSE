# data_prcoesses
import math
import numpy as np
from datetime import datetime
from datetime import timedelta
import copy
from shapely import geometry

#######################
# Add to list quickly #
#######################
def add(lst, obj, index): return lst[:index] + [obj] + lst[index:]

#############################################
# Find min and max values in area in netCDF #
#############################################
def minmax_in_region(data, lons, lats, region):
    """
    Calculate minimum and maximum values in georeferenced array
    Give range as `range = [xmin, xmax, ymin, ymax]`
    """
    # constrain data to region
    bools = (region[0] <= lons) & (lons <= region[1]) & (region[2] <= lats) & (lats <= region[3])  
    data = data[bools]
    # get min and max
    local_min = data.min()
    local_max = data.max()

    return (local_min, local_max)

####################################################
# Convert ocean time (days since 1990) to datetime #
####################################################
def oceantime_2_dt(frame_time):
    """
    Datetime is in local timezone (but not timezone aware)
    """
    dtcon_days = frame_time
    dtcon_start = datetime(1990,1,1)
    dtcon_delta = timedelta(dtcon_days/24/60/60)
    dtcon_offset = dtcon_start + dtcon_delta

    return dtcon_offset

######################
# Harversine formula #
######################
def harversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    # harversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2.)**2. + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2.)**2.
    c = 2. * math.asin(math.sqrt(a))
    km = 6371. * c # radius of earth
    return km

##################
# Make study box #
##################
def boxmaker(lon_orig, lat_orig, km):
    """
    Calculate points directly north, south, east and 
    west a certain distance from given coordinates
    """
    # convert decimal degrees to radians
    lon_orig, lat_orig = map(math.radians, [lon_orig, lat_orig])
    # reverse harversine formula
    c = km / 6371.
    a = math.sin(c/2.)**2.
    dlat = 2. * math.asin(math.sqrt(a))
    dlon = 2. * math.asin(math.sqrt(a/(math.cos(lat_orig)**2.)))
    # convert back to decimal degrees 
    lon_orig, lat_orig, dlat, dlon = map(math.degrees, [lon_orig, lat_orig, dlat, dlon])
    # find coordinates
    north = lat_orig + dlat
    south = lat_orig - dlat
    east = lon_orig + dlon
    west = lon_orig - dlon
    # correct over the 0-360 degree line
    if west > 360:
        west = west - 360
    if east > 360:
        east = east - 360
    # round to 6 decimal places
    region = [west, east, south, north]
    region = [round(x,6) for x in region]

    # export region
    return region

# Return a set of plotgons from a custom grid
def grid_polygon(grid_df):
    # iterate through h and v lines
    polys = [None]*((max(grid_df.hline)-1)*(max(grid_df.vline)-1))
    i = 0
    for h in range(min(grid_df.hline), max(grid_df.hline)):
        for v in range(min(grid_df.vline), max(grid_df.vline)):
            polys[i] = [(h, v), (h, v+1), (h+1, v+1), (h+1, v)]
            i += 1
    # convert to coordinates
    polys = [[(float(grid_df.loc[(grid_df['hline'] == p[0]) & (grid_df['vline'] == p[1])].lon),\
               float(grid_df.loc[(grid_df['hline'] == p[0]) & (grid_df['vline'] == p[1])].lat))\
              for p in poly] for poly in polys]

    # convert to shapely polygons
    polys = [geometry.Polygon(poly) for poly in polys]

    return(polys)

##############################
# Count points in study zone #
##############################
def count_points(lons, lats, region, bath=None, depthmax=1e10):
    """
    Passing bathymetry and depthmax is optional
    """
    # if no bathymetry data, make bath - number so always true
    if bath is None:
        bath = copy.deepcopy(lons)
        bath.fill(-1e10)
    # make generator of all points
    point_tuple = zip(lats.ravel(), lons.ravel(), bath.ravel())
    # iterate over tuple points and keep every point that is in cell
    point_list = []
    j = 0
    for p in point_tuple:
        if region.contains(geometry.Point(p[1], p[0])) and (p[2] <= depthmax):
            point_list.append(j)
        j = j + 1

    # return number of points
    return len(point_list)
