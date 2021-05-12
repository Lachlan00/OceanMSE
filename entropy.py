# ocean variance program
from extract_timeseries import *
from data_processes import *
from data_visulisation import *
from pymse import mse

# DBUG
import pdb

#################
# Configuration #
#################

# directories
ROMS_directory = '/Volumes/LP_MstrData/master-data/ocean/ROMS/highres'

# Study zone
BateBox = boxmaker(150.2269, -36.25201, 20)

# check study zone box positions
check_boxROMS([BateBox], ROMS_directory, 
            depthmax=4000, save=True, out_fn='./plots/study_zones.png')

# get the mean of the dataset
df_mean_temp = region_mean_ts(ROMS_directory, 'temp', BateBox, depthmax=1e10)

# setup paramaters for MSE using values from Balzter et al. (2015)
R = 0.3
# multiply R value by standard deviation of series
R = R*df_mean_temp['temp'].std()
M = 3

entropy = mse(df_mean_temp['temp'][:].reset_index(drop=True), m=M, r=R, scale=range(1,365))

# temp plot
import matplotlib.pyplot as plt
plt.plot(entropy[0][0])
plt.show()

# first and last 5 years
entropy_fh = mse(df_mean_temp['temp'][:(5*365)].reset_index(drop=True), m=M, r=R, scale=range(1,365))
entropy_lh = mse(df_mean_temp['temp'][(-5*365):].reset_index(drop=True), m=M, r=R, scale=range(1,365))
