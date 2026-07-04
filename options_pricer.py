# ============================================================
# OPTIONS PRICER - Terminal Version
# ============================================================

# --- IMPORTS ---
import numpy as np
import matplotlib.pyplot as plt
from market_data import get_nifty_price, get_nifty_volatility, get_next_expiry, get_monthly_expiry
from core import price_option

# --- FETCH MARKET DATA ---
S0 = get_nifty_price()
sigma = get_nifty_volatility()
weekly_date, weekly_T, weekly_days = get_next_expiry()
monthly_date, monthly_T, monthly_days = get_monthly_expiry()

print(f"Current Nifty 50 Price:    ₹{S0}")
print(f"Annual Volatility (sigma): {sigma*100:.2f}%")
print(f"Next Weekly Expiry:  {weekly_date} ({weekly_days} days away)")
print(f"Next Monthly Expiry: {monthly_date} ({monthly_days} days away)")

# --- USER INPUTS ---
print("=" * 45)
print("         NIFTY OPTIONS PRICER")
print("=" * 45)
print("Select Expiry Type:")
print("1. Weekly  (next Thursday)")
print("2. Monthly (last Thursday of month)")
expiry_choice = input("Enter 1 or 2: ")

if expiry_choice == "1":
    expiry_date = weekly_date
    T = weekly_T
    days_remaining = weekly_days
    paths = 100000
elif expiry_choice == "2":
    expiry_date = monthly_date
    T = monthly_T
    days_remaining = monthly_days
    paths = 50000
else:
    print("Invalid choice, defaulting to weekly")
    expiry_date = weekly_date
    T = weekly_T
    days_remaining = weekly_days
    paths = 100000

print(f"\nCurrent Nifty Price: ₹{S0}")
print(f"Suggested Strike:    ₹{round(S0 / 100) * 100 + 500}")
strike_input = input("Enter Strike Price (or press Enter for suggested): ")

if strike_input == "":
    K = round(S0 / 100) * 100 + 500
else:
    K = float(strike_input)

r = 0.065

# --- PRICE OPTION ---
results = price_option(S0, K, T, r, sigma, paths)

# --- SUMMARY ---
print("=" * 45)
print("         OPTIONS PRICER RESULTS")
print("=" * 45)
print(f"Stock Price (S0):       ₹{S0}")
print(f"Strike Price (K):       ₹{K}")
print(f"Volatility (sigma):     {sigma*100:.2f}%")
print(f"Risk Free Rate (r):     {r*100}%")
print(f"Expiry Date:            {expiry_date}")
print(f"Days to Expiry:         {days_remaining} days")
print(f"Simulated Paths:        {paths}")
print("-" * 45)
print(f"Call Option (MC):       ₹{results['call_price']:.2f}")
print(f"Call Option (BS):       ₹{results['BS_call']:.2f}")
print(f"Difference:             ₹{abs(results['BS_call'] - results['call_price']):.2f}")
print("-" * 45)
print(f"Put Option  (MC):       ₹{results['put_price']:.2f}")
print(f"Put Option  (BS):       ₹{results['BS_put']:.2f}")
print(f"Difference:             ₹{abs(results['BS_put'] - results['put_price']):.2f}")
print("=" * 45)
print("-" * 45)
print("            GREEKS")
print("-" * 45)
print(f"Delta (Call):           {results['delta_call']:.4f}")
print(f"Delta (Put):            {results['delta_put']:.4f}")
print(f"Gamma:                  {results['gamma']:.6f}")
print(f"Theta (Call)/day:       ₹{results['theta_call']:.2f}")
print(f"Theta (Put)/day:        ₹{results['theta_put']:.2f}")
print(f"Vega (per 1% vol):      ₹{results['vega']:.2f}")
print("=" * 45)

# --- PLOT ---
plt.figure(figsize=(12, 6))
plt.plot(results['paths'][:, :50], alpha=0.3, linewidth=0.8)
plt.axhline(y=K, color='red', linestyle='--', linewidth=2, label=f'Strike ₹{K}')
plt.axhline(y=S0, color='green', linestyle='--', linewidth=2, label=f'Current ₹{S0}')
plt.title(f'Monte Carlo Simulation - {paths:,} paths')
plt.xlabel('Trading Days')
plt.ylabel('Nifty 50 Price (₹)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()