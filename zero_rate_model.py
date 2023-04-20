# Project: Master Thesis
# Author: Yuanlin Dong
# Date of creation: 2023-04-10
# Log of changes:
# Date          What
# 2023-04-20    Convert logics in this file into a list of functions,
#               place the list of functions into the file functions.py,
#               and call those functions in this file


###a refresh to clear all variables before running the script###
from IPython import get_ipython
get_ipython().run_line_magic('reset', '-sf')
###a refresh to clear all variables before running the script###

import pandas as pd
import numpy as np
import itertools

import scipy
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

import csv
from csv import DictReader

import os, sys

from functions import *


# 0. set up file path

filepath = '/Users/yuanlindong/Documents/python/masterthesis/input/'
filepath_out = '/Users/yuanlindong/Documents/python/masterthesis/output/'

## list of tenors to be modelled
tenor_list = [30,90,180,360,720,1440,3960]
## list of time steps
step_list = [0,90,180,360]

## kappa - a placeholder, to be estimated from historical data
kappa = [0.0054, 0.0065, 0.0035, 0.0058, 0.0025, 0.0085, 0.0055]

# kappa = [0.54, 0.65, 0.35, 0.58, 0.25, 0.85, 0.55]

# 1. create input data: current forward rates for the MRL calibration

## to extract current spot rates from input files
dirs = os.listdir(filepath)
df_sr_current = create_df_sr_current(dirs, filepath)

## construct daily spot rate curve through linear interpolation and flat extrapolation
df_sr_current_daily = create_df_sr_current_daily(df_sr_current)

## derive the list of forward rates corresponding to each combination of step and tenor from daily spot rate curve
df_fr_current = create_df_fr_current(step_list, tenor_list, df_sr_current_daily)


# 2. estimate piece-wise MRL
df_mrl_estimated = estimate_mrl(df_fr_current, tenor_list, kappa)

# 3. export data to excel for further analysis
df_2_excel(df_mrl_estimated, filepath_out, "mrl_estimated")









