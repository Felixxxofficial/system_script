import time
from playwright.sync_api import sync_playwright, TimeoutError
import os
import requests
import json

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ADPOWER_PROFILE_ID = os.getenv('ADPOWER_PROFILE_ID', 'kxslwbx')  # AdsPower profile ID
ADPOWER_API_URL = os.getenv('ADPOWER_API_URL', 'http://127.0.0.1:50325')  # AdsPower local API
RUNWAY_URL = 'https://app.runwayml.com/video-tools/teams/janotad/ai-tools/generate?sessionId=7adcf098-b9bf-4f55-a23e-c7e98f9c7409'

def start_adspower_browser():
    """Start AdsPower browser profile and return WebSocket endpoint"""
    try:
        # Control instance (just opens AdsPower UI)
        ctrl_url = f"{ADPOWER_API_URL}/api/v1/browser/start?user_id={ADPOWER_PROFILE_ID}&open_url=about:blank"
        print("[INFO] Starting AdsPower control browser")
        requests.get(ctrl_url)
        
        # Working instance (will be controlled via Playwright)
        work_url = f"{ADPOWER_API_URL}/api/v1/browser/start?user_id={ADPOWER_PROFILE_ID}&open_url=https://google.com"
        print("[INFO] Starting working browser instance")
        response = requests.get(work_url)
        response.raise_for_status()
        
        data = response.json()
        if data.get("code") != 0:
            raise Exception(f"AdsPower error: {data.get('msg')}")
        
        # Make sure we have all the required data
        if not data.get("data") or not data["data"].get("ws"):
            raise Exception("Missing WebSocket data in AdsPower response")
            
        # Get the CDP endpoint instead of puppeteer for better compatibility
        ws_endpoint = data["data"]["ws"].get("cdp") or data["data"]["ws"].get("puppeteer")
        if not ws_endpoint:
            raise Exception("No valid WebSocket endpoint found in AdsPower response")
            
        print(f"[INFO] Working browser WebSocket: {ws_endpoint}")
        # Wait a moment for the browser to fully initialize
        time.sleep(3)
        return ws_endpoint
    except Exception as e:
        print(f"[ERROR] Browser startup failed: {e}")
        return None

