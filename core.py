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


def price_option_with_separate_iv(S0, K, T, r, iv_call, iv_put, paths):
    """
    Price call using call IV and put using put IV separately
    for maximum accuracy matching market prices
    """
    mu = r
    dt = 1/252
    N = max(int(T * 252), 1)

    np.random.seed(42)
    Z = np.random.standard_normal((N, paths))

    # --- CALL PRICING using call IV ---
    S_call = np.zeros((N+1, paths))
    S_call[0] = S0
    for t in range(1, N+1):
        S_call[t] = S_call[t-1] * np.exp((mu - 0.5 * iv_call**2) * dt + iv_call * np.sqrt(dt) * Z[t-1])

    final_prices_call = S_call[-1]
    call_payoffs = np.maximum(final_prices_call - K, 0)
    call_price = np.exp(-r * T) * np.mean(call_payoffs)

    # --- PUT PRICING using put IV ---
    S_put = np.zeros((N+1, paths))
    S_put[0] = S0
    for t in range(1, N+1):
        S_put[t] = S_put[t-1] * np.exp((mu - 0.5 * iv_put**2) * dt + iv_put * np.sqrt(dt) * Z[t-1])

    final_prices_put = S_put[-1]
    put_payoffs = np.maximum(K - final_prices_put, 0)
    put_price = np.exp(-r * T) * np.mean(put_payoffs)

    # --- BLACK-SCHOLES using call IV for call, put IV for put ---
    # Call BS
    d1_call = (math.log(S0/K) + (r + 0.5 * iv_call**2) * T) / (iv_call * math.sqrt(T))
    d2_call = d1_call - iv_call * math.sqrt(T)
    BS_call = S0 * norm.cdf(d1_call) - K * math.exp(-r * T) * norm.cdf(d2_call)

    # Put BS
    d1_put = (math.log(S0/K) + (r + 0.5 * iv_put**2) * T) / (iv_put * math.sqrt(T))
    d2_put = d1_put - iv_put * math.sqrt(T)
    BS_put = K * math.exp(-r * T) * norm.cdf(-d2_put) - S0 * norm.cdf(-d1_put)

    # --- GREEKS using call IV (standard practice) ---
    d1 = d1_call
    d2 = d2_call
    sigma = iv_call

    delta_call = norm.cdf(d1)
    delta_put = norm.cdf(d1) - 1
    gamma = norm.pdf(d1) / (S0 * sigma * math.sqrt(T))
    theta_call = (-(S0 * norm.pdf(d1) * sigma) / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * norm.cdf(d2)) / 252
    theta_put = (-(S0 * norm.pdf(d1) * sigma) / (2 * math.sqrt(T)) + r * K * math.exp(-r * T) * norm.cdf(-d2)) / 252
    vega = S0 * norm.pdf(d1) * math.sqrt(T) / 100

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
        "paths": S_call,
        "final_prices": final_prices_call
    }


def calculate_implied_volatility(market_price, S0, K, T, r, option_type='call'):
    """
    Calculate implied volatility from market price using Newton-Raphson method.
    """
    sigma = 0.20
    max_iterations = 100
    tolerance = 0.0001

    for i in range(max_iterations):
        d1 = (math.log(S0/K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        if option_type == 'call':
            price = S0 * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * math.exp(-r * T) * norm.cdf(-d2) - S0 * norm.cdf(-d1)

        vega = S0 * norm.pdf(d1) * math.sqrt(T)
        diff = price - market_price

        if abs(diff) < tolerance:
            return round(sigma, 4)

        if vega == 0:
            break
        sigma = sigma - diff / vega

        if sigma <= 0:
            sigma = 0.001
        if sigma > 5:
            sigma = 5

    return round(sigma, 4)


def adjust_iv_for_skew(vix, S0, K, T):
    """
    Adjust India VIX for volatility skew.
    """
    moneyness = math.log(K / S0) / math.sqrt(T)
    skew_adjustment = 1 - 0.05 * moneyness - 0.02 * moneyness**2
    skew_adjustment = max(0.80, min(1.20, skew_adjustment))
    adjusted_iv = vix * skew_adjustment
    return round(adjusted_iv, 4)