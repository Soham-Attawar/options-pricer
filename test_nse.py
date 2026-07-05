import requests
import json

def get_nse_option_chain(symbol="NIFTY"):
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

    url = f'https://www.nseindia.com/api/NextApi/apiClient/GetQuoteApi?functionName=getSymbolDerivativesData&symbol={symbol}'
    response = session.get(url, headers=headers, timeout=10)

    if response.status_code == 200:
        return response.json()
    return None

def get_option_price(symbol, strike, expiry_date, option_type='CE'):
    """
    Get real market price for a specific option
    
    Parameters:
    symbol      - "NIFTY" or "BANKNIFTY"
    strike      - strike price (e.g. 24800)
    expiry_date - expiry date string (e.g. "07-Jul-2026")
    option_type - "CE" for call, "PE" for put
    
    Returns: dict with lastPrice, IV, OI etc
    """
    data = get_nse_option_chain(symbol)
    
    if not data or 'data' not in data:
        return None
    
    for entry in data['data']:
        entry_strike = float(entry['strikePrice'].strip())
        entry_expiry = entry['expiryDate']
        entry_type = entry['optionType']
        
        if (entry_strike == float(strike) and 
            entry_expiry == expiry_date and 
            entry_type == option_type):
            return entry
    
    return None

# --- TEST ---
print("Fetching Nifty option chain...")
result = get_option_price("NIFTY", 24800, "07-Jul-2026", "CE")

if result:
    print(f"\nFound option:")
    print(f"Strike:     {result['strikePrice'].strip()}")
    print(f"Expiry:     {result['expiryDate']}")
    print(f"Type:       {result['optionType']}")
    print(f"LTP:        ₹{result['lastPrice']}")
    print(f"OI:         {result['openInterest']}")
    print(f"Volume:     {result['totalTradedVolume']}")
else:
    print("Option not found — try different strike or expiry")
    
    # Show available expiries
    data = get_nse_option_chain("NIFTY")
    if data:
        expiries = list(set([e['expiryDate'] for e in data['data']]))
        print(f"\nAvailable expiries: {sorted(expiries)}")
        strikes = list(set([e['strikePrice'].strip() for e in data['data'] if e['expiryDate'] == expiries[0]]))
        print(f"Available strikes for {expiries[0]}: {sorted(strikes)[:10]}")