def simple_scroll_test(page):
    """Simple test: Enter prompt, scroll up a little, then down to check for queue"""
    # First, focus on the text prompt input and enter a test prompt
    prompt_selector = 'div[contenteditable="true"][data-testid="prompt-textarea"]'
    
    try:
        # Wait for the prompt input to be visible
        page.wait_for_selector(prompt_selector, state='visible', timeout=10000)
        print("[INFO] Text prompt input found")
        
        # Click on the prompt input to focus it
        page.click(prompt_selector)
        print("[INFO] Clicked on text prompt input")
        time.sleep(1)
        
        # Enter a test prompt
        test_prompt = "This is a test prompt for scrolling experiment"
        page.fill(prompt_selector, test_prompt)
        print(f"[INFO] Entered test prompt: '{test_prompt}'")
        time.sleep(1)
        
        # Take a screenshot before any scrolling
        screenshot_path = os.path.join(SCRIPT_DIR, "before_scroll.png")
        page.screenshot(path=screenshot_path)
        print(f"[INFO] Saved screenshot before scrolling to {screenshot_path}")
        
    except Exception as e:
        print(f"[ERROR] Failed to focus on text prompt input: {e}")
    
    # Now focus on the virtuoso-item-list and do the simple scroll test
    print("\n[INFO] Starting simple scroll test - up a little, then down to check for queue...")
    virtuoso_item_list = 'div[data-testid="virtuoso-item-list"]'
    
    try:
        # Check if the virtuoso-item-list element exists
        if page.query_selector(virtuoso_item_list):
            print(f"[INFO] Found virtuoso-item-list element")
            
            # Click on the list to focus it
            page.click(virtuoso_item_list)
            print(f"[INFO] Clicked on virtuoso-item-list to focus it")
            time.sleep(1)
            
            # Get the current scroll position
            initial_position = page.evaluate(f"""
            () => {{
                const list = document.querySelector('{virtuoso_item_list}');
                if (list) {{
                    // Find the parent scroller
                    const scroller = list.closest('[data-testid="virtuoso-scroller"]');
                    if (scroller) {{
                        return scroller.scrollTop;
                    }}
                    return null;
                }}
                return null;
            }}
            """)
            print(f"[INFO] Initial scroll position: {initial_position}")
            
            # First scroll up a little bit
            result = page.evaluate(f"""
            () => {{
                const list = document.querySelector('{virtuoso_item_list}');
                if (list) {{
                    // Find the parent scroller
                    const scroller = list.closest('[data-testid="virtuoso-scroller"]');
                    if (scroller) {{
                        // Get current position
                        const currentPos = scroller.scrollTop;
                        // Scroll up a little bit (150 pixels)
                        scroller.scrollTop = currentPos - 150;
                        return `Scrolled up from ${{currentPos}} to ${{scroller.scrollTop}}`;
                    }}
                    return "Parent scroller not found";
                }}
                return "List not found";
            }}
            """)
            print(f"[INFO] {result}")
            time.sleep(1)
            
            # Take a screenshot after scrolling up
            screenshot_path = os.path.join(SCRIPT_DIR, "after_scroll_up.png")
            page.screenshot(path=screenshot_path)
            print(f"[INFO] Saved screenshot after scrolling up to {screenshot_path}")
            
            # Now scroll down to check for queue
            print("[INFO] Now scrolling down to check for queue...")
            
            # Scroll down further than initial position to see queue items
            result = page.evaluate(f"""
            () => {{
                const list = document.querySelector('{virtuoso_item_list}');
                if (list) {{
                    // Find the parent scroller
                    const scroller = list.closest('[data-testid="virtuoso-scroller"]');
                    if (scroller) {{
                        // Get current position
                        const currentPos = scroller.scrollTop;
                        // Scroll down past initial position (initial + 300 pixels)
                        scroller.scrollTop = {initial_position} + 300;
                        return `Scrolled down from ${{currentPos}} to ${{scroller.scrollTop}}`;
                    }}
                    return "Parent scroller not found";
                }}
                return "List not found";
            }}
            """)
            print(f"[INFO] {result}")
            time.sleep(1)
            
            # Take a screenshot after scrolling down
            screenshot_path = os.path.join(SCRIPT_DIR, "after_scroll_down.png")
            page.screenshot(path=screenshot_path)
            print(f"[INFO] Saved screenshot after scrolling down to {screenshot_path}")
            
            # Check for 'In queue' text
            queue_selectors = [
                'div.percentage-o2hVFS:text("In queue")',  # Direct text match
                'div.percentage-o2hVFS',                   # Class only
                'div.progress-bar-container-lIQqmt div.percentage-o2hVFS'  # Parent-child relationship
            ]
            
            found_queue = False
            for selector in queue_selectors:
                elements = page.query_selector_all(selector)
                for element in elements:
                    if element.is_visible():
                        text = element.inner_text().strip()
                        if "In queue" in text:
                            found_queue = True
                            print(f"[SUCCESS] Found 'In queue' text: '{text}'")
                            
                            # Take a screenshot of the found queue message
                            screenshot_path = os.path.join(SCRIPT_DIR, "found_queue_message.png")
                            page.screenshot(path=screenshot_path)
                            print(f"[INFO] Saved screenshot with queue message to {screenshot_path}")
                            break
                
                if found_queue:
                    break
            
            if not found_queue:
                print("[INFO] No 'In queue' messages found")
            
        else:
            print("[WARNING] Could not find virtuoso-item-list element")
    except Exception as e:
        print(f"[ERROR] Error during scrolling: {e}")

def main():
    """Main function to run the scrolling test"""
    ws_endpoint = start_adspower_browser()
    if not ws_endpoint:
        print("[ERROR] Failed to get WebSocket endpoint, exiting")
        return
    
    with sync_playwright() as p:
        try:
            # Connect to the browser
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            print("[INFO] Connected to browser")
            
            # Use the default context
            context = browser.contexts[0]
            
            # Get the first page or create a new one if none exists
            if len(context.pages) > 0:
                page = context.pages[0]
                print("[INFO] Using existing page")
            else:
                page = context.new_page()
                print("[INFO] Created new page")
            
            # Navigate to Runway
            print(f"[INFO] Navigating to {RUNWAY_URL}")
            page.goto(RUNWAY_URL)
            
            # Wait for the page to load
            page.wait_for_load_state("networkidle")
            print("[INFO] Page loaded")
            
            # Run the simple scroll test
            simple_scroll_test(page)
            
            # Keep the browser open for a moment to see the results
            print("[INFO] Test completed, keeping browser open for 5 seconds")
            time.sleep(5)
            
        except Exception as e:
            print(f"[ERROR] Test failed: {e}")
        finally:
            # Close the browser
            browser.close()
            print("[INFO] Browser closed")

if __name__ == "__main__":
    main()
