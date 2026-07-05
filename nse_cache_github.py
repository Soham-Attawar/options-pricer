# ============================================================
# NSE CACHE - GitHub Actions version
# Fetches NSE data and saves to Supabase
# ============================================================

import requests
import os
import json
from datetime import datetime

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def get_nse_option_chain(symbol="NIFTY"):
    """Fetch NSE option chain"""
    try:
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.nseindia.com/option-chain',
            'Connection': 'keep-alive',
        }

        print(f"Fetching {symbol} from NSE...")
        session.get('https://www.nseindia.com', headers=headers, timeout=15)
        session.get('https://www.nseindia.com/option-chain', headers=headers, timeout=15)

        url = f'https://www.nseindia.com/api/NextApi/apiClient/GetQuoteApi?functionName=getSymbolDerivativesData&symbol={symbol}'
        response = session.get(url, headers=headers, timeout=15)

        print(f"NSE response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            chain = data.get('data', [])
            print(f"Got {len(chain)} entries for {symbol}")
            return chain
        else:
            print(f"NSE returned: {response.text[:200]}")
            return []

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return []


def save_to_supabase(symbol, chain):
    """Save option chain to Supabase"""
    if not chain:
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

    # Prepare rows
    rows = []
    for entry in chain:
        try:
            rows.append({
                "symbol": symbol,
                "strike": float(entry['strikePrice'].strip()),
                "expiry_date": entry['expiryDate'],
                "option_type": entry['optionType'],
                "last_price": float(entry['lastPrice']),
                "open_interest": int(entry['openInterest']),
                "volume": int(entry['totalTradedVolume']),
                "change": float(entry['change']),
                "pchange": float(entry['pchange']),
                "updated_at": datetime.now().isoformat()
            })
        except Exception as e:
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
print(f"SUPABASE_URL: {SUPABASE_URL[:30] if SUPABASE_URL else 'NOT SET'}...")
print(f"SUPABASE_KEY: {'SET' if SUPABASE_KEY else 'NOT SET'}")

# Fetch and save NIFTY
nifty_chain = get_nse_option_chain("NIFTY")
if nifty_chain:
    save_to_supabase("NIFTY", nifty_chain)
else:
    print("NIFTY fetch failed — NSE might be blocking GitHub IPs")

# Fetch and save BANKNIFTY
banknifty_chain = get_nse_option_chain("BANKNIFTY")
if banknifty_chain:
    save_to_supabase("BANKNIFTY", banknifty_chain)
else:
    print("BANKNIFTY fetch failed — NSE might be blocking GitHub IPs")

print("Done!")