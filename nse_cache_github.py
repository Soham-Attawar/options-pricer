# ============================================================
# NSE CACHE - GitHub Actions version using NseIndiaApi
# Fetches ALL expiries and saves to Supabase
# Accumulates IV history in option_chain_history table
# ============================================================

import requests
import os
import time
from datetime import datetime, timedelta
from nse import NSE

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://mmmkqwuvzdysetroovhv.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_QxjC-OlwafscoTdoOa06OQ_W6J_5H0O")


def get_nse_option_chain_all_expiries(symbol="NIFTY"):
    """Fetch NSE option chain for ALL expiries with retry logic"""
    try:
        print(f"Fetching {symbol} from NSE using NseIndiaApi...")
        all_rows = []

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
                        time.sleep(5)

            if not data or 'records' not in data:
                print(f"No data returned for {symbol}")
                return []

            expiry_dates = data['records'].get('expiryDates', [])
            print(f"Available expiries for {symbol}: {expiry_dates}")

            for expiry in expiry_dates:
                try:
                    expiry_date = datetime.strptime(expiry, "%d-%b-%Y")

                    expiry_data = None
                    for attempt in range(3):
                        try:
                            expiry_data = nse.optionChain(
                                symbol=symbol.lower(),
                                expiry_date=expiry_date
                            )
                            if expiry_data:
                                break
                        except Exception as e:
                            print(f"    Attempt {attempt+1} failed for {expiry}: {e}")
                            if attempt < 2:
                                time.sleep(3)

                    if not expiry_data or 'records' not in expiry_data:
                        print(f"  No data for {expiry}")
                        continue

                    records = expiry_data['records']['data']
                    print(f"  {expiry}: {len(records)} records")

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
                                    "bid_price": float(ce.get('buyPrice1', 0)),
                                    "ask_price": float(ce.get('sellPrice1', 0)),
                                    "bid_qty": int(ce.get('buyQuantity1', 0)),
                                    "ask_qty": int(ce.get('sellQuantity1', 0)),
                                    "nse_iv": float(ce.get('impliedVolatility', 0)),
                                    "updated_at": datetime.now().isoformat()
                                })
                            except Exception as e:
                                print(f"    Error processing CE: {e}")
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
                                    "bid_price": float(pe.get('buyPrice1', 0)),
                                    "ask_price": float(pe.get('sellPrice1', 0)),
                                    "bid_qty": int(pe.get('buyQuantity1', 0)),
                                    "ask_qty": int(pe.get('sellQuantity1', 0)),
                                    "nse_iv": float(pe.get('impliedVolatility', 0)),
                                    "updated_at": datetime.now().isoformat()
                                })
                            except Exception as e:
                                print(f"    Error processing PE: {e}")
                                continue

                except Exception as e:
                    print(f"  Failed for {expiry}: {e}")
                    continue

        print(f"Total rows prepared for {symbol}: {len(all_rows)}")
        return all_rows

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return []


def save_to_supabase_current(symbol, rows):
    """
    Save to option_chain table (current snapshot)
    Deletes old data for symbol and inserts fresh
    """
    if not rows:
        print(f"No data to save for {symbol}")
        return

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }

    # Delete current data for this symbol
    delete_response = requests.delete(
        f"{SUPABASE_URL}/rest/v1/option_chain?symbol=eq.{symbol}",
        headers=headers,
        timeout=10
    )
    print(f"Cleared current data for {symbol}: status {delete_response.status_code}")

    # Insert fresh data in batches
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
        print(f"  Batch {i//100 + 1}: status {response.status_code}")

    print(f"Successfully saved {total_inserted} rows to option_chain for {symbol}")


def save_to_supabase_history(symbol, rows):
    """
    Save to option_chain_history table (accumulates over time)
    Never deletes — keeps building IV history for IV rank/percentile
    Cleans up snapshots older than 30 days to manage storage
    """
    if not rows:
        return

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }

    # Clean up snapshots older than 30 days
    cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
    delete_response = requests.delete(
        f"{SUPABASE_URL}/rest/v1/option_chain_history?symbol=eq.{symbol}&snapshot_time=lt.{cutoff}",
        headers=headers,
        timeout=10
    )
    print(f"Cleaned old history (>30 days) for {symbol}: status {delete_response.status_code}")

    # Prepare history rows with snapshot_time
    snapshot_time = datetime.utcnow().isoformat()
    history_rows = []
    for row in rows:
        history_rows.append({
            "symbol": row["symbol"],
            "strike": row["strike"],
            "expiry_date": row["expiry_date"],
            "option_type": row["option_type"],
            "last_price": row["last_price"],
            "bid_price": row.get("bid_price", 0),
            "ask_price": row.get("ask_price", 0),
            "bid_qty": row.get("bid_qty", 0),
            "ask_qty": row.get("ask_qty", 0),
            "open_interest": row["open_interest"],
            "volume": row["volume"],
            "change": row["change"],
            "pchange": row["pchange"],
            "implied_volatility": row["implied_volatility"],
            "nse_iv": row["nse_iv"],
            "snapshot_time": snapshot_time
        })

    # Insert history in batches
    total_inserted = 0
    for i in range(0, len(history_rows), 100):
        batch = history_rows[i:i+100]
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/option_chain_history",
            headers=headers,
            json=batch,
            timeout=15
        )
        if response.status_code == 201:
            total_inserted += len(batch)
        print(f"  History batch {i//100 + 1}: status {response.status_code}")

    print(f"Successfully saved {total_inserted} rows to option_chain_history for {symbol}")


# --- MAIN ---
print(f"NSE Cache GitHub Actions — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"SUPABASE_URL: {'SET' if SUPABASE_URL else 'NOT SET'}")
print(f"SUPABASE_KEY: {'SET' if SUPABASE_KEY else 'NOT SET'}")

for symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]:
    rows = get_nse_option_chain_all_expiries(symbol)
    if rows:
        # Save current snapshot (for live pricing)
        save_to_supabase_current(symbol, rows)
        # Save to history (for IV rank/percentile — never overwrites)
        save_to_supabase_history(symbol, rows)
    else:
        print(f"No data fetched for {symbol} — skipping")

print("Done!")