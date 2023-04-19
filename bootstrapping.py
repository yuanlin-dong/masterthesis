# Project: Master Thesis
# Author: Yuanlin Dong
# Date of creation: 2023-04-06


import pandas as pd
import numpy as np
import datetime

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

# 1. import data
start_date = date(2012, 10, 3)

df_indata = pd.read_excel(r'/Users/yuanlindong/Documents/python/masterthesis/input/bootstrap_data.xlsx',
                   sheet_name='to_python1')
print(df_indata)
df_tenor = pd.read_excel(r'/Users/yuanlindong/Documents/python/masterthesis/input/bootstrap_data.xlsx',
                   sheet_name='to_python2')
print(df_tenor)

df_indata['Maturity Dates'] = df_indata['Maturity Dates'].dt.date
df_indata['days'] = pd.to_timedelta(df_indata['Maturity Dates'] - start_date).dt.days.astype('int')
df_indata['delta'] = df_indata['days']/360

df_tenor['Tenor'] = df_tenor['Tenor'].dt.date

# 2. bootstrap

## LIBOR
df_libor = pd.DataFrame(df_indata[df_indata['Source'] == 'LIBOR'])

df_libor['discount_factor'] = 1/(1+df_libor['delta']*df_libor['Market Quotes'])

df_libor_df = df_libor[['Maturity Dates','Source','days', 'discount_factor']]

## FUTURE
df_future = pd.DataFrame(df_indata[df_indata['Source'] == 'Futures'])
df_future['future_rate'] = 1-df_future['Market Quotes']/100

### the first reset date is 3 months before the maturity date of the first future contract, and we obtain DF of the first reset date through interpolation
reset_date_1 = date(2013,3,20)
reset_days_1 = (reset_date_1 - start_date).days/360
df_temp = df_libor
df_temp['rel_days'] = pd.to_timedelta(df_temp['Maturity Dates'] - reset_date_1).dt.days.astype('int')
df_temp['rel_days_sort'] = df_temp['rel_days'].abs()
df_temp.sort_values(by=['rel_days_sort'], inplace=True)
df_temp = df_temp.head(2)
df_temp = df_temp.sort_values(by=['rel_days'])
q = df_temp.iloc[1,6]/(df_temp.iloc[1,3] - df_temp.iloc[0,3])
libor_1 = df_temp.iloc[0,1]*q + df_temp.iloc[1,1]*(1-q)
discount_factor_1 = 1/(1+reset_days_1*libor_1)

### obtain the DF of maturity dates of futures
df_future.sort_values(by=['Maturity Dates'], inplace=True)
df_future.reset_index(inplace=True)
df_future.drop(columns=['index'],inplace=True)

df_future_df = []
for index, row in df_future.iterrows():
    if index == 0:
        delta_lag = reset_days_1
        delta = row['delta']
        discount_factor = discount_factor_1/(1+(delta - delta_lag)*row['future_rate'])
        delta_lag = delta
    elif index > 0:
        delta = row['delta']
        discount_factor = discount_factor/(1+(delta - delta_lag)*row['future_rate'])
        delta_lag = delta

    df_future_df.append((row['Maturity Dates'], row['Source'], row['days'], discount_factor))

df_future_df.append((reset_date_1, 'Interpolation', reset_days_1*360, discount_factor_1))

df_future_df = pd.DataFrame(df_future_df, columns=("Maturity Dates", "Source", "days", "discount_factor"))

## Swap
df_swap = pd.DataFrame(df_indata[df_indata['Source'] == 'Swap'])

### get a list of tenors corresponding to swaps
df_libor_future_df = pd.concat([df_libor_df, df_future_df], ignore_index=True, axis=0)
df_temp = df_tenor.merge(df_libor_future_df, left_on='Tenor', right_on='Maturity Dates', how='left')
df_temp = df_temp[df_temp['Maturity Dates'].isna()]
df_temp = df_temp[['Tenor']]

### linear interpolation of swap rates
df_swap_tenor = df_temp.merge(df_swap, left_on='Tenor', right_on='Maturity Dates', how='left')
# df_swap_tenor['days'] = pd.to_timedelta(df_swap_tenor['Tenor'] - start_date).dt.days.astype('int')
df_swap_tenor = df_swap_tenor.sort_values(by=['Tenor','Maturity Dates'],ascending=False)
df_temp = []
for index, row in df_swap_tenor.iterrows():
    tenor = row['Tenor']
    if pd.isna(row['Maturity Dates']) == False:
        maturity_dates_right = row['Maturity Dates']
        market_quotes_right = row['Market Quotes']
    df_temp.append((tenor, maturity_dates_right, market_quotes_right, row['Maturity Dates'], row['Market Quotes']))
df_temp = pd.DataFrame(df_temp, columns=("Tenor", "Maturity Dates right", "Market Quotes right", "Maturity Dates", "Market Quotes"))

df_temp = df_temp.sort_values(by=['Tenor', 'Maturity Dates'])
df_temp['Maturity Dates left'] = df_temp['Tenor'].shift(1)

#### drop the first row as it can not be interpolated
df_temp = df_temp.iloc[1:]
df_temp['q'] = (df_temp['Maturity Dates right'] - df_temp['Tenor'])/(df_temp['Maturity Dates right'] - df_temp['Maturity Dates left'])
df_temp = df_temp.reset_index()
df_temp.drop(columns=['index'], inplace=True)
df_swap_rate = []
for index, row in df_temp.iterrows():
    tenor = row['Tenor']
    if pd.isna(row['Maturity Dates']) == False:
        market_quotes = row['Market Quotes']
    elif pd.isna(row['Maturity Dates']) == True:
        market_quotes = row['q']*market_quotes_left + (1-row['q'])*row['Market Quotes right']
    market_quotes_left = market_quotes
    df_swap_rate.append((tenor, market_quotes/100))
df_swap_rate = pd.DataFrame(df_swap_rate, columns=("Tenor","Swap Rates"))

### to obtain DF at the first swap cashflow date through interpolation
swap_cf_date_1 = df_swap_tenor['Tenor'].min()
swap_cf_days_1 = (swap_cf_date_1 - start_date).days/360

df_temp = df_libor_future_df
df_temp['rel_days'] = pd.to_timedelta(df_temp['Maturity Dates'] - swap_cf_date_1).dt.days.astype('int')
df_temp['rel_days_sort'] = df_temp['rel_days'].abs()
df_temp.sort_values(by=['rel_days_sort'], inplace=True)
df_temp = df_temp.head(2)
df_temp = df_temp.sort_values(by=['rel_days'])

q = df_temp.iloc[1,5]/(df_temp.iloc[1,2] - df_temp.iloc[0,2])
temp0 = (1/df_temp.iloc[0,3] - 1)/(df_temp.iloc[0,2]/360)
temp1 = (1/df_temp.iloc[1,3] - 1)/(df_temp.iloc[1,2]/360)
swap_cf_libor_1 = temp0*q + temp1*(1-q)
swap_cf_discount_factor_1 = 1/(1+swap_cf_days_1*swap_cf_libor_1)

### to obtain DF at the rest swap cashflow dates
df_swap_df = [[swap_cf_date_1, swap_cf_discount_factor_1]]
for index, row in df_swap_rate.iterrows():
    if index == 0:
        a = swap_cf_discount_factor_1*(swap_cf_date_1 - start_date).days / 360
        sigma = (row['Tenor'] - swap_cf_date_1).days / 360
        b = row['Tenor']
        discount_factor = (1-row['Swap Rates']*a)/(1+row['Swap Rates']*sigma)
        print(1-row['Swap Rates']*a)
        print(1+row['Swap Rates']*sigma)
    elif index > 0:
        a = a + sigma*discount_factor
        sigma = (row['Tenor'] - b).days / 360
        b = row['Tenor']
        discount_factor = (1 - row['Swap Rates']*a)/(1+row['Swap Rates']*sigma)
    df_swap_df.append((row['Tenor'], discount_factor))

df_swap_df = pd.DataFrame(df_swap_df, columns=("Tenor", "Discount Factor"))

# 3. Discount Factor Curve
df_libor_future_df = df_libor_future_df[['Maturity Dates','discount_factor']].rename(columns={'Maturity Dates':'Tenor', 'discount_factor':'Discount Factor'})

df_curve = pd.concat([df_libor_future_df, df_swap_df]).sort_values(['Tenor']).reset_index().drop(columns=['index'])








