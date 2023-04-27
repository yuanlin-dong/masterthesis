# Project: Master Thesis
# Author: Yuanlin Dong
# Date of creation: 2023-04-11
# Log of changes:
# Date          What
# 2023-04-20    added a couple of functions created to replace logics in the main file zero_rate_model.py
# 2023-04-25    added two functions - one for importing and process all historical data, another for the historical calibration
# 2023-04-25    added two functions for processing nok ir data as it has a different structure to the euro ir data
# 2023-04-25    added functions for processing fx data and also for calibrating the fx model
# 2023-04-26    added functions for model calibration based on arbitrage-free theorem
import csv
from csv import DictReader

import pandas as pd
import numpy as np
import itertools

from scipy.stats import *
from scipy.optimize import *


##########################################functions for zero rate model and CRR's FX rate model###############################
def infile_2_list(filepath, filename):
    file = filepath + filename
    python_list = []
    with open(file, 'r') as f:
        for line in csv.reader(f):
            python_list.append(line)
    return python_list

def create_df_sr_all(dirs, filepath):
    header = []
    value = []
    date = []
    for filename in dirs:
        if '.csv' in filename:
            print(filename)
            temp = infile_2_list(filepath, filename)
            a = temp[0]
            for i in range(1, len(temp)):
                b = temp[i]
                c = [b[0]]*(len(b) - 1)
                header.extend(a[1:len(a)])
                value.extend(b[1:len(b)])
                date.extend(c)

    temp_sr = pd.DataFrame(np.column_stack([header, date, value]), columns=['header', 'date', 'value'])
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

    result = pd.concat([temp_est[['date', 'value', 'tenor']], temp_sr[['date', 'value', 'tenor']]])

    result['value'] = pd.to_numeric(result['value'], errors='coerce')
    result = result.sort_values(by=['tenor', 'date'])

    return result

def create_df_sr_current(dirs, filepath):
    header = []
    value = []
    date = []
    for filename in dirs:
        if '.csv' in filename:
            # print(filename)
            temp = infile_2_list(filepath, filename)
            a = temp[0]
            b = temp[1]
            c = [b[0]]*(len(b) - 1)
            header.extend(a[1:len(a)])
            value.extend(b[1:len(b)])
            date.extend(c)

    temp_sr = pd.DataFrame(np.column_stack([header, date, value]), columns=['header', 'date', 'value'])
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

    result = pd.concat([temp_est[['date', 'value', 'tenor']], temp_sr[['date', 'value', 'tenor']]])

    result = result.sort_values(by=['tenor'])

    return result

def create_df_sr_current_daily(df_sr_current):
    temp = pd.DataFrame(list(range(1,10801)), columns=['tenor'])
    temp1 = temp.merge(df_sr_current,on='tenor', how='left')

    temp1['value'] = pd.to_numeric(temp1['value'], errors='coerce')
    temp1['value'] = temp1['value'].interpolate(method='linear', limit_direction='forward', axis=0)

    result = temp1
    return result

def create_df_fr_current(step_list, tenor_list, df_sr_current_daily):
    temp = pd.DataFrame(itertools.product(step_list, tenor_list), columns=['step', 'tenor'])
    temp['forward_start'] = temp['step']
    temp['forward_end'] = temp['step'] + temp['tenor']
    temp = temp.drop(columns=['tenor'])

    temp = temp.merge(df_sr_current_daily, left_on='forward_start', right_on='tenor', how='left')
    temp = temp.rename(columns={"value": "forward_start_rate"})
    temp = temp.drop(columns=['tenor', 'date'])
    temp = temp.merge(df_sr_current_daily, left_on='forward_end', right_on='tenor', how='left')
    temp = temp.rename(columns={"value": "forward_end_rate"})
    temp = temp.drop(columns=['tenor', 'date'])
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
    temp1['mrl'] = ((np.exp(temp1['kappa'])*(temp1['step'] - temp1['step lag']))*temp1['forward rate'] - temp1['forward rate lag'])/\
                   (np.exp(temp1['kappa'])*(temp1['step'] - temp1['step lag']))

    result = temp1
    return result

def df_2_excel(df_name, filepath, filename):
    # filename_out = "current_spot_rate.xlsx"
    file_out = filepath + filename + ".xlsx"
    df_name.to_excel(file_out)

