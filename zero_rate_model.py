# Project: Master Thesis
# Author: Yuanlin Dong
# Date of creation: 2023-04-10

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

# 1. import input files
header = []
latest_value = []
latest_date = []


dirs = os.listdir(filepath)
for filename in dirs:
    if '.csv' in filename:
        # print(filename)
        temp = infile_2_list(filepath, filename)
        a = temp[0]
        b = temp[1]
        c = [b[0]]*(len(b) - 1)
        header.extend(a[1:len(a)])
        latest_value.extend(b[1:len(b)])
        latest_date.extend(c)

temp_sr = pd.DataFrame(np.column_stack([header, latest_date, latest_value]), columns=['header', 'latest_date', 'latest_value'])
temp_sr['tt'] = temp_sr['header'].str[29:len(temp_sr['header'])-28]
temp_est = temp_sr[temp_sr['header'] == 'EST.B.EU000A2X2A25.WT'] ### obtain ester data
temp_sr = temp_sr[temp_sr['tt'].str[0:3] == 'SR_'] ### remove spread data


### derive the tenor from the header data
temp_sr['tenor_text'] = temp_sr['tt'].str[3:len(temp_sr['tt'])-3]
temp_sr['ccc'] = temp_sr['tenor_text'].str.find('Y')
temp_sr['tenor_year'] = temp_sr.apply(lambda x: x['tenor_text'][0:max(0,x['ccc'])], 1)
temp_sr['tenor_month'] = temp_sr.apply(lambda x: x['tenor_text'][x['ccc'] + 1:len(x['tenor_text'])-1], 1)
temp_sr['tenor_year'] = pd.to_numeric(temp_sr['tenor_year'], errors='coerce').fillna(0).astype('int64')
temp_sr['tenor_month'] = pd.to_numeric(temp_sr['tenor_month'], errors='coerce').fillna(0).astype('int64')
temp_sr['tenor'] = temp_sr['tenor_year']*360 + temp_sr['tenor_month']*30

temp_est['tenor'] = 1

df_sr_current = pd.concat([temp_est[['latest_date', 'latest_value', 'tenor']], temp_sr[['latest_date', 'latest_value', 'tenor']]])

df_sr_current = df_sr_current.sort_values(by=['tenor'])

# 2. construct daily spot rate curve through linear interpolation and flat extrapolation

temp = pd.DataFrame(list(range(1,10800)), columns=['tenor'])
temp1 = temp.merge(df_sr_current,on='tenor',how='left')

temp1['latest_value'] = pd.to_numeric(temp1['latest_value'], errors='coerce')
temp1['latest_value'] = temp1['latest_value'].interpolate(method='linear', limit_direction='forward', axis=0)

df_sr_current_daily = temp1

filename_out = "current_spot_rate.xlsx"
file_out = filepath_out + filename_out
df_sr_current.to_excel(file_out)

# 3. derive forward rate from daily spot rate curve
temp = pd.DataFrame(itertools.product(step_list, tenor_list), columns=['step', 'tenor'])
temp['forward_start'] = temp['step']
temp['forward_end'] = temp['step'] + temp['tenor']
temp = temp.drop(columns=['tenor'])

temp = temp.merge(df_sr_current_daily, left_on='forward_start', right_on='tenor', how='left')
temp = temp.rename(columns={"latest_value": "forward_start_rate"})
temp = temp.drop(columns=['tenor', 'latest_date'])
temp = temp.merge(df_sr_current_daily, left_on='forward_end', right_on='tenor', how='left')
temp = temp.rename(columns={"latest_value": "forward_end_rate"})
temp = temp.drop(columns=['tenor', 'latest_date'])
temp['forward_start_rate'] = temp['forward_start_rate'].fillna(0)
temp['forward_end_rate'] = temp['forward_end_rate'].fillna(0)
temp['forward rate'] = (temp['forward_end']*temp['forward_end_rate'] - temp['forward_start']*temp['forward_start_rate'])/(temp['forward_end'] - temp['forward_start'])

temp['tenor'] = temp['forward_end'] - temp['forward_start']
temp = temp[['step', 'tenor', 'forward rate']]
df_fr_current_daily = temp
del temp, temp1, temp_sr, temp_est, a, b, c

# 4. calculate piece-wise MRL
df_fr_current_daily = df_fr_current_daily.sort_values(by=['tenor', 'step'])
temp = pd.DataFrame(list(zip(tenor_list, kappa)), columns=['tenor_list', 'kappa'])
temp1 = df_fr_current_daily.merge(temp, left_on='tenor', right_on='tenor_list', how='left')
temp1['forward rate lag'] = temp1['forward rate'].shift(1)
temp1['step lag'] = temp1['step'].shift(1)
temp1 = temp1[temp1['step'] > 0]
temp1['MRL'] = ((np.exp(temp1['kappa'])*(temp1['step'] - temp1['step lag']))*temp1['forward rate'] - temp1['forward rate lag'])/(np.exp(temp1['kappa'])*(temp1['step'] - temp1['step lag']))

result = temp1
del temp, temp1










