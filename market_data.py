# ============================================================
# MARKET DATA - Fetch real market data using yfinance and NSE
# ============================================================

import yfinance as yf
import numpy as np
import requests
import re
from datetime import datetime, timedelta
import pytz


def get_nifty_price():
    nifty = yf.Ticker("^NSEI")
    data = nifty.history(period="1d")
    if data.empty:
        data = nifty.history(period="5d")
    if data.empty:
        return None
    return round(data['Close'].iloc[-1], 2)


def get_nifty_volatility():
    nifty = yf.Ticker("^NSEI")
    data = nifty.history(period="1y")
    if data.empty:
        return None
    daily_returns = data['Close'].pct_change().dropna()
    if daily_returns.empty or daily_returns.std() == 0:
        return None
    return round(daily_returns.std() * np.sqrt(252), 4)


def get_india_vix():
    try:
        vix = yf.Ticker("^INDIAVIX")
        data = vix.history(period="1d")
        if data.empty:
            data = vix.history(period="5d")
        if data.empty:
            return None
        return round(data['Close'].iloc[-1] / 100, 4)
    except:
        return None


def get_rbi_rate():
    """Fetch current RBI repo rate from RBI website"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(
            'https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=62514',
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            matches = re.findall(r'repo rate.*?(\d+\.\d+)\s*per cent', response.text, re.IGNORECASE)
            if matches:
                return round(float(matches[0]) / 100, 4)
        return None
    except:
        return None


def get_next_expiry():
    today = datetime.now()
    days_until_tuesday = (1 - today.weekday()) % 7
    if days_until_tuesday == 0:
        days_until_tuesday = 7
    next_expiry = today + timedelta(days=days_until_tuesday)
    T = days_until_tuesday / 252
    return next_expiry.strftime("%Y-%m-%d"), T, days_until_tuesday


def get_monthly_expiry():
    today = datetime.now()
    if today.month == 12:
        next_month = today.replace(year=today.year+1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month+1, day=1)
    last_day = next_month - timedelta(days=1)
    days_back = (last_day.weekday() - 1) % 7
    last_tuesday = last_day - timedelta(days=days_back)
    if last_tuesday < today:
        next_month2 = next_month.replace(month=next_month.month+1) if next_month.month < 12 else next_month.replace(year=next_month.year+1, month=1)
        last_day2 = next_month2 - timedelta(days=1)
        days_back2 = (last_day2.weekday() - 1) % 7
        last_tuesday = last_day2 - timedelta(days=days_back2)
    days_remaining = (last_tuesday - today).days
    T = days_remaining / 252
    return last_tuesday.strftime("%Y-%m-%d"), T, days_remaining


def get_banknifty_price():
    banknifty = yf.Ticker("^NSEBANK")
    data = banknifty.history(period="1d")
    if data.empty:
        data = banknifty.history(period="5d")
    if data.empty:
        return None
    return round(data['Close'].iloc[-1], 2)


def get_banknifty_volatility():
    banknifty = yf.Ticker("^NSEBANK")
    data = banknifty.history(period="1y")
    if data.empty:
        return None
    daily_returns = data['Close'].pct_change().dropna()
    if daily_returns.empty or daily_returns.std() == 0:
        return None
    return round(daily_returns.std() * np.sqrt(252), 4)


def get_banknifty_expiry():
    return get_monthly_expiry()


def get_finnifty_price():
    finnifty = yf.Ticker("NIFTY_FIN_SERVICE.NS")
    data = finnifty.history(period="1d")
    if data.empty:
        data = finnifty.history(period="5d")
    if data.empty:
        return None
    return round(data['Close'].iloc[-1], 2)


def get_finnifty_volatility():
    finnifty = yf.Ticker("NIFTY_FIN_SERVICE.NS")
    data = finnifty.history(period="1y")
    if data.empty:
        return get_india_vix()
    daily_returns = data['Close'].pct_change().dropna()
    if daily_returns.empty or daily_returns.std() == 0:
        return get_india_vix()
    return round(daily_returns.std() * np.sqrt(252), 4)


def get_finnifty_expiry():
    return get_monthly_expiry()


def get_midcap_price():
    midcap = yf.Ticker("NIFTY_MID_SELECT.NS")
    data = midcap.history(period="1d")
    if data.empty:
        data = midcap.history(period="5d")
    if data.empty:
        return None
    return round(data['Close'].iloc[-1], 2)


def get_midcap_volatility():
    try:
        midcap = yf.Ticker("NIFTY_MID_SELECT.NS")
        data = midcap.history(period="1y")
        if data.empty or len(data) < 30:
            return get_india_vix()
        daily_returns = data['Close'].pct_change().dropna()
        if daily_returns.empty or daily_returns.std() == 0:
            return get_india_vix()
        return round(daily_returns.std() * np.sqrt(252), 4)
    except:
        return get_india_vix()


def get_midcap_expiry():
    return get_monthly_expiry()


def get_market_status():
    try:
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        if now.weekday() >= 5:
            return {
                'is_open': False,
                'status': '🔴 Market Closed',
                'message': 'Market reopens Monday 9:15am IST',
                'color': 'red'
            }
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        if market_open <= now <= market_close:
            return {
                'is_open': True,
                'status': '🟢 Market Open',
                'message': 'Closes at 3:30pm IST',
                'color': 'green'
            }
        elif now < market_open:
            return {
                'is_open': False,
                'status': '🟡 Market Opens Soon',
                'message': 'Opens at 9:15am IST today',
                'color': 'yellow'
            }
        else:
            return {
                'is_open': False,
                'status': '🔴 Market Closed',
                'message': 'Market reopens tomorrow 9:15am IST',
                'color': 'red'
            }
    except:
        return {
            'is_open': False,
            'status': '⚪ Market Status Unknown',
            'message': '',
            'color': 'gray'
        }


def convert_date_to_nse_format(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%d-%b-%Y")


def _get_nse_session():
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.nseindia.com/option-chain',
        'Connection': 'keep-alive',
    }
    session.get('https://www.nseindia.com', headers=headers, timeout=10)
    session.get('https://www.nseindia.com/option-chain', headers=headers, timeout=10)
    return session, headers


def get_nse_option_chain(symbol="NIFTY"):
    """Fetch NSE option chain using old REST API — fallback only"""
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
        print(f"NSE REST API error: {e}")
        return None


def get_nse_option_chain_live(symbol="NIFTY"):
    """
    Fetch live NSE option chain using NseIndiaApi
    Returns full data including bid/ask prices and NSE IV
    """
    try:
        from nse import NSE
        import time
        with NSE(download_folder='./', server=True, timeout=30) as nse:
            data = None
            for attempt in range(3):
                try:
                    data = nse.optionChain(symbol=symbol.lower())
                    if data:
                        break
                except Exception as e:
                    print(f"  Attempt {attempt+1} failed: {e}")
                    if attempt < 2:
                        time.sleep(3)

            if not data or 'records' not in data:
                return None

            # Flatten records into a list with CE/PE separated
            records = data['records']['data']
            flattened = []

            for record in records:
                expiry = record.get('expiryDates', '')
                strike = float(record.get('strikePrice', 0))

                if 'CE' in record and record['CE']:
                    ce = record['CE']
                    flattened.append({
                        'strikePrice': str(strike),
                        'expiryDate': ce.get('expiryDate', expiry).replace('-', '-'),
                        'optionType': 'CE',
                        'lastPrice': float(ce.get('lastPrice', 0)),
                        'openInterest': int(ce.get('openInterest', 0)),
                        'totalTradedVolume': int(ce.get('totalTradedVolume', 0)),
                        'change': float(ce.get('change', 0)),
                        'pChange': float(ce.get('pChange', 0)),
                        'impliedVolatility': float(ce.get('impliedVolatility', 0)),
                        'buyPrice1': float(ce.get('buyPrice1', 0)),
                        'sellPrice1': float(ce.get('sellPrice1', 0)),
                        'buyQuantity1': int(ce.get('buyQuantity1', 0)),
                        'sellQuantity1': int(ce.get('sellQuantity1', 0)),
                    })

                if 'PE' in record and record['PE']:
                    pe = record['PE']
                    flattened.append({
                        'strikePrice': str(strike),
                        'expiryDate': pe.get('expiryDate', expiry).replace('-', '-'),
                        'optionType': 'PE',
                        'lastPrice': float(pe.get('lastPrice', 0)),
                        'openInterest': int(pe.get('openInterest', 0)),
                        'totalTradedVolume': int(pe.get('totalTradedVolume', 0)),
                        'change': float(pe.get('change', 0)),
                        'pChange': float(pe.get('pChange', 0)),
                        'impliedVolatility': float(pe.get('impliedVolatility', 0)),
                        'buyPrice1': float(pe.get('buyPrice1', 0)),
                        'sellPrice1': float(pe.get('sellPrice1', 0)),
                        'buyQuantity1': int(pe.get('buyQuantity1', 0)),
                        'sellQuantity1': int(pe.get('sellQuantity1', 0)),
                    })

            return flattened

    except Exception as e:
        print(f"NseIndiaApi error: {e}")
        return None


def _process_option_entry(entry, last_price_key='lastPrice'):
    """
    Process a raw option entry into standardized format
    Works for both NseIndiaApi and REST API formats
    Uses midpoint price when bid/ask available
    Assesses data quality
    """
    last_price = float(entry.get('lastPrice', entry.get('last_price', 0)))
    bid_price = float(entry.get('buyPrice1', entry.get('bid_price', 0)))
    ask_price = float(entry.get('sellPrice1', entry.get('ask_price', 0)))
    volume = int(entry.get('totalTradedVolume', entry.get('volume', 0)))
    open_interest = int(entry.get('openInterest', entry.get('open_interest', 0)))
    nse_iv_raw = float(entry.get('impliedVolatility', entry.get('nse_iv', 0)))

    # Normalize NSE IV — NSE returns it as percentage (e.g. 10.5 means 10.5%)
    nse_iv = nse_iv_raw / 100 if nse_iv_raw > 1 else nse_iv_raw

    # Use midpoint if valid
    if bid_price > 0 and ask_price > 0 and ask_price > bid_price:
        mid_price = (bid_price + ask_price) / 2
        spread_pct = (ask_price - bid_price) / last_price * 100 if last_price > 0 else 100
    else:
        mid_price = last_price
        spread_pct = None

    # Data quality assessment
    data_quality = "good"
    quality_notes = []

    if volume < 100:
        data_quality = "poor"
        quality_notes.append("low volume")
    if open_interest == 0:
        data_quality = "poor"
        quality_notes.append("zero OI")
    if spread_pct and spread_pct > 10:
        data_quality = "poor"
        quality_notes.append(f"wide spread {spread_pct:.1f}%")

    return {
        'lastPrice': last_price,
        'midPrice': mid_price,
        'bidPrice': bid_price,
        'askPrice': ask_price,
        'spreadPct': spread_pct,
        'openInterest': open_interest,
        'volume': volume,
        'change': float(entry.get('change', 0)),
        'pchange': float(entry.get('pChange', entry.get('pchange', 0))),
        'nseIV': nse_iv,
        'dataQuality': data_quality,
        'qualityNotes': quality_notes,
    }


def get_nse_option_price(symbol, strike, expiry_date, option_type='CE'):
    """
    Fetch real market price for a specific NSE option
    Priority: NseIndiaApi (live, has bid/ask) → REST API → Supabase cache
    """
    # Convert expiry_date format for matching
    # expiry_date comes in as "28-Jul-2026"
    # NseIndiaApi returns expiryDate as "28-07-2026" or "28-Jul-2026"

    try:
        # Try NseIndiaApi first — has bid/ask and NSE IV
        chain = get_nse_option_chain_live(symbol)

        if chain:
            for entry in chain:
                entry_strike = float(entry['strikePrice'])
                entry_type = entry['optionType']
                entry_expiry_raw = entry['expiryDate']

                # Normalize expiry date format for comparison
                try:
                    # Try parsing as DD-MM-YYYY
                    dt = datetime.strptime(entry_expiry_raw, "%d-%m-%Y")
                    entry_expiry_normalized = dt.strftime("%d-%b-%Y")
                except:
                    try:
                        # Try parsing as DD-Mon-YYYY
                        dt = datetime.strptime(entry_expiry_raw, "%d-%b-%Y")
                        entry_expiry_normalized = entry_expiry_raw
                    except:
                        entry_expiry_normalized = entry_expiry_raw

                if (entry_strike == float(strike) and
                    entry_expiry_normalized == expiry_date and
                    entry_type == option_type):

                    result = _process_option_entry(entry)
                    result['source'] = 'live'
                    return result

    except Exception as e:
        print(f"NseIndiaApi fetch failed: {e}")

    # Fallback to REST API
    try:
        chain = get_nse_option_chain(symbol)
        if chain:
            for entry in chain:
                entry_strike = float(entry['strikePrice'].strip())
                entry_expiry = entry['expiryDate']
                entry_type = entry['optionType']

                if (entry_strike == float(strike) and
                    entry_expiry == expiry_date and
                    entry_type == option_type):

                    result = _process_option_entry(entry)
                    result['source'] = 'live'
                    return result
    except Exception as e:
        print(f"REST API fetch failed: {e}")

    # Final fallback — Supabase cache
    print("Trying Supabase cache...")
    return get_option_price_from_supabase(symbol, strike, expiry_date, option_type)


def get_option_price_from_supabase(symbol, strike, expiry_date, option_type='CE'):
    """
    Fetch option price from Supabase cache
    Uses midpoint price when bid/ask available
    Returns NSE IV directly
    """
    try:
        import os
        SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://mmmkqwuvzdysetroovhv.supabase.co")
        SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_QxjC-OlwafscoTdoOa06OQ_W6J_5H0O")

        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }

        params = {
            'symbol': f'eq.{symbol}',
            'strike': f'eq.{float(strike)}',
            'expiry_date': f'eq.{expiry_date}',
            'option_type': f'eq.{option_type}',
            'select': '*'
        }

        url = f"{SUPABASE_URL}/rest/v1/option_chain"
        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                row = data[0]

                entry = {
                    'lastPrice': float(row['last_price']),
                    'buyPrice1': float(row.get('bid_price', 0)),
                    'sellPrice1': float(row.get('ask_price', 0)),
                    'openInterest': int(row.get('open_interest', 0)),
                    'totalTradedVolume': int(row.get('volume', 0)),
                    'change': float(row.get('change', 0)),
                    'pChange': float(row.get('pchange', 0)),
                    'impliedVolatility': float(row.get('nse_iv', 0)),
                }

                result = _process_option_entry(entry)
                result['updated_at'] = row['updated_at']
                result['source'] = 'supabase'

                # Convert IST timestamp for display
                try:
                    updated_utc = row['updated_at']
                    dt = datetime.fromisoformat(updated_utc.replace('Z', '+00:00'))
                    ist = pytz.timezone('Asia/Kolkata')
                    dt_ist = dt.astimezone(ist)
                    result['updated_at'] = dt_ist.strftime('%Y-%m-%dT%H:%M')
                except:
                    result['updated_at'] = row['updated_at'][:16]

                return result
        return None

    except Exception as e:
        print(f"Supabase fetch error: {e}")
        return None


def get_all_options_from_supabase(symbol, expiry_date):
    """
    Fetch all option strikes for a symbol and expiry from Supabase
    """
    try:
        import os
        SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://mmmkqwuvzdysetroovhv.supabase.co")
        SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_QxjC-OlwafscoTdoOa06OQ_W6J_5H0O")

        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }

        params = {
            'symbol': f'eq.{symbol}',
            'expiry_date': f'eq.{expiry_date}',
            'select': '*',
            'order': 'strike.asc'
        }

        url = f"{SUPABASE_URL}/rest/v1/option_chain"
        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            return response.json()
        return []

    except Exception as e:
        print(f"Supabase fetch error: {e}")
        return []


def get_expiry_dates_from_supabase(symbol):
    """
    Fetch all available expiry dates for a symbol from Supabase
    """
    try:
        import os
        SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://mmmkqwuvzdysetroovhv.supabase.co")
        SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_QxjC-OlwafscoTdoOa06OQ_W6J_5H0O")

        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }

        params = {
            'symbol': f'eq.{symbol}',
            'select': 'expiry_date',
            'order': 'expiry_date.asc'
        }

        url = f"{SUPABASE_URL}/rest/v1/option_chain"
        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            expiries = sorted(list(set([row['expiry_date'] for row in data])))
            return expiries
        return []

    except Exception as e:
        print(f"Supabase expiry fetch error: {e}")
        return []


if __name__ == "__main__":
    price = get_nifty_price()
    volatility = get_nifty_volatility()
    india_vix = get_india_vix()
    rbi_rate = get_rbi_rate()
    weekly_date, weekly_T, weekly_days = get_next_expiry()
    monthly_date, monthly_T, monthly_days = get_monthly_expiry()

    print(f"Current Nifty 50 Price:    ₹{price}")
    print(f"Annual Volatility (sigma): {volatility*100:.2f}%" if volatility else "Volatility: unavailable")
    print(f"India VIX:                 {india_vix*100:.2f}%" if india_vix else "India VIX: unavailable")
    print(f"RBI Rate:                  {rbi_rate*100:.2f}%" if rbi_rate else "RBI Rate: unavailable")
    print(f"Next Weekly Expiry:  {weekly_date} ({weekly_days} days away)")
    print(f"Next Monthly Expiry: {monthly_date} ({monthly_days} days away)")

    bn_price = get_banknifty_price()
    bn_vol = get_banknifty_volatility()
    print(f"\nBankNifty Price:      ₹{bn_price}")
    print(f"BankNifty Volatility: {bn_vol*100:.2f}%" if bn_vol else "BankNifty Volatility: unavailable")

    finnifty_price = get_finnifty_price()
    finnifty_vol = get_finnifty_volatility()
    midcap_price = get_midcap_price()
    midcap_vol = get_midcap_volatility()

    print(f"\nFinNifty Price:      ₹{finnifty_price}")
    print(f"FinNifty Volatility: {finnifty_vol*100:.2f}%" if finnifty_vol else "FinNifty Volatility: unavailable")
    print(f"MidcapNifty Price:      ₹{midcap_price}")
    print(f"MidcapNifty Volatility: {midcap_vol*100:.2f}%" if midcap_vol else "MidcapNifty Volatility: unavailable")

    print("\nTesting NSE option price fetch...")
    expiries = get_expiry_dates_from_supabase("NIFTY")
    print(f"Available expiries: {expiries}")

    if expiries:
        test_expiry = expiries[0]
        call = get_nse_option_price("NIFTY", 24800, test_expiry, "CE")
        put = get_nse_option_price("NIFTY", 24800, test_expiry, "PE")

        if call:
            print(f"\nNifty 24800 CE ({test_expiry}):")
            print(f"  LTP:     ₹{call['lastPrice']}")
            print(f"  Mid:     ₹{call['midPrice']:.2f}")
            print(f"  Bid/Ask: ₹{call['bidPrice']} / ₹{call['askPrice']}")
            print(f"  NSE IV:  {call['nseIV']*100:.2f}%")
            print(f"  Quality: {call['dataQuality']}")
            print(f"  Source:  {call['source']}")

        if put:
            print(f"\nNifty 24800 PE ({test_expiry}):")
            print(f"  LTP:     ₹{put['lastPrice']}")
            print(f"  Mid:     ₹{put['midPrice']:.2f}")
            print(f"  Bid/Ask: ₹{put['bidPrice']} / ₹{put['askPrice']}")
            print(f"  NSE IV:  {put['nseIV']*100:.2f}%")
            print(f"  Quality: {put['dataQuality']}")
            print(f"  Source:  {put['source']}")