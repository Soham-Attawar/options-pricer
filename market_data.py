# ============================================================
# MARKET DATA - Fetch real Nifty 50 price using yfinance
# ============================================================

import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
from datetime import datetime, timedelta

def get_nifty_price():
    # ^NSEI is the Yahoo Finance ticker for Nifty 50 index
    nifty = yf.Ticker("^NSEI")
    
    # Get the latest price data
    data = nifty.history(period="1d")
    
    # Extract the closing price
    current_price = data['Close'].iloc[-1]
    
    return round(current_price, 2)

def get_nifty_volatility():
    # Get last 1 year of daily data to calculate volatility
    nifty = yf.Ticker("^NSEI")
    data = nifty.history(period="1y")
    
    # Calculate daily returns
    daily_returns = data['Close'].pct_change().dropna()
    
    # Annualize volatility (multiply by sqrt of 252 trading days)
    annual_volatility = daily_returns.std() * np.sqrt(252)
    
    return round(annual_volatility, 4)

def get_next_expiry():
    today = datetime.now()
    
    # Find days until next Thursday (weekday 3 = Thursday)
    days_until_thursday = (3 - today.weekday()) % 7
    
    # If today is Thursday, get next Thursday
    if days_until_thursday == 0:
        days_until_thursday = 7
    
    # Calculate next expiry date
    next_expiry = today + timedelta(days=days_until_thursday)
    
    # Calculate T (time to expiry in years)
    T = days_until_thursday / 252
    
    return next_expiry.strftime("%Y-%m-%d"), T, days_until_thursday

def get_monthly_expiry():
    today = datetime.now()
    
    # Find last Thursday of current month
    # Start from last day of month and go backwards
    if today.month == 12:
        next_month = today.replace(year=today.year+1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month+1, day=1)
    
    last_day = next_month - timedelta(days=1)
    
    # Go back to find last Thursday
    days_back = (last_day.weekday() - 3) % 7
    last_thursday = last_day - timedelta(days=days_back)
    
    # If last thursday already passed this month get next months
    if last_thursday < today:
        next_month2 = next_month.replace(month=next_month.month+1) if next_month.month < 12 else next_month.replace(year=next_month.year+1, month=1)
        last_day2 = next_month2 - timedelta(days=1)
        days_back2 = (last_day2.weekday() - 3) % 7
        last_thursday = last_day2 - timedelta(days=days_back2)
    
    days_remaining = (last_thursday - today).days
    T = days_remaining / 252
    
    return last_thursday.strftime("%Y-%m-%d"), T, days_remaining

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
    # BankNifty expires every Wednesday (weekday 2)
    today = datetime.now()

    days_until_wednesday = (2 - today.weekday()) % 7

    if days_until_wednesday == 0:
        days_until_wednesday = 7

    next_expiry = today + timedelta(days=days_until_wednesday)
    T = days_until_wednesday / 252

    return next_expiry.strftime("%Y-%m-%d"), T, days_until_wednesday

if __name__ == "__main__":
    # --- RUN ---
    price = get_nifty_price()
    volatility = get_nifty_volatility()

    weekly_date, weekly_T, weekly_days = get_next_expiry()
    monthly_date, monthly_T, monthly_days = get_monthly_expiry()

    # --- TEST BANKNIFTY ---
    bn_price = get_banknifty_price()
    bn_vol = get_banknifty_volatility()
    bn_expiry, bn_T, bn_days = get_banknifty_expiry()

    print(f"BankNifty Price:      ₹{bn_price}")
    print(f"BankNifty Volatility: {bn_vol*100:.2f}%")
    print(f"Next Expiry:          {bn_expiry} ({bn_days} days away)")