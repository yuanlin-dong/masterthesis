# Project: Master Thesis
# Author: Yuanlin Dong
# Date of creation: 2023-04-11
# Log of changes:
# Date          What
# 2023-04-20    added a couple of functions created to replace logics in the main file zero_rate_model.py


import csv
from csv import DictReader

import pandas as pd
import numpy as np
import itertools

def infile_2_list(filepath, filename):
    file = filepath + filename
    python_list = []
    with open(file, 'r') as f:
        for line in csv.reader(f):
            python_list.append(line)
    return python_list

def create_df_sr_current(dirs, filepath):
    header = []
    latest_value = []
    latest_date = []
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

    result = pd.concat([temp_est[['latest_date', 'latest_value', 'tenor']], temp_sr[['latest_date', 'latest_value', 'tenor']]])

    result = result.sort_values(by=['tenor'])

    return result

def create_df_sr_current_daily(df_sr_current):
    temp = pd.DataFrame(list(range(1,10801)), columns=['tenor'])
    temp1 = temp.merge(df_sr_current,on='tenor', how='left')

    temp1['latest_value'] = pd.to_numeric(temp1['latest_value'], errors='coerce')
    temp1['latest_value'] = temp1['latest_value'].interpolate(method='linear', limit_direction='forward', axis=0)

    result = temp1
    return result

def create_df_fr_current(step_list, tenor_list, df_sr_current_daily):
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
    df_fr_current = temp

    return df_fr_current

def estimate_mrl(df_fr_current, tenor_list, kappa):
    df_fr_current = df_fr_current.sort_values(by=['tenor', 'step'])
    temp = pd.DataFrame(list(zip(tenor_list, kappa)), columns=['tenor_list', 'kappa'])
    temp1 = df_fr_current.merge(temp, left_on='tenor', right_on='tenor_list', how='left')
    temp1['forward rate lag'] = temp1['forward rate'].shift(1)
    temp1['step lag'] = temp1['step'].shift(1)
    temp1 = temp1[temp1['step'] > 0]
    temp1['MRL'] = ((np.exp(temp1['kappa'])*(temp1['step'] - temp1['step lag']))*temp1['forward rate'] - temp1['forward rate lag'])/(np.exp(temp1['kappa'])*(temp1['step'] - temp1['step lag']))

    result = temp1
    return result

def df_2_excel(df_name, filepath, filename):
    # filename_out = "current_spot_rate.xlsx"
    file_out = filepath + filename + ".xlsx"
    df_name.to_excel(file_out)