def historical_calibration(df_sr_selected):
    df_sr_selected.sort_values(by=['tenor', 'date'], inplace=True)
    df_sr_selected['tenor lag'] = df_sr_selected['tenor'].shift(1)
    df_sr_selected['value lag'] = df_sr_selected['value'].shift(1)

    auto_covar = df_sr_selected.loc[df_sr_selected['tenor lag'] == df_sr_selected['tenor']]
    auto_covar['auto covar'] = (auto_covar['value'] - auto_covar['value lag']) ** 2

    a = pd.DataFrame(df_sr_selected['value'].groupby(df_sr_selected['tenor']).mean())
    a.reset_index(inplace=True)
    a.rename(columns={"value": "a"}, inplace=True)

    var = df_sr_selected.merge(a, on="tenor", how="left")
    var["var"] = (var["value"] - var["a"]) ** 2

    var_sum = pd.DataFrame(var['var'].groupby(var['tenor']).sum())
    var_sum.reset_index(inplace=True)

    auto_covar_sum = pd.DataFrame(auto_covar["auto covar"].groupby(auto_covar["tenor"]).sum())
    auto_covar_sum.reset_index(inplace=True)

    kappa = var_sum.merge(auto_covar_sum, on="tenor", how="left")
    kappa["kappa"] = (1 / (2 * 1 / 255)) * kappa["auto covar"] / kappa["var"]

    N_1 = pd.DataFrame(auto_covar["date"].groupby(auto_covar["tenor"]).count())
    N_1.reset_index(inplace=True)
    N_1.rename(columns={"date": "N_1"}, inplace=True)

    result = kappa.merge(N_1, on="tenor", how="left")
    result["sigma"] = np.sqrt((2 * result["kappa"] - (result["kappa"] ** 2) / 255) * result["var"] / result["N_1"])

    return result

def TENOR_2_tenor_norway(x):
    if "Y" in x:
        tenor = pd.to_numeric(x[0:len(x)-1], errors='coerce')*360
    elif "M" in x:
        tenor = pd.to_numeric(x[0:len(x)-1], errors='coerce')*30
    return tenor

def create_df_sr_all_norway(filepath, filename, filename_nowa, spot_date):
    file = filepath + filename
    df_sr = pd.read_csv(file, delimiter=";")
    df_sr["tenor"] = df_sr["TENOR"].apply(TENOR_2_tenor_norway)
    df_sr = df_sr[["TIME_PERIOD", "tenor", "OBS_VALUE"]]
    df_sr.rename(columns={"TIME_PERIOD": "date", "OBS_VALUE": "value"}, inplace=True)

    file_nowa = filepath + filename_nowa
    df_nowa = pd.read_csv(file_nowa, delimiter=";")
    df_nowa = df_nowa[["TIME_PERIOD", "OBS_VALUE"]]
    df_nowa.rename(columns={"TIME_PERIOD": "date", "OBS_VALUE": "value"}, inplace=True)
    df_nowa["tenor"] = 1

    df_sr_all = pd.concat([df_sr, df_nowa], ignore_index=True)
    df_sr_all = df_sr_all.loc[df_sr_all["date"] <= spot_date]
    df_sr_all.sort_values(by=["date", "tenor"], inplace=True)

    return df_sr_all


def create_df_fx(filepath, filename, spot_date):
    file = filepath + filename
    df_fx = pd.read_csv(file, index_col=None, header=None, skiprows=5)
    df_fx.rename(columns={0: 'date', 1: 'value'}, inplace=True)
    df_fx = df_fx.loc[df_fx["date"] <= spot_date]
    df_fx["value"] = pd.to_numeric(df_fx["value"], errors="coerce")
    df_fx["tenor"] = 0
    df_fx.sort_values(by=['date'], inplace=True)

    return df_fx

def create_fx_fr_current(temp_euro, temp_nok, fx_spot, step_list):
    temp = temp_euro.merge(temp_nok, on="tenor", how="left")
    temp = temp[["tenor", "value_x", "value_y"]]
    temp.rename(columns={"value_x": "value_euro", "value_y": "value_nok"}, inplace=True)

    temp_selected = temp.loc[temp['tenor'].isin(step_list)]
    temp_selected["fx multiplier"] = np.exp(
        0.01 * (temp_selected["value_nok"] - temp_selected["value_euro"]) * temp_selected["tenor"] / 360)

    temp_selected["fx forward"] = temp_selected["fx multiplier"] * fx_spot

    temp_selected.rename(columns={"tenor": "step", "fx forward": "forward rate"}, inplace=True)
    temp_selected["tenor"] = 0
    temp_selected = temp_selected[["step", "tenor", "forward rate"]]

    temp_0 = {'step': [0], 'tenor': [0], 'forward rate': [fx_spot]}
    temp_0 = pd.DataFrame(temp_0)
    df_fx_fr_current = pd.concat([temp_0, temp_selected], ignore_index=True)

    return df_fx_fr_current

