# Project: Master Thesis
# Author: Yuanlin Dong
# Date of creation: 2023-04-27
# Log of changes:
# Date          What


###a refresh to clear all variables before running the script###
from IPython import get_ipython
get_ipython().run_line_magic('reset', '-sf')
###a refresh to clear all variables before running the script###

import numpy as np
from scipy.stats import *
from scipy.optimize import *

from functions import *

# 1. import input data into python

ForwardRates = [0.06, 0.08, 0.09, 0.10, 0.10, 0.10, 0.09, 0.09]
T0 = np.arange(0, 4.5, 0.5)

CapPrices = [0.002, 0.008, 0.012, 0.016]
CapMat = [1, 2, 3, 4]
delta = 0.5

# 2. obtain implied vegas, which are the derivatives of the Black and Bachelier prices with respect to their volatility

## to derive zero rates from observed forward rates
ZeroBondPrices = [1.0] * len(T0)
d1 = [1.0] * 8
for i in range(1, len(ZeroBondPrices)):
    ZeroBondPrices[i] = ZeroBondPrices[i - 1] / (1 + delta * ForwardRates[i - 1])

## to derive the kappa corresponding to each cap
Maturities = [1, 2, 3, 4]
kappa = [0, 0, 0, 0]
for m in Maturities:
    kappa[m - 1] = (ZeroBondPrices[1] - ZeroBondPrices[2 * m]) / (delta * sum(ZeroBondPrices[2:(2 * m + 1)]))

print(ForwardRates, T0, m, delta, ZeroBondPrices, CapPrices, kappa)

## to estimate the implied volatility based on observed cap prices, using the Black and Bachelier pricing formula
impVol = []
for m in range(0, 4):
    BCap = lambda iv: BlackCap(iv, kappa, ForwardRates, T0, m, delta, ZeroBondPrices) - CapPrices[m]
    impVol.append(bisect(BCap, 0.005, 0.25))
    # print(impVol)
print(impVol)

## to calculate the implied vega based on the Black and Bachelier pricing formula and the implied volatility estimated in the last step
## the implied vega is the derivations of the Black and Bachelier prices with respect to their volatilities
Vegas = []
for m in range(0, 4):
    Vegas.append(BlackVega(delta, ZeroBondPrices, ForwardRates, T0, impVol[m], m, kappa))
    # print(Vegas)
print(Vegas)

# 3. estimate the diffusion term through running the optimization algorithm on the objective function -
#   sum of the square of pricing error weighted by the implied vega
def objectiveFunction(par):
    b = par[0]
    nu = par[1]
    myAns = 0
    for m in range(4):
        Cn_model = CapVasicek(b, nu, kappa, ForwardRates, T0, m, delta, ZeroBondPrices)
        myAns = myAns + (1 / Vegas[m] ** 2) * (Cn_model - CapPrices[m]) ** 2
    return myAns

_result = minimize(objectiveFunction, x0=[0.1, 0.03])
print(_result)