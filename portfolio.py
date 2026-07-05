# ============================================================
# PORTFOLIO - Portfolio VaR calculation
# ============================================================

import numpy as np
import math
from scipy.stats import norm


def simulate_portfolio_pnl(positions, S0, sigma, T, r, paths=50000):
    """
    Simulate P&L for a portfolio of options positions
    
    Parameters:
    positions - list of dicts, each containing:
        {
            'option_type': 'call' or 'put',
            'strike': float,
            'premium': float,
            'lots': int,
            'lot_size': int,
            'action': 'buy' or 'sell'
        }
    S0    - current index price
    sigma - volatility
    T     - time to expiry in years
    r     - risk free rate
    paths - number of simulation paths
    
    Returns: dict with portfolio risk metrics
    """

    # Simulate future prices
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

    # Calculate P&L for each position
    total_pnl = np.zeros(paths)

    position_results = []

    for pos in positions:
        strike = pos['strike']
        premium = pos['premium']
        lots = pos['lots']
        lot_size = pos['lot_size']
        action = pos['action']
        option_type = pos['option_type']

        # Calculate payoff at expiry
        if option_type == 'call':
            payoff = np.maximum(final_prices - strike, 0)
        else:
            payoff = np.maximum(strike - final_prices, 0)

        # P&L per unit
        if action == 'buy':
            pnl_per_unit = payoff - premium
        else:  # sell
            pnl_per_unit = premium - payoff

        # Total P&L for this position
        position_pnl = pnl_per_unit * lots * lot_size
        total_pnl += position_pnl

        position_results.append({
            'avg_pnl': float(np.mean(position_pnl)),
            'max_pnl': float(np.max(position_pnl)),
            'min_pnl': float(np.min(position_pnl))
        })

    # Portfolio metrics
    var_95 = float(np.percentile(total_pnl, 5))
    var_99 = float(np.percentile(total_pnl, 1))
    cvar_95 = float(np.mean(total_pnl[total_pnl <= var_95]))
    prob_profit = float((total_pnl > 0).sum() / paths * 100)
    max_profit = float(np.max(total_pnl))
    max_loss = float(np.min(total_pnl))
    avg_pnl = float(np.mean(total_pnl))

    return {
        'total_pnl': total_pnl,
        'var_95': var_95,
        'var_99': var_99,
        'cvar_95': cvar_95,
        'prob_profit': prob_profit,
        'max_profit': max_profit,
        'max_loss': max_loss,
        'avg_pnl': avg_pnl,
        'position_results': position_results,
        'final_prices': final_prices
    }