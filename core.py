# ============================================================
# CORE - Monte Carlo and Black-Scholes pricing engine
# ============================================================

import numpy as np
from scipy.stats import norm
import math

def price_option(S0, K, T, r, sigma, paths):
    """
    Price a European call and put option using Monte Carlo simulation
    and Black-Scholes formula.
    
    Parameters:
    S0    - Current stock/index price
    K     - Strike price
    T     - Time to expiry in years
    r     - Risk free interest rate
    sigma - Annual volatility
    paths - Number of simulation paths
    
    Returns: dictionary with all results
    """

    # --- MONTE CARLO SIMULATION ---
    mu = r
    dt = 1/252
    N = max(int(T * 252), 1)

    np.random.seed(42)
    Z = np.random.standard_normal((N, paths))
    S = np.zeros((N+1, paths))
    S[0] = S0

    for t in range(1, N+1):
        S[t] = S[t-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z[t-1])

    final_prices = S[-1]

    # --- OPTION PRICES ---
    call_payoffs = np.maximum(final_prices - K, 0)
    put_payoffs = np.maximum(K - final_prices, 0)
    call_price = np.exp(-r * T) * np.mean(call_payoffs)
    put_price = np.exp(-r * T) * np.mean(put_payoffs)

    # --- BLACK-SCHOLES ---
    d1 = (math.log(S0/K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    BS_call = S0 * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    BS_put = K * math.exp(-r * T) * norm.cdf(-d2) - S0 * norm.cdf(-d1)

    # --- GREEKS ---
    delta_call = norm.cdf(d1)
    delta_put = norm.cdf(d1) - 1
    gamma = norm.pdf(d1) / (S0 * sigma * math.sqrt(T))
    theta_call = (-(S0 * norm.pdf(d1) * sigma) / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * norm.cdf(d2)) / 252
    theta_put = (-(S0 * norm.pdf(d1) * sigma) / (2 * math.sqrt(T)) + r * K * math.exp(-r * T) * norm.cdf(-d2)) / 252
    vega = S0 * norm.pdf(d1) * math.sqrt(T) / 100

    # --- RETURN ALL RESULTS ---
    return {
        "call_price": call_price,
        "put_price": put_price,
        "BS_call": BS_call,
        "BS_put": BS_put,
        "delta_call": delta_call,
        "delta_put": delta_put,
        "gamma": gamma,
        "theta_call": theta_call,
        "theta_put": theta_put,
        "vega": vega,
        "paths": S,
        "final_prices": final_prices
    }