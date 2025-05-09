import requests
from playwright.sync_api import sync_playwright
import json

# AdsPower API configuration
ADPOWER_API_URL = "http://local.adspower.net:50325"
PROFILE_ID = "kxslwbx"

def start_adspower_browser():
    """Start AdsPower browser profile and return WebSocket endpoint"""
    try:
        # Send GET request to start browser
        url = f"{ADPOWER_API_URL}/api/v1/browser/start?user_id={PROFILE_ID}"
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad status codes
        data = response.json()
        
        # Check if request was successful
        if data.get("code") == 0:
            ws_endpoint = data["data"]["ws"]["selenium"]
            print(f"[INFO] Successfully started browser. WebSocket: {ws_endpoint}")
            return ws_endpoint
        else:
            print(f"[ERROR] Failed to start browser: {data.get('msg')}")
            return None
    except Exception as e:
        print(f"[ERROR] Error starting AdsPower browser: {e}")
        return None

def main():
    # Start AdsPower browser
    ws_endpoint = start_adspower_browser()
    if not ws_endpoint:
        print("[ERROR] Exiting due to failure to start browser")
        return

    # Connect to browser using Playwright
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()

            # Test navigation (e.g., go to a sample page)
            page.goto("https://www.example.com", wait_until="domcontentloaded")
            print(f"[INFO] Navigated to example.com. Page title: {page.title()}")

            # Close browser
            browser.close()
            print("[INFO] Browser closed successfully")
        except Exception as e:
            print(f"[ERROR] Playwright error: {e}")
        finally:
            if 'browser' in locals():
                browser.close()

if __name__ == "__main__":
    main()