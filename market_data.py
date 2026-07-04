# ============================================================
# MARKET DATA - Fetch real market data using yfinance
# ============================================================

import yfinance as yf
import numpy as np
from datetime import datetime, timedelta


def get_nifty_price():
    # ^NSEI is the Yahoo Finance ticker for Nifty 50 index
    nifty = yf.Ticker("^NSEI")

    data = nifty.history(period="1d")

    if data.empty:
        data = nifty.history(period="5d")

    if data.empty:
        return 24056.0  # fallback price

    current_price = data['Close'].iloc[-1]
    return round(current_price, 2)


def get_nifty_volatility():
    # Get last 1 year of daily data to calculate volatility
    nifty = yf.Ticker("^NSEI")
    data = nifty.history(period="1y")

    daily_returns = data['Close'].pct_change().dropna()

    annual_volatility = daily_returns.std() * np.sqrt(252)

    return round(annual_volatility, 4)


def get_next_expiry():
    # Nifty 50 weekly options expire every Tuesday (weekday 1)
    # Changed from Thursday to Tuesday by NSE effective September 2025
    today = datetime.now()

    days_until_tuesday = (1 - today.weekday()) % 7

    if days_until_tuesday == 0:
        days_until_tuesday = 7

    next_expiry = today + timedelta(days=days_until_tuesday)

    T = days_until_tuesday / 252

    return next_expiry.strftime("%Y-%m-%d"), T, days_until_tuesday


def get_monthly_expiry():
    today = datetime.now()

    # Find last Tuesday of current month
    if today.month == 12:
        next_month = today.replace(year=today.year+1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month+1, day=1)

    last_day = next_month - timedelta(days=1)

    # Go back to find last Tuesday (weekday 1)
    # Changed from last Thursday to last Tuesday by NSE effective September 2025
    days_back = (last_day.weekday() - 1) % 7
    last_tuesday = last_day - timedelta(days=days_back)

    # If last tuesday already passed this month get next months
    if last_tuesday < today:
        next_month2 = next_month.replace(month=next_month.month+1) if next_month.month < 12 else next_month.replace(year=next_month.year+1, month=1)
        last_day2 = next_month2 - timedelta(days=1)
        days_back2 = (last_day2.weekday() - 1) % 7
        last_tuesday = last_day2 - timedelta(days=days_back2)

    days_remaining = (last_tuesday - today).days
    T = days_remaining / 252

    return last_tuesday.strftime("%Y-%m-%d"), T, days_remaining


def get_banknifty_price():
    # ^NSEBANK is Yahoo Finance ticker for BankNifty
    banknifty = yf.Ticker("^NSEBANK")

    data = banknifty.history(period="1d")

    if data.empty:
        data = banknifty.history(period="5d")

    if data.empty:
        return 55000.0  # fallback price

    current_price = data['Close'].iloc[-1]
    return round(current_price, 2)


def get_banknifty_volatility():
    # Get 1 year of data to calculate annual volatility
    banknifty = yf.Ticker("^NSEBANK")
    data = banknifty.history(period="1y")

    daily_returns = data['Close'].pct_change().dropna()

    annual_volatility = daily_returns.std() * np.sqrt(252)

    return round(annual_volatility, 4)


def get_banknifty_expiry():
    # BankNifty weekly options discontinued November 2024
    # Only monthly expiry remains — last Tuesday of the month
    return get_monthly_expiry()


if __name__ == "__main__":
    # --- TEST NIFTY ---
    price = get_nifty_price()
    volatility = get_nifty_volatility()
    weekly_date, weekly_T, weekly_days = get_next_expiry()
    monthly_date, monthly_T, monthly_days = get_monthly_expiry()

    print(f"Current Nifty 50 Price:    ₹{price}")
    print(f"Annual Volatility (sigma): {volatility*100:.2f}%")
    print(f"Next Weekly Expiry:  {weekly_date} ({weekly_days} days away)")
    print(f"Next Monthly Expiry: {monthly_date} ({monthly_days} days away)")

    # --- TEST BANKNIFTY ---
    bn_price = get_banknifty_price()
    bn_vol = get_banknifty_volatility()
    bn_expiry, bn_T, bn_days = get_banknifty_expiry()

    print(f"\nBankNifty Price:      ₹{bn_price}")
    print(f"BankNifty Volatility: {bn_vol*100:.2f}%")
    print(f"BankNifty Expiry:     {bn_expiry} ({bn_days} days away)")