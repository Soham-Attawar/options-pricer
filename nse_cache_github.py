# ============================================================
# NSE CACHE - GitHub Actions version using NseIndiaApi
# ============================================================

import requests
import os
import json
from datetime import datetime
from nse import NSE

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def get_nse_option_chain(symbol="NIFTY"):
    """Fetch NSE option chain using NseIndiaApi with server=True"""
    try:
        print(f"Fetching {symbol} from NSE using NseIndiaApi...")
        
        with NSE(download_folder='./', server=True) as nse:
            data = nse.optionChain(symbol=symbol.lower())
            
        if not data or 'records' not in data:
            print(f"No data returned for {symbol}")
            return []
            
        records = data['records']['data']
        print(f"Got {len(records)} records for {symbol}")
        return records

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return []


def save_to_supabase(symbol, records):
    """Save option chain to Supabase"""
    if not records:
        print(f"No data to save for {symbol}")
        return

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }

    # Delete old data for this symbol
    delete_response = requests.delete(
        f"{SUPABASE_URL}/rest/v1/option_chain?symbol=eq.{symbol}",
        headers=headers,
        timeout=10
    )
    print(f"Delete old data: status {delete_response.status_code}")

    # Prepare rows from NseIndiaApi format
    rows = []
    for record in records:
        expiry = record.get('expiryDates', '')

        # Process CE (Call)
        if 'CE' in record and record['CE']:
            ce = record['CE']
            try:
                rows.append({
                    "symbol": symbol,
                    "strike": float(ce.get('strikePrice', 0)),
                    "expiry_date": expiry,
                    "option_type": "CE",
                    "last_price": float(ce.get('lastPrice', 0)),
                    "open_interest": int(ce.get('openInterest', 0)),
                    "volume": int(ce.get('totalTradedVolume', 0)),
                    "change": float(ce.get('change', 0)),
                    "pchange": float(ce.get('pChange', 0)),
                    "implied_volatility": float(ce.get('impliedVolatility', 0)),
                    "updated_at": datetime.now().isoformat()
                })
            except:
                continue

        # Process PE (Put)
        if 'PE' in record and record['PE']:
            pe = record['PE']
            try:
                rows.append({
                    "symbol": symbol,
                    "strike": float(pe.get('strikePrice', 0)),
                    "expiry_date": expiry,
                    "option_type": "PE",
                    "last_price": float(pe.get('lastPrice', 0)),
                    "open_interest": int(pe.get('openInterest', 0)),
                    "volume": int(pe.get('totalTradedVolume', 0)),
                    "change": float(pe.get('change', 0)),
                    "pchange": float(pe.get('pChange', 0)),
                    "implied_volatility": float(pe.get('impliedVolatility', 0)),
                    "updated_at": datetime.now().isoformat()
                })
            except:
                continue

    print(f"Prepared {len(rows)} rows for {symbol}")

    # Insert in batches of 100
    for i in range(0, len(rows), 100):
        batch = rows[i:i+100]
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/option_chain",
            headers=headers,
            json=batch,
            timeout=10
        )
        print(f"Insert batch {i//100 + 1}: status {response.status_code}")

    print(f"Successfully saved {len(rows)} rows for {symbol}")


# --- MAIN ---
print(f"NSE Cache GitHub Actions — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"SUPABASE_URL: {'SET' if SUPABASE_URL else 'NOT SET'}")
print(f"SUPABASE_KEY: {'SET' if SUPABASE_KEY else 'NOT SET'}")

nifty_records = get_nse_option_chain("NIFTY")
if nifty_records:
    save_to_supabase("NIFTY", nifty_records)

banknifty_records = get_nse_option_chain("BANKNIFTY")
if banknifty_records:
    save_to_supabase("BANKNIFTY", banknifty_records)

print("Done!")