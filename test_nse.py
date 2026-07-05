from playwright.sync_api import sync_playwright
import json

def get_nse_data_playwright(symbol="NIFTY"):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-http2']
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ignore_https_errors=True
        )
        page = context.new_page()

        try:
            # Skip main page — go directly to a lighter NSE page
            print("Getting NSE cookies...")
            page.goto("https://www.nseindia.com/option-chain",
                     wait_until="domcontentloaded",
                     timeout=60000)

            page.wait_for_timeout(2000)

            # Fetch data
            print("Fetching data...")
            url = f"https://www.nseindia.com/api/NextApi/apiClient/GetQuoteApi?functionName=getSymbolDerivativesData&symbol={symbol}"
            response = page.request.get(url)
            print(f"Status: {response.status}")

            if response.status == 200:
                data = response.json()
                print(f"Success! Total entries: {len(data.get('data', []))}")
                return data
            else:
                print(f"Failed: {response.text[:200]}")
                return None

        except Exception as e:
            print(f"Error: {e}")
            return None
        finally:
            browser.close()

data = get_nse_data_playwright("NIFTY")
if data:
    print("Playwright working!")
else:
    print("Playwright failed — sticking with requests method")