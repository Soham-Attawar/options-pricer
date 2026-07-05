# ============================================================
# MARKET DATA - Fetch real market data using yfinance and NSE
# ============================================================

import yfinance as yf
import numpy as np
import requests
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


def get_india_vix():
    """
    Fetch India VIX — NSE's official volatility index
    Represents market's expected volatility for next 30 days
    Much better than historical volatility for options pricing
    """
    try:
        vix = yf.Ticker("^INDIAVIX")
        data = vix.history(period="1d")

        if data.empty:
            data = vix.history(period="5d")

        if data.empty:
            return None

        # VIX is already in percentage — convert to decimal
        vix_value = data['Close'].iloc[-1] / 100
        return round(vix_value, 4)

    except:
        return None


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


def _get_nse_session():
    """
    Create a session with NSE cookies
    Required before any NSE API call
    """
    session = requests.Session()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.nseindia.com/option-chain',
        'Connection': 'keep-alive',
    }

    # Get cookies from main page first
    session.get('https://www.nseindia.com', headers=headers, timeout=10)
    session.get('https://www.nseindia.com/option-chain', headers=headers, timeout=10)

    return session, headers


def get_nse_option_chain(symbol="NIFTY"):
    """
    Fetch full NSE option chain for a symbol
    Returns raw data list or None if failed
    """
    try:
        session, headers = _get_nse_session()

        url = f'https://www.nseindia.com/api/NextApi/apiClient/GetQuoteApi?functionName=getSymbolDerivativesData&symbol={symbol}'
        response = session.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()

        if not data or 'data' not in data:
            return None

        return data['data']

    except Exception as e:
        print(f"NSE option chain fetch error: {e}")
        return None


def get_nse_option_price(symbol, strike, expiry_date, option_type='CE'):
    """
    Fetch real market price for a specific NSE option

    Parameters:
    symbol      - "NIFTY" or "BANKNIFTY"
    strike      - strike price (e.g. 24800)
    expiry_date - expiry date string from NSE (e.g. "07-Jul-2026")
    option_type - "CE" for call, "PE" for put

    Returns: dict with lastPrice, OI, volume etc or None if failed
    """
    try:
        chain = get_nse_option_chain(symbol)

        if not chain:
            return None

        for entry in chain:
            entry_strike = float(entry['strikePrice'].strip())
            entry_expiry = entry['expiryDate']
            entry_type = entry['optionType']

            if (entry_strike == float(strike) and
                entry_expiry == expiry_date and
                entry_type == option_type):
                return {
                    'lastPrice': entry['lastPrice'],
                    'openInterest': entry['openInterest'],
                    'volume': entry['totalTradedVolume'],
                    'high': entry['highPrice'],
                    'low': entry['lowPrice'],
                    'change': entry['change'],
                    'pchange': entry['pchange']
                }

        return None

    except Exception as e:
        print(f"NSE option price fetch error: {e}")
        return None


def get_nse_expiry_dates(symbol="NIFTY"):
    """
    Get all available expiry dates from NSE option chain
    Returns sorted list of expiry date strings
    """
    try:
        chain = get_nse_option_chain(symbol)

        if not chain:
            return []

        expiries = sorted(list(set([e['expiryDate'] for e in chain])))
        return expiries

    except Exception as e:
        print(f"NSE expiry dates fetch error: {e}")
        return []


def get_nse_strikes(symbol="NIFTY", expiry_date=None):
    """
    Get all available strike prices for a symbol and expiry
    Returns sorted list of strike prices
    """
    try:
        chain = get_nse_option_chain(symbol)

        if not chain:
            return []

        if expiry_date:
            strikes = sorted(list(set([
                float(e['strikePrice'].strip())
                for e in chain
                if e['expiryDate'] == expiry_date
            ])))
        else:
            strikes = sorted(list(set([
                float(e['strikePrice'].strip())
                for e in chain
            ])))

        return strikes

    except Exception as e:
        print(f"NSE strikes fetch error: {e}")
        return []
    
def convert_date_to_nse_format(date_str):
    """
    Convert date from YYYY-MM-DD to DD-Mon-YYYY format
    Example: 2026-07-28 → 28-Jul-2026
    """
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%d-%b-%Y")


if __name__ == "__main__":
    # --- TEST NIFTY ---
    price = get_nifty_price()
    volatility = get_nifty_volatility()
    india_vix = get_india_vix()
    weekly_date, weekly_T, weekly_days = get_next_expiry()
    monthly_date, monthly_T, monthly_days = get_monthly_expiry()

    print(f"Current Nifty 50 Price:    ₹{price}")
    print(f"Annual Volatility (sigma): {volatility*100:.2f}%")
    print(f"India VIX:                 {india_vix*100:.2f}%" if india_vix else "India VIX: unavailable")
    print(f"Next Weekly Expiry:  {weekly_date} ({weekly_days} days away)")
    print(f"Next Monthly Expiry: {monthly_date} ({monthly_days} days away)")

    # --- TEST BANKNIFTY ---
    bn_price = get_banknifty_price()
    bn_vol = get_banknifty_volatility()
    bn_expiry, bn_T, bn_days = get_banknifty_expiry()

    print(f"\nBankNifty Price:      ₹{bn_price}")
    print(f"BankNifty Volatility: {bn_vol*100:.2f}%")
    print(f"BankNifty Expiry:     {bn_expiry} ({bn_days} days away)")

    # --- TEST NSE OPTION CHAIN ---
    print("\nFetching NSE option chain...")
    expiries = get_nse_expiry_dates("NIFTY")
    print(f"Available expiries: {expiries}")

    if expiries:
        # Find nearest expiry (July 7)
        nearest_expiry = "07-Jul-2026"
        
        call = get_nse_option_price("NIFTY", 24800, nearest_expiry, "CE")
        put = get_nse_option_price("NIFTY", 24800, nearest_expiry, "PE")

        if call:
            print(f"\nNifty 24800 CE ({nearest_expiry}):")
            print(f"  LTP:    ₹{call['lastPrice']}")
            print(f"  OI:     {call['openInterest']}")
            print(f"  Volume: {call['volume']}")
        else:
            print(f"\nCall not found for {nearest_expiry}")

        if put:
            print(f"\nNifty 24800 PE ({nearest_expiry}):")
            print(f"  LTP:    ₹{put['lastPrice']}")
            print(f"  OI:     {put['openInterest']}")
            print(f"  Volume: {put['volume']}")
        else:
            print(f"\nPut not found for {nearest_expiry}")

        # Also test monthly expiry
        monthly_expiry = "28-Jul-2026"
        call_monthly = get_nse_option_price("NIFTY", 24800, monthly_expiry, "CE")
        
        if call_monthly:
            print(f"\nNifty 24800 CE ({monthly_expiry}):")
            print(f"  LTP:    ₹{call_monthly['lastPrice']}")