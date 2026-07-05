# ============================================================
# NSE CACHE - GitHub Actions version using NseIndiaApi
# Fetches ALL expiries and saves to Supabase
# ============================================================

import requests
import os
from datetime import datetime
from nse import NSE

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


def get_nse_option_chain_all_expiries(symbol="NIFTY"):
    """Fetch NSE option chain for ALL expiries"""
    try:
        print(f"Fetching {symbol} from NSE using NseIndiaApi...")
        all_rows = []

        with NSE(download_folder='./', server=True) as nse:
            # Get initial data to find all expiry dates
            data = nse.optionChain(symbol=symbol.lower())

            if not data or 'records' not in data:
                print(f"No data returned for {symbol}")
                return []

            # Get all available expiry dates
            expiry_dates = data['records'].get('expiryDates', [])
            print(f"Available expiries for {symbol}: {expiry_dates}")

            # Fetch data for each expiry separately
            for expiry in expiry_dates:
                try:
                    expiry_date = datetime.strptime(expiry, "%d-%b-%Y")
                    expiry_data = nse.optionChain(
                        symbol=symbol.lower(),
                        expiry_date=expiry_date
                    )

                    if not expiry_data or 'records' not in expiry_data:
                        print(f"  No data for {expiry}")
                        continue

                    records = expiry_data['records']['data']
                    print(f"  {expiry}: {len(records)} records")

                    # Process each record
                    for record in records:
                        # Process CE (Call)
                        if 'CE' in record and record['CE']:
                            ce = record['CE']
                            try:
                                all_rows.append({
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
                                all_rows.append({
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

                except Exception as e:
                    print(f"  Failed for {expiry}: {e}")
                    continue

        print(f"Total rows prepared for {symbol}: {len(all_rows)}")
        return all_rows

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return []


def save_to_supabase(symbol, rows):
    """Save option chain to Supabase"""
    if not rows:
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
    print(f"Delete old data for {symbol}: status {delete_response.status_code}")

    # Insert in batches of 100
    total_inserted = 0
    for i in range(0, len(rows), 100):
        batch = rows[i:i+100]
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/option_chain",
            headers=headers,
            json=batch,
            timeout=15
        )
        if response.status_code == 201:
            total_inserted += len(batch)
        print(f"Batch {i//100 + 1}: status {response.status_code}")

    print(f"Successfully saved {total_inserted} rows for {symbol}")


# --- MAIN ---
print(f"NSE Cache GitHub Actions — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"SUPABASE_URL: {'SET' if SUPABASE_URL else 'NOT SET'}")
print(f"SUPABASE_KEY: {'SET' if SUPABASE_KEY else 'NOT SET'}")

# Fetch and save NIFTY all expiries
nifty_rows = get_nse_option_chain_all_expiries("NIFTY")
if nifty_rows:
    save_to_supabase("NIFTY", nifty_rows)

# Fetch and save BANKNIFTY all expiries
banknifty_rows = get_nse_option_chain_all_expiries("BANKNIFTY")
if banknifty_rows:
    save_to_supabase("BANKNIFTY", banknifty_rows)

print("Done!")