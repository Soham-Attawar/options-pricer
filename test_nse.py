from nse import NSE
from pathlib import Path
import json

print("Testing NseIndiaApi with server=True...")

with NSE(download_folder='./', server=True) as nse:
    try:
        # Get option chain for NIFTY
        data = nse.optionChain(symbol="nifty")
        print(f"Success! Type: {type(data)}")
        print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
        
        # Try to get specific data
        if data:
            print(json.dumps(data, indent=2)[:500])
            
    except Exception as e:
        print(f"Failed: {e}")