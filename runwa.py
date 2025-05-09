import os
import json
from datetime import datetime
import time
import msvcrt  # Windows-specific keyboard input
from playwright.sync_api import sync_playwright, TimeoutError
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
COOKIE_PATH = os.path.join(BASE_DIR, 'runway_cookies.json')
ADPOWER_PROFILE_ID = os.getenv('ADPOWER_PROFILE_ID', 'kxslwbx')  # AdsPower profile ID
ADPOWER_API_URL = os.getenv('ADPOWER_API_URL', 'http://127.0.0.1:50325')  # AdsPower local API
RUNWAY_URL = 'https://app.runwayml.com/video-tools/teams/janotad/dashboard'

stop_scraping = False

def load_cookies():
    """Load cookies from file"""
    try:
        with open(COOKIE_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load cookies: {e}")
        return None

def save_cookies(context):
    """Save cookies to file after login"""
    try:
        cookies = context.cookies()
        with open(COOKIE_PATH, 'w') as f:
            json.dump(cookies, f)
        print("[INFO] Cookies saved successfully")
    except Exception as e:
        print(f"[ERROR] Failed to save cookies: {e}")

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
            
        ws_endpoint = data["data"]["ws"]["puppeteer"]
        print(f"[INFO] Working browser WebSocket: {ws_endpoint}")
        return ws_endpoint
    except Exception as e:
        print(f"[ERROR] Browser startup failed: {e}")
        return None

def validate_page_load(page):
    """Validate that the Runway dashboard loaded correctly"""
    try:
        # Wait for any element that confirms the page has loaded
        page.wait_for_selector('body', timeout=20000)
        print("[INFO] Page loaded successfully")
        
        # Check for login page vs dashboard
        if page.query_selector('input[type="email"]'):
            print("[INFO] Login page detected")
            return "login"
        else:
            print("[INFO] Page loaded, checking for dashboard elements")
            # Try to find elements specific to the dashboard
            dashboard_elements = page.query_selector_all('button, a, div[role="button"]')
            print(f"[INFO] Found {len(dashboard_elements)} interactive elements")
            return "dashboard" if len(dashboard_elements) > 5 else "unknown"
    except Exception as e:
        print(f"[ERROR] Page failed to load properly: {e}")
        return "error"

def list_visible_elements(page):
    """List all visible elements on the page"""
    try:
        print("[INFO] Listing visible elements...")
        elements = page.query_selector_all('button, a, div[role="button"], input, textarea, p')
        print(f"[INFO] Found {len(elements)} interactive elements")
        
        for i, element in enumerate(elements[:50]):  # Show more elements
            if element.is_visible():
                tag = element.evaluate('el => el.tagName.toLowerCase()')
                text = element.inner_text().strip()[:100] if tag != 'input' else '[input field]'
                attrs = element.evaluate('''el => {
                    const result = {};
                    for (const attr of el.attributes) {
                        result[attr.name] = attr.value;
                    }
                    return result;
                }''')
                print(f"[DEBUG] Element {i}: {tag}, Text: {text}, Attrs: {attrs}")
    except Exception as e:
        print(f"[ERROR] Failed to list visible elements: {e}")

def generate_video(page, prompt, max_retries=3):
    """Generate a video with the given prompt"""
    for attempt in range(max_retries):
        try:
            print(f"[INFO] Generating video with prompt: {prompt} (Attempt {attempt + 1}/{max_retries})")
            
            # Click "Nature" category
            print("[INFO] Looking for Nature category...")
            nature_selector = 'text="Nature"'
            page.wait_for_selector(nature_selector, timeout=10000)
            page.click(nature_selector)
            print("[INFO] Clicked Nature category")
            time.sleep(2)  # Wait for UI to update

            # Click "Select asset" button
            print("[INFO] Looking for 'Select asset' button...")
            select_asset_selector = 'button[data-rac]:has-text("Select asset")'
            page.wait_for_selector(select_asset_selector, timeout=10000)
            page.click(select_asset_selector)
            print("[INFO] Clicked Select asset button")
            time.sleep(2)  # Wait for modal to open

            # Click "Assets" tab
            print("[INFO] Looking for Assets tab...")
            assets_selector = 'p.secondary-YynanQ:has-text("Assets")'
            page.wait_for_selector(assets_selector, timeout=10000)
            page.click(assets_selector)
            print("[INFO] Clicked Assets tab")
            time.sleep(2)  # Wait for assets to load

            # Select asset "7.5."
            print("[INFO] Looking for asset 7.5...")
            asset_selector = 'p.name-kS9Ae2:has-text("7.5.")'
            page.wait_for_selector(asset_selector, timeout=10000)
            page.click(asset_selector)
            print("[INFO] Selected asset 7.5.")
            time.sleep(2)  # Wait for asset selection

            # Click first image
            print("[INFO] Looking for first image...")
            image_selector = 'img'  # First image
            page.wait_for_selector(image_selector, timeout=10000)
            images = page.query_selector_all(image_selector)
            if len(images) > 0:
                images[0].click()
                print("[INFO] Clicked first image")
            else:
                print("[ERROR] No images found")
                continue
            time.sleep(2)  # Wait for image selection

            # Input prompt
            print("[INFO] Looking for text prompt input...")
            prompt_selector = 'div[aria-label="Text Prompt Input"]'
            page.wait_for_selector(prompt_selector, timeout=10000)
            page.click(prompt_selector)
            
            # Clear existing text if any
            page.keyboard.press("Control+A")
            page.keyboard.press("Delete")
            
            # Type the prompt
            page.fill(prompt_selector, prompt)
            print(f"[INFO] Entered prompt: {prompt}")
            time.sleep(1)  # Wait after typing

            # Click Generate button
            print("[INFO] Looking for Generate button...")
            generate_selector = 'button:has-text("Generate")'
            page.wait_for_selector(generate_selector, timeout=10000)
            page.click(generate_selector)
            print("[INFO] Clicked Generate button")

            # Wait for video generation to complete (looking for "Done" or similar indicator)
            print("[INFO] Waiting for video generation to complete...")
            done_selector = 'text="Done" >> visible=true, text="Complete" >> visible=true, text="Download" >> visible=true'
            try:
                page.wait_for_selector(done_selector, timeout=300000)  # 5-minute timeout
                print("[INFO] Video generation completed")
                return True
            except TimeoutError:
                print("[WARNING] Video generation timeout - checking if still processing...")
                # Check if there's a progress indicator
                if page.query_selector('text="Processing" >> visible=true'):
                    print("[INFO] Still processing, waiting longer...")
                    try:
                        page.wait_for_selector(done_selector, timeout=300000)  # Additional 5 minutes
                        print("[INFO] Video generation completed after extended wait")
                        return True
                    except TimeoutError:
                        print("[ERROR] Video generation timed out after extended wait")
                        continue

        except Exception as e:
            print(f"[ERROR] Failed to generate video: {e}")
            if attempt < max_retries - 1:
                print("[INFO] Retrying...")
                time.sleep(5)  # Longer wait before retry
            continue
    
    print("[ERROR] All attempts to generate video failed")
    return False

def check_for_quit():
    """Check for 'q' key press to stop processing"""
    global stop_scraping
    print("[INFO] Press 'q' at any time to stop processing")
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch().decode().lower()
            if key == 'q':
                stop_scraping = True
                print("\n[INFO] 'q' pressed - Stopping...")
                break

def main():
    print("[INFO] Starting Runway video generation test")
    
    try:
        # Start both browser instances
        ws_url = start_adspower_browser()
        if not ws_url:
            print("[ERROR] Failed to start browser - exiting")
            return
        
        with sync_playwright() as p:
            # More robust connection with error handling
            try:
                browser = p.chromium.connect(
                    ws_url,
                    timeout=30000,  # 30 second timeout
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                
                # Verify connection
                if not browser.contexts:
                    raise Exception("No browser contexts available")
                
                # Get the existing page (already at Google)
                pages = browser.contexts[0].pages
                page = pages[0] if pages else browser.new_page()
                
                # Now navigate to Yahoo in the working browser
                print("[INFO] Navigating working browser to Yahoo")
                page.goto("https://yahoo.com", timeout=60000, wait_until="networkidle")
                
                # Navigate to Runway
                print(f"[INFO] Navigating to {RUNWAY_URL}")
                page.goto(RUNWAY_URL, wait_until='domcontentloaded')
                
                # Check page status
                page_status = validate_page_load(page)
                print(f"[INFO] Page status: {page_status}")
                
                # List visible elements
                list_visible_elements(page)
                
                # Take a screenshot for debugging
                screenshot_path = os.path.join(SCRIPT_DIR, "runway_screenshot.png")
                page.screenshot(path=screenshot_path)
                print(f"[INFO] Screenshot saved to {screenshot_path}")
                
                # Save cookies
                save_cookies(browser.contexts[0])
                
                # Test video generation with a sample prompt
                test_prompt = "Here is my test prompt"
                print(f"[INFO] Testing video generation with prompt: {test_prompt}")
                success = generate_video(page, test_prompt)
                
                if success:
                    print("[INFO] Video generation test successful!")
                else:
                    print("[ERROR] Video generation test failed")
                
                # Wait for manual inspection
                print("[INFO] Test completed. Press Enter to close...")
                input()

            except Exception as e:
                print(f"[ERROR] Browser connection failed: {e}")
                return
    
    except Exception as e:
        print(f"[ERROR] Main function error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("[INFO] Script completed")

if __name__ == "__main__":
    main()