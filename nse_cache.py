# ============================================================
# NSE CACHE - Fetches live NSE data and saves to Supabase
# Run this locally during market hours (9:15am - 3:30pm IST)
# ============================================================

import time
from datetime import datetime
import pytz
from supabase import create_client
from market_data import get_nse_option_chain

# --- SUPABASE CONNECTION ---
SUPABASE_URL = "https://mmmkqwuvzdysetroovhv.supabase.co"
SUPABASE_KEY = "sb_publishable_QxjC-OlwafscoTdoOa06OQ_W6J_5H0O"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def is_market_open():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    if now.weekday() >= 5:
        return False
    market_open = now.replace(hour=9, minute=15, second=0)
    market_close = now.replace(hour=15, minute=30, second=0)
    return market_open <= now <= market_close

def save_option_chain(symbol="NIFTY"):
    print(f"Fetching {symbol} option chain...")
    chain = get_nse_option_chain(symbol)

    if not chain:
        print(f"Failed to fetch {symbol} data")
        return False

    # Prepare data for Supabase
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

    if not rows:
        print("No rows to save")
        return False

    # Delete old data for this symbol
    supabase.table("option_chain").delete().eq("symbol", symbol).execute()

    # Insert new data in batches of 100
    batch_size = 100
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        supabase.table("option_chain").insert(batch).execute()

    print(f"Saved {len(rows)} rows for {symbol}")
    return True

def run_cache():
    print("NSE Cache started...")
    print("Will fetch data every 3 minutes during market hours")

    while True:
        if is_market_open():
            print(f"\n{datetime.now().strftime('%H:%M:%S')} — Market open, fetching data...")
            save_option_chain("NIFTY")
            save_option_chain("BANKNIFTY")
            print("Waiting 3 minutes...")
            time.sleep(180)
        else:
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            print(f"{now.strftime('%H:%M:%S')} — Market closed, checking again in 5 minutes...")
            time.sleep(300)

if __name__ == "__main__":
    # Test first
    print("Testing Supabase connection...")
    save_option_chain("NIFTY")
    print("Test complete! Run run_cache() to start continuous fetching")
    run_cache()