def estimate_mrl_fx(df_fx_fr_current, tenor_list, kappa, sigma):
    temp = pd.DataFrame(list(zip(tenor_list, kappa, sigma)), columns=['tenor_list', 'kappa', 'sigma'])
    temp1 = df_fx_fr_current.merge(temp, left_on='tenor', right_on='tenor_list', how='left')
    temp1["forward rate orig"] = temp1["forward rate"]
    temp1["forward rate"] = np.log(temp1["forward rate orig"])

    temp1["adj1"] = np.exp(temp1["kappa"] * temp1["step"] / 360) - np.exp(-1 * temp1["kappa"] * temp1["step"] / 360)
    temp1["adj1 cumsum"] = temp1["adj1"].cumsum()

    temp1["adj1 cumsum lag"] = temp1["adj1"].shift(1)
    temp1['forward rate lag'] = temp1['forward rate'].shift(1)
    temp1['step lag'] = temp1['step'].shift(1)

    temp1 = temp1[temp1['step'] > 0]

    temp1["exp adj"] = (temp1["adj1"] - temp1["adj1 cumsum lag"]) * temp1["sigma"] ** 2 / \
                       (4 * temp1["kappa"] * (np.exp(temp1["kappa"] * temp1["step"] / 360) - np.exp(
                           temp1["kappa"] * temp1["step lag"] / 360)))

    temp1['mrl wo adj'] = ((np.exp(temp1['kappa']) * (temp1['step'] - temp1['step lag'])) * temp1['forward rate'] -
                           temp1['forward rate lag']) / \
                          (np.exp(temp1['kappa']) * (temp1['step'] - temp1['step lag']))

    temp1['mrl'] = temp1['mrl wo adj'] - temp1['exp adj']

    return temp1

##########################Functions for the 1-factor-hjm-model#############################################################

def myIntegral(b, nu, t0, t1):
    return nu ** 2 / b ** 2 * (np.exp(-b * t0) - np.exp(-b * t1)) ** 2 * (np.exp(2 * b * t0) - 1) / (2 * b)

def CapVasicek(b, nu, kappa, ForwardRates, T, M, delta, Z):
    myAns = 0
    k = kappa[M]
    for i in range(1, (2 * M + 2)):
        I = myIntegral(b, nu, T[i], T[i + 1])
        print(I)
        d1 = (np.log(Z[i + 1] / Z[i] * (1 + delta * k)) + 0.5 * I) / np.sqrt(I)
        d2 = (np.log(Z[i + 1] / Z[i] * (1 + delta * k)) - 0.5 * I) / np.sqrt(I)
        cplt_i = Z[i] * norm.cdf(-d2, 0, 1) - (1 + delta * k) * Z[i + 1] * (norm.cdf(-d1, 0, 1))
        # print(Z[i+2])
        # print(cplt_i)
        myAns = myAns + cplt_i
    return myAns

def BlackVega(delt, Z, fwds, T, sig, M, kap):
    myAns = 0
    k = kap[M]
    for i in range(1, (2 * M + 2)):
        # print(fwds[i])
        # print(sig)
        d1 = (np.log(fwds[i] / k) + 0.5 * sig ** 2 * T[i]) / (sig * np.sqrt(T[i]))
        # d2 = d1 - sig*sqrt(T[i])
        cplt_Vega = delt * Z[i + 1] * fwds[i] * np.sqrt(T[i]) * norm.pdf(d1, 0, 1)
        myAns = myAns + cplt_Vega
    return myAns

def BlackCap(sig, kap, fwds, T, M, delt, Z):
    myAns = 0
    k = kap[M]
    for i in range(1, (2 * M + 2)):
        d1 = (np.log(fwds[i] / k) + 0.5 * (sig ** 2) * T[i]) / (sig * np.sqrt(T[i]))
        d2 = d1 - sig * np.sqrt(T[i])
        cplt_i = delt * Z[i + 1] * (fwds[i] * norm.cdf(d1, 0, 1) - k * norm.cdf(d2, 0, 1))
        myAns = myAns + cplt_i
    return myAns