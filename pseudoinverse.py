# Project: Master Thesis
# Author: Yuanlin Dong
# Date of creation: 2023-04-10

###a refresh to clear all variables before running the script###
from IPython import get_ipython
get_ipython().run_line_magic('reset', '-sf')
###a refresh to clear all variables before running the script###

import pandas as pd
import numpy as np
import scipy

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from functions import *

# 0. set up file path

filepath = '/Users/yuanlindong/Documents/python/masterthesis/input/'
filepath_out = '/Users/yuanlindong/Documents/python/masterthesis/output/'

# 1. import data
df_bond = pd.read_excel(r'/Users/yuanlindong/Documents/python/masterthesis/input/pseudoinverse_data.xlsx', sheet_name='to_python_1')
df = pd.read_excel(r'/Users/yuanlindong/Documents/python/masterthesis/input/pseudoinverse_data.xlsx', sheet_name='to_python_2')
print(df_bond)
print(df)
spot_date = date(1996,9,4)
# kk = df.iloc[9]['cashflow_dates']
# kkk = kk.date()
# test = date(1997,3,26)
# print(kkk == test)

# start_date_array = [[1996,1997,1996,1997,1996,1997,1996,1997,1996], [11,1,9,3,11,2,12,3,10], [15,19,26,3,6,27,7,8,13]]
# end_date_array = [[1996,1998,1999,2000,2001,2002,2005,2006,2008], [11,1,3,3,11,8,12,9,10], [15,19,26,3,6,27,7,8,13]]
# coupon_array = [[5,4.875,6.125,4.5,3.5,4.875,4.25,3.875,4.5]]
# price_array = np.array([103.82,106.04,118.44,106.28,101.15,111.06,106.24,98.49,110.87])
# shape = (9,1)
# price_array = price_array.reshape(shape)

# 2. calculate the cashflow matrix

## process the input bond data
start_date_array = []
end_date_array = []
coupon_array = []
price_array = []
start_date_array.append(df_bond['Next coupon'].dt.year.values.tolist())
start_date_array.append(df_bond['Next coupon'].dt.month.values.tolist())
start_date_array.append(df_bond['Next coupon'].dt.day.values.tolist())
end_date_array.append(df_bond['Maturity'].dt.year.values.tolist())
end_date_array.append(df_bond['Maturity'].dt.month.values.tolist())
end_date_array.append(df_bond['Maturity'].dt.day.values.tolist())
coupon_array.append((0.5*df_bond['Annal coupon (%)']).values.tolist())
price_array = np.array(df_bond['Price'].values.tolist())
shape = (9,1)
price_array = price_array.reshape(shape)

## construct the cashflow matrix

delta = relativedelta(months=6)
cashflow = np.zeros((9,104))
for i in range(0,9):
    start_date = date(start_date_array[0][i], start_date_array[1][i], start_date_array[2][i])
    end_date = date(end_date_array[0][i], end_date_array[1][i], end_date_array[2][i])

    # x = "bond_array_" + str(i)
    list_amount = []
    list_date = []
    number_of_cashflow = 0
    while start_date <= end_date:
        amount = coupon_array[0][i]
        coupon_date = start_date
        number_of_cashflow += 1
        if start_date == end_date:
            amount += 100
        list_amount.append(amount)
        list_date.append(coupon_date)

        start_date += delta
    # globals()[x] = [list_amount, list_date]
    bond_array = [list_amount, list_date]
    # print(bond_array[1][number_of_cashflow-1])
    for j in range(0,number_of_cashflow):
        cashflow_date = bond_array[1][j]
        cashflow_amount = bond_array[0][j]
        for h in range(0,104):
            temp = df.iloc[h]['cashflow_dates']
            if temp.date() == cashflow_date:
                cashflow[i][h] = cashflow_amount
                break

print(cashflow)

# 3. construct W
W_temp = np.zeros((1,104))
for i in range(0,104):
    date_temp = df.iloc[i]['cashflow_dates']
    date_temp_ = date_temp.date()
    year_temp = date_temp_.year
    month_temp = date_temp_.month
    day_temp = date_temp_.day
    if i == 0:
        gamma = (year_temp - spot_date.year) + (month_temp - spot_date.month - 1) / 12 + (min(day_temp, 30) + max(0, 30 - spot_date.day)) / 360
    if i >= 1:
        date_temp_prev = df.iloc[i-1]['cashflow_dates']
        date_temp_prev_ = date_temp_prev.date()
        year_temp_prev = date_temp_prev_.year
        month_temp_prev = date_temp_prev_.month
        day_temp_prev = date_temp_prev_.day
        gamma = (year_temp - year_temp_prev) + (month_temp - month_temp_prev - 1)/12 + (min(day_temp, 30) + max(0, 30 - day_temp_prev))/360

    W_temp[0][i] = 1/np.sqrt(gamma)
W = np.diagflat(W_temp)

# 4. construct M
M_temp = np.ones((1,104))
M = np.diagflat(M_temp)
for i in range(1,104):
    M[i][i-1] = -1

# 5. construct I
I = np.zeros((104,1))
I[0][0] = 1

# 6. calculate the discount curve
M_inv = np.linalg.inv(M)
W_inv = np.linalg.inv(W)

A = np.matmul(np.matmul(cashflow, M_inv), W_inv)
A_trans = A.transpose()
A_A_trans_inv = np.linalg.inv(np.matmul(A, A_trans))
cashflow_M_inv = np.matmul(cashflow, M_inv)
delta_star_1 = np.matmul(A_trans, A_A_trans_inv)
delta_star_2 = np.matmul(cashflow_M_inv, I)
delta_star = np.matmul(delta_star_1, (price_array - delta_star_2))

W_temp_trans = W_temp.transpose()
discount_curve_1 = np.multiply(delta_star, 1/W_temp_trans)
discount_curve = np.zeros((104,1))
for i in range(0,104):
    if i == 0:
        discount_curve[i][0] = 1 + discount_curve_1[i][0]
    if i > 0:
        discount_curve[i][0] = discount_curve[i-1][0] + discount_curve_1[i][0]


# 6. final result
df_temp1 = pd.DataFrame(discount_curve, columns=['Discount Factor'])
df['Tenor'] = df['cashflow_dates'].dt.date
df_curve = pd.concat([df['Tenor'], df_temp1], axis=1)
df_curve.rename(columns={'Tenor': 'Maturity Dates', 'Discount Factor': 'value'}, inplace=True)
df_curve['tenor'] = pd.to_timedelta(df_curve['Maturity Dates'] - spot_date).dt.days.astype('int')
df_curve_daily = create_df_sr_current_daily(df_curve)

# 7. export data to excel for further analysis
filename = "pi_df_curve"
file = filepath_out + filename + ".xlsx"
with pd.ExcelWriter(file) as writer:
    df_curve.to_excel(writer, sheet_name="discount factor table")
    df_curve_daily.to_excel(writer, sheet_name="discount factor curve")

