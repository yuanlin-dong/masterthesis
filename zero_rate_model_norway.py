# Project: Master Thesis
# Author: Yuanlin Dong
# Date of creation: 2023-04-25
# Log of changes:
# Date          What

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

spot_date = "2023-04-05"
## list of tenors to be modelled
tenor_list = [1,180,270,360,720,1440,3600]
## list of time steps
step_list = [0,90,180,360]

# 0. set up file path

filepath = '/Users/yuanlindong/Documents/python/masterthesis/input/norway/'
filepath_out = '/Users/yuanlindong/Documents/python/masterthesis/output/'
filename = 'GOVT_ZEROCOUPON.csv'
filename_nowa = 'SHORT_RATES.csv'
dirs = os.listdir(filepath)

# 1. historical calibration of MRR and volatility

## import Norway zero rate curve data
df_sr_all = create_df_sr_all_norway(filepath, filename, filename_nowa, spot_date)

## run historical calibration algorithm
df_sr_selected = df_sr_all.loc[df_sr_all['tenor'].isin(tenor_list)]
df_nok_sr_historical_calibration = historical_calibration(df_sr_selected)
kappa = list(df_nok_sr_historical_calibration["kappa"])

# 2. create input data: current forward rates for the MRL calibration

## to extract current spot rates from input files
df_sr_current = df_sr_all.loc[df_sr_all["date"] == spot_date]

## construct daily spot rate curve through linear interpolation and flat extrapolation
df_sr_current_daily = create_df_sr_current_daily(df_sr_current)

## derive the list of forward rates corresponding to each combination of step and tenor from daily spot rate curve
df_fr_current = create_df_fr_current(step_list, tenor_list, df_sr_current_daily)

# 3. estimate piece-wise MRL
df_mrl_estimated = estimate_mrl(df_fr_current, tenor_list, kappa)

# 4. export data to excel for further analysis
df_2_excel(df_nok_sr_historical_calibration, filepath_out, "nok_mrr_volatility_estimated")
df_2_excel(df_mrl_estimated, filepath_out, "nok_mrl_estimated")
df_2_excel(df_sr_current_daily, filepath_out, "nok_sr_current")





