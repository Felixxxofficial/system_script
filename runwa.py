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
            nature_selector = 'button.title-YfEi4M:has-text("Nature")'
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

            # Add enhanced debugging to find and interact with the 7.5 folder
            print("[INFO] Debugging available elements before looking for 7.5 folder...")
            # List all elements that might be related to folders
            debug_elements = page.query_selector_all('div.inner-s5b9zr, p.name-kS9Ae2, div.imageGrid-FH3gvW')
            print(f"[DEBUG] Found {len(debug_elements)} potential folder elements")
            
            for i, element in enumerate(debug_elements):
                if element.is_visible():
                    tag = element.evaluate('el => el.tagName.toLowerCase()')
                    class_name = element.evaluate('el => el.className')
                    text = element.inner_text().strip()[:50] if tag != 'input' else '[input field]'
                    print(f"[DEBUG] Element {i}: {tag}.{class_name}, Text: {text}")
                    
                    # Check if this element contains "7.5"
                    if "7.5" in text:
                        print(f"[DEBUG] Found element with 7.5 text: {tag}.{class_name}")
            
            # First, check if we're already inside the 7.5 folder
            print("[INFO] Checking if we're already inside the 7.5 folder...")
            nav_selector = 'div.container-JD1VJ8:has(button:has-text("7.5."))'
            
            try:
                # Check if the navigation breadcrumb with 7.5 is present
                if page.is_visible(nav_selector):
                    print("[INFO] Already inside the 7.5 folder!")
                    inside_folder = True
                else:
                    inside_folder = False
                    print("[INFO] Not inside the 7.5 folder yet, need to navigate to it")
                    
                    # Try to find and click the 7.5 folder
                    print("[INFO] Looking for div.inner-s5b9zr containing 7.5...")
                    inner_selector = 'div.inner-s5b9zr'
                    inner_elements = page.query_selector_all(inner_selector)
                    
                    target_element = None
                    for i, element in enumerate(inner_elements):
                        if element.is_visible():
                            text = element.inner_text().strip()
                            print(f"[DEBUG] inner-s5b9zr {i} text: {text[:50]}")
                            if "7.5" in text:
                                target_element = element
                                print(f"[DEBUG] Found target element {i} with 7.5 text")
                                break
                    
                    if target_element:
                        # Use JavaScript to force open the folder - this worked before
                        print("[INFO] Using JavaScript to force open the 7.5 folder")
                        
                        # Get the element's DOM path for JavaScript
                        element_js_handle = target_element.evaluate('''(element) => {
                            // Force a click event on the element
                            const clickEvent = new MouseEvent('dblclick', {
                                bubbles: true,
                                cancelable: true,
                                view: window
                            });
                            element.dispatchEvent(clickEvent);
                            
                            // Try to find and click any clickable children
                            const clickables = element.querySelectorAll('p, div, img');
                            for (let i = 0; i < clickables.length; i++) {
                                clickables[i].click();
                            }
                            
                            // Also try to click the name element specifically
                            const nameElement = element.querySelector('p.name-kS9Ae2');
                            if (nameElement) {
                                nameElement.click();
                                // Try a double click too
                                const dblClickEvent = new MouseEvent('dblclick', {
                                    bubbles: true,
                                    cancelable: true,
                                    view: window
                                });
                                nameElement.dispatchEvent(dblClickEvent);
                            }
                            
                            return "Attempted to force open folder via JavaScript";
                        }''')
                        
                        print(f"[DEBUG] JavaScript result: {element_js_handle}")
                        time.sleep(5)  # Longer wait for JavaScript actions to take effect
                        
                        # Try to verify we're inside the folder by checking for the navigation breadcrumb
                        print("[INFO] Checking for navigation breadcrumb with 7.5...")
                        try:
                            # Check for the navigation breadcrumb that indicates we're inside the folder
                            breadcrumb_selector = 'div.container-JD1VJ8 button:has-text("7.5.")'
                            page.wait_for_selector(breadcrumb_selector, timeout=5000)
                            print("[INFO] Successfully navigated to the 7.5 folder!")
                            inside_folder = True
                        except Exception as e:
                            print(f"[WARNING] Could not find navigation breadcrumb: {e}")
                            # Even if we can't confirm, assume we're in and continue
                            print("[INFO] Continuing anyway, assuming we're in the folder")
                            inside_folder = True
            except Exception as e:
                print(f"[WARNING] Error checking folder navigation: {e}")
                inside_folder = False
            
            # Now that we're inside the folder (or should be), find and click on an image
            if inside_folder:
                # Wait a moment to ensure folder contents are loaded
                time.sleep(3)
                
                # Try multiple approaches to find and click on images
                print("[INFO] Looking for images in the 7.5 folder...")
                
                # Approach 1: Look for image titles
                print("[INFO] Approach 1: Looking for image titles...")
                image_title_selector = 'p.title-Epqee6'
                try:
                    page.wait_for_selector(image_title_selector, timeout=5000, state='visible')
                    image_titles = page.query_selector_all(image_title_selector)
                    print(f"[DEBUG] Found {len(image_titles)} image titles in the folder")
                    
                    if len(image_titles) > 0:
                        for i, title in enumerate(image_titles[:5]):
                            if title.is_visible():
                                text = title.inner_text().strip()
                                print(f"[DEBUG] Image {i}: {text}")
                        
                        # Click on the first visible title
                        for title in image_titles:
                            if title.is_visible():
                                print("[INFO] Clicking on first visible image title")
                                title.click()
                                time.sleep(3)
                                break
                except Exception as e:
                    print(f"[WARNING] Approach 1 failed: {e}")
                
                # Approach 2: Look for image containers
                print("[INFO] Approach 2: Looking for image info containers...")
                try:
                    image_info_selector = 'div.info-FG7ssj'
                    if page.is_visible(image_info_selector):
                        print("[INFO] Found visible image info containers")
                        # Click the first one using JavaScript for more reliable clicking
                        page.evaluate('''
                        () => {
                            const imageInfos = document.querySelectorAll('div.info-FG7ssj');
                            if (imageInfos.length > 0) {
                                // Try to click it
                                imageInfos[0].click();
                                // Also try to click any child elements
                                const children = imageInfos[0].querySelectorAll('*');
                                for (let i = 0; i < children.length; i++) {
                                    children[i].click();
                                }
                                return true;
                            }
                            return false;
                        }
                        ''')
                        print("[INFO] Clicked on image container via JavaScript")
                        time.sleep(3)
                except Exception as e:
                    print(f"[WARNING] Approach 2 failed: {e}")
                
                # Approach 3: Click on any image element
                print("[INFO] Approach 3: Looking for any image elements...")
                try:
                    # Try to find and click on any image
                    images = page.query_selector_all('img')
                    print(f"[DEBUG] Found {len(images)} image elements")
                    
                    if len(images) > 0:
                        for img in images:
                            if img.is_visible():
                                print("[INFO] Clicking on first visible image element")
                                img.click()
                                time.sleep(3)
                                break
                except Exception as e:
                    print(f"[WARNING] Approach 3 failed: {e}")
            else:
                print("[ERROR] Could not confirm we're inside the 7.5 folder")
                # Try fallback approach if we can't find the exact element
                print("[INFO] Fallback: Looking for any element with 7.5 text")
                try:
                    fallback_selector = 'p.name-kS9Ae2:text("7.5.")'
                    page.wait_for_selector(fallback_selector, timeout=10000)
                    page.click(fallback_selector)
                    print("[INFO] Clicked on element with 7.5 text")
                    time.sleep(3)
                except Exception as e:
                    print(f"[ERROR] Fallback also failed: {e}")
                    raise Exception("Failed to navigate to 7.5 folder")
            
            # Wait for any images to be visible
            print("[INFO] Waiting for images to be visible...")
            page.wait_for_selector('img.image-F76umv', timeout=15000, state='visible')
            time.sleep(2)
            
            # We've already clicked an image in the folder verification section,
            # so we can skip the image selection step here and go directly to the prompt
            
            # Wait longer for UI to update after image selection
            print("[INFO] Waiting for UI to update after image selection...")
            time.sleep(10)  # Increased wait time
            
            # Input prompt using the exact selector from the HTML
            print("[INFO] Looking for text prompt input...")
            # Use the exact selector from the provided HTML
            exact_prompt_selector = 'div[aria-label="Text Prompt Input"][contenteditable="true"][role="textbox"]'
            
            # Wait for the prompt input to appear (with a longer timeout)
            try:
                print("[INFO] Waiting for text prompt input to appear...")
                page.wait_for_selector(exact_prompt_selector, timeout=15000, state='visible')
                print("[INFO] Text prompt input found!")
            except Exception as e:
                print(f"[WARNING] Could not find exact text prompt input: {e}")
                # Try a more general selector
                print("[INFO] Trying more general selector...")
                try:
                    page.wait_for_selector('div.textbox-lvV8X2', timeout=5000, state='visible')
                    print("[INFO] Found textbox-lvV8X2 class element")
                    exact_prompt_selector = 'div.textbox-lvV8X2'
                except Exception as e2:
                    print(f"[WARNING] Could not find textbox class either: {e2}")
                    # Try even more general selectors
                    general_selectors = [
                        'div[aria-label="Text Prompt Input"]',
                        'div[contenteditable="true"]',
                        'div[role="textbox"]'
                    ]
                    for selector in general_selectors:
                        try:
                            if page.is_visible(selector):
                                print(f"[INFO] Found input with selector: {selector}")
                                exact_prompt_selector = selector
                                break
                        except:
                            continue
            
            # Try to click and fill the prompt input
            try:
                # Click on the prompt input to focus it
                print("[INFO] Clicking on text prompt input")
                page.click(exact_prompt_selector)
                time.sleep(1)
                
                # Clear any existing text
                print("[INFO] Clearing existing text")
                page.keyboard.press("Control+A")
                page.keyboard.press("Delete")
                time.sleep(0.5)
                
                # Type the prompt using keyboard typing (more reliable for contenteditable)
                print(f"[INFO] Typing prompt: {prompt}")
                page.keyboard.type(prompt)
                print("[INFO] Successfully entered prompt text")
                time.sleep(1)
            except Exception as e:
                print(f"[ERROR] Failed to enter prompt text: {e}")
                # Try using JavaScript as a last resort
                try:
                    print("[INFO] Trying JavaScript to set prompt text")
                    page.evaluate(f'''
                    () => {{
                        const promptInput = document.querySelector('div[aria-label="Text Prompt Input"]');
                        if (promptInput) {{
                            promptInput.textContent = "{prompt}";
                            return true;
                        }}
                        return false;
                    }}
                    ''')
                    print("[INFO] Set prompt text via JavaScript")
                except Exception as js_error:
                    print(f"[ERROR] JavaScript prompt entry also failed: {js_error}")
                    continue
            
            # Click Generate button
            print("[INFO] Looking for Generate button...")
            generate_selector = 'button:has-text("Generate")'
            try:
                page.wait_for_selector(generate_selector, timeout=10000)
                page.click(generate_selector)
                print("[INFO] Clicked Generate button")
            except Exception as e:
                print(f"[ERROR] Failed to click Generate button: {e}")
                continue

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
        
        # Add a small delay to ensure AdsPower is fully initialized
        time.sleep(5)
        
        with sync_playwright() as p:
            # More robust connection with error handling
            try:
                # Add retry mechanism for browser connection
                max_connection_attempts = 3
                connection_attempt = 0
                
                while connection_attempt < max_connection_attempts:
                    try:
                        connection_attempt += 1
                        print(f"[INFO] Connection attempt {connection_attempt}/{max_connection_attempts}")
                        
                        # Add slow_mo parameter to make browser interactions more stable
                        browser = p.chromium.connect_over_cdp(
                            ws_url,
                            timeout=30000,  # 30 second timeout
                            slow_mo=100,  # Add 100ms delay between actions
                            headers={"User-Agent": "Mozilla/5.0"}
                        )
                        print("[INFO] Browser connection successful")
                        break
                    except Exception as e:
                        print(f"[ERROR] Connection attempt {connection_attempt} failed: {e}")
                        if connection_attempt >= max_connection_attempts:
                            raise
                        time.sleep(5)  # Wait before retry
                
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