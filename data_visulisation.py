# make plots
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Polygon
import matplotlib.dates as mdates
import cmocean # oceanogrpahy colorscales - https://matplotlib.org/cmocean/
from datetime import datetime
from datetime import timedelta
import PIL
import numpy as np
from os import listdir
from os.path import isfile, join
from netCDF4 import Dataset
from scipy import stats
import seaborn as sns


# DBUG
import pdb

# Hack to fix missing PROJ4 env var for basemap
import os
conda_dir = '/Users/lachlanphillips/miniconda3/'
proj_lib = os.path.join(os.path.join(conda_dir, 'share'), 'proj')
os.environ["PROJ_LIB"] = proj_lib
from mpl_toolkits.basemap import Basemap

# local modules
from data_processes import *

# # Test polygon print


################
# plot polygon #
################
def make_polygon(region, m):
    x1,y1 = m(region[0],region[2]) 
    x2,y2 = m(region[0],region[3]) 
    x3,y3 = m(region[1],region[3]) 
    x4,y4 = m(region[1],region[2])
    p = Polygon([(x1,y1),(x2,y2),(x3,y3),(x4,y4)], facecolor='none',
                edgecolor='#ff0000',linewidth=2,ls='dashed', zorder=10)

    return(p)

###############################################
# Check box positions relative to ROMS extent #
###############################################
def check_gridROMS(polys, ROMS_directory, depthmax=1e10, save=False, 
    out_fn='', margin=.05, clim=[0, 500], depth_unit='m', count_cells=False,
    plot_depthmax=False):
    print('\nChecking analysis regions..')
    file_ls = [f for f in listdir(ROMS_directory) if isfile(join(ROMS_directory, f))]
    file_ls = list(filter(lambda x:'.nc' in x, file_ls))
    file_ls = sorted(file_ls)
    # obtain bathymetry data
    nc_file = ROMS_directory + '/' + file_ls[0]
    fh = Dataset(nc_file, mode='r')
    lats = fh.variables['lat_rho'][:] 
    lons = fh.variables['lon_rho'][:]
    bath = fh.variables['h'][:]

    # set title
    title = 'Analysis Regions'
    if len(polys) == 1:
        title = 'Analysis Region'

    # Check balance
    if (count_cells):
        print('Study zone balance (grid cell count)..')
        for region, i in zip(polys, range(1,len(polys)+1)):
            cells = count_points(lons, lats, region, bath, depthmax)
            print('Cell '+str(i)+': '+str(cells))

    # convert bath to km
    depth_conv = 1
    if depth_unit == 'km':
        depth_conv = 1000
    bath = bath/depth_conv

    if clim is None:
        clim = [min(bath, max(bath))]

    # calculate box min max
    box_lonMin = min([min(poly.exterior.xy[0]) for poly in polys])
    box_lonMax = max([max(poly.exterior.xy[0]) for poly in polys])
    box_latMin = min([min(poly.exterior.xy[1]) for poly in polys])
    box_latMax = max([max(poly.exterior.xy[1]) for poly in polys])

    # setup map
    m = Basemap(projection='merc', llcrnrlat=box_latMin-margin, urcrnrlat=box_latMax+margin,\
        llcrnrlon=box_lonMin-margin, urcrnrlon=box_lonMax+margin, lat_ts=20, resolution='h')

    # make plot
    fig = plt.figure(figsize=(8,8))
    plt.tight_layout()
    plt.title(title, size=15)
    # draw stuff
    m.drawcoastlines(color='black', linewidth=0.7)
    m.fillcontinents(color='#A0A0A0')
    # add grid
    parallels = np.arange(-81.,0,.2)
    m.drawparallels(parallels,labels=[True,False,False,True], linewidth=1, dashes=[3,3], color='#707070')
    meridians = np.arange(10.,351.,.2)
    m.drawmeridians(meridians,labels=[True,False,False,True], linewidth=1, dashes=[3,3], color='#707070')
    # add bathymetry extent
    cs = m.pcolor(lons, lats, np.squeeze(bath), latlon=True ,vmin=clim[0]/depth_conv, 
        vmax=clim[1]/depth_conv, cmap=cmocean.cm.deep)
    cbar = plt.colorbar()
    if plot_depthmax:
        CS = m.contour(lons, lats, np.squeeze(bath), [depthmax/depth_conv], colors='k', latlon=True, linestyles='dashed', alpha=0.9)
    cbar.ax.invert_yaxis()
    cbar.ax.set_ylabel('Depth ('+depth_unit+')', rotation=270, labelpad=16, size=12)

     # add polygons
    for poly in polys:
        x,y = poly.exterior.xy
        x,y = m(x,y)
        plt.plot(x,y, color='red')

    # save plot
    if save:
        print('\nSaving plot..')
        fig.savefig(out_fn)
    else:
        # show plot
        print('Close plot to continue..')
        plt.show()
        plt.close("all")

#########################
# Merge images together #
#########################
def img_join(output_name, img_ls, direction='vertical'):
    # open images
    images = [PIL.Image.open(i) for i in img_ls]
    
    # Resize if needed
    if direction == 'vertical':
        h_ls = [i.size[0] for i in images]
        if len(set(h_ls)) != 1:
            print('Width dimensions are not equal.. resizing')
            min_h = min(h_ls)
            images = [i.resize((min_h, i.size[1])) for i in images] 
    if direction == 'horizontal':
        v_ls = [i.size[1] for i in images]
        if len(set(v_ls)) != 1:
            print('Height dimensions are not equal.. resizing')
            min_v = min(v_ls)
            images = [i.resize((i.size[0], min_v)) for i in images] 

    # stack
    if direction == 'vertical':
        imgs_comb = np.vstack(np.asarray(i) for i in images)
        imgs_comb = PIL.Image.fromarray(imgs_comb)
        imgs_comb.save(output_name)
    elif direction == 'horizontal':
        imgs_comb = np.hstack(np.asarray(i) for i in images)
        imgs_comb = PIL.Image.fromarray(imgs_comb)
        imgs_comb.save(output_name)    
    else:
        print('Error: invalid margin string')

    print('\nImages joined - saved to: '+output_name)
