# ocean variance program
from extract_timeseries import *
from data_processes import *
from data_visulisation import *
from pymse import mse
import pickle
import time

# DBUG
import pdb

#################
# Configuration #
#################

# Load the grid as polygons
polys = grid_polygon(pd.read_csv('./data/oceanGrid.csv'))

# directories
ROMS_directory = '/Volumes/LP_MstrData/master-data/ocean/ROMS/highres'

# check study zone box positions
check_gridROMS(polys, ROMS_directory, 
              depthmax=4000, save=True, out_fn='./plots/study_zones.png')

# # get the mean of the dataset for each cell
# df_mean_temp = polys_mean_ts(polys, 'temp', ROMS_directory, depthmax=1e10)
# # Save the data
# with open('data/tempGrid.pkl','wb') as fp:
#     pickle.dump(df_mean_temp, fp)

# Load the data
with open('data/tempGrid.pkl','rb') as fp:
    df_mean_temp = pickle.load(fp)

# setup paramaters for MSE using values from Balzter et al. (2015)

# Compute MSE for each series
for col in df_mean_temp.columns[1:]:
    print('\nProcessing cell '+col+'..')
    # setup paramaters for MSE using values from Balzter et al. (2015)
    R = 0.3
    # multiply R value by standard deviation of series
    R = R*df_mean_temp[col].std()
    M = 3
    tic = time.process_time()
    entropy = mse(df_mean_temp[col].reset_index(drop=True), 
        m=M, r=R, scale=range(1,365))
    toc = time.process_time()
    print('Completed in',round((toc - tic)/60,1),'minutes')
    print('Saving entropy data..')
    with open('data/entropy/grid_'+col+'.pkl','wb') as fp:
        pickle.dump(entropy, fp)


# # temp plot
# import matplotlib.pyplot as plt
# plt.plot(entropy[0][0])
# plt.show()

# # first and last 5 years
# entropy_fh = mse(df_mean_temp['temp'][:(5*365)].reset_index(drop=True), m=M, r=R, scale=range(1,365))
# entropy_lh = mse(df_mean_temp['temp'][(-5*365):].reset_index(drop=True), m=M, r=R, scale=range(1,365))
