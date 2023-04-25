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


# 0. set up file path

filepath = '/Users/yuanlindong/Documents/python/masterthesis/input/norway/'
filepath_out = '/Users/yuanlindong/Documents/python/masterthesis/output/'
filename = 'datafx.csv'
dirs = os.listdir(filepath)

spot_date = "2023-04-05"
## list of tenors to be modelled
tenor_list = [0]
## list of time steps
step_list = [0,90,180,360]

# 1. import eur/nok fx rate data

df_fx = create_df_fx(filepath, filename, spot_date)
fx_spot = df_fx["value"].loc[df_fx["date"] == spot_date].values[0]


# 2. derive forward fx rate through IRP
temp_filename = 'euro_sr_current.xlsx'
temp_file = filepath_out + temp_filename
temp_euro = pd.read_excel(temp_file)

temp_filename = 'nok_sr_current.xlsx'
temp_file = filepath_out + temp_filename
temp_nok = pd.read_excel(temp_file)

df_fx_fr_current = create_fx_fr_current(temp_euro, temp_nok, fx_spot, step_list)

# 3. historical calibration
df_fx["value_orig"] = df_fx["value"]
df_fx["value"] = np.log(df_fx["value_orig"])
df_fx_historical_calibration = historical_calibration(df_fx)
kappa = list(df_fx_historical_calibration["kappa"])
sigma = list(df_fx_historical_calibration["sigma"])

# 4. estimate piece-wise MRL
df_mrl_estimated = estimate_mrl_fx(df_fx_fr_current, tenor_list, kappa, sigma)

# 5. export data to excel for further analysis
df_2_excel(df_fx_historical_calibration, filepath_out, "fx_mrr_volatility_estimated")
df_2_excel(df_mrl_estimated, filepath_out, "fx_mrl_estimated")


