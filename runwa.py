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

# Default prompt
DEFAULT_PROMPT = "the girl is smiling"

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
                
                # Use JavaScript to click on the first image - similar to how we opened the folder
                print("[INFO] Using JavaScript to click on the first image in the folder...")
                
                # First, get all image titles to display what's available
                try:
                    image_title_selector = 'p.title-Epqee6'
                    page.wait_for_selector(image_title_selector, timeout=5000, state='visible')
                    image_titles = page.query_selector_all(image_title_selector)
                    print(f"[DEBUG] Found {len(image_titles)} image titles in the folder")
                    
                    # Display the first few image titles
                    for i, title in enumerate(image_titles[:5]):
                        if title.is_visible():
                            text = title.inner_text().strip()
                            print(f"[DEBUG] Image {i}: {text}")
                except Exception as e:
                    print(f"[WARNING] Could not list image titles: {e}")
                
                # Try multiple different click methods with fast clicks
                # Function to check if we've reached the desired state
                def check_image_selected():
                    try:
                        output_mode_selector = 'div[aria-label="Output mode"][role="radiogroup"]'
                        return page.is_visible(output_mode_selector, timeout=3000)
                    except Exception:
                        return False
                
                # Method 1: Fast clicks on image container
                print("[INFO] METHOD 1: Fast clicks on image container")
                try:
                    image_info_selector = 'div.info-FG7ssj'
                    page.wait_for_selector(image_info_selector, timeout=10000, state='visible')
                    image_infos = page.query_selector_all(image_info_selector)
                    
                    if len(image_infos) > 0:
                        first_image = image_infos[0]
                        print("[INFO] Found first image, doing 4 fast clicks")
                        
                        # 4 fast clicks
                        for i in range(4):
                            first_image.click(force=True)
                            time.sleep(0.1)  # Very short delay between clicks
                        
                        time.sleep(3)  # Wait to see if it worked
                        
                        if check_image_selected():
                            print("[INFO] METHOD 1 SUCCEEDED: Image selected!")
                        else:
                            print("[INFO] METHOD 1 failed, trying next method")
                    else:
                        print("[WARNING] No image info containers found for Method 1")
                except Exception as e:
                    print(f"[WARNING] Method 1 failed with error: {e}")
                
                # Method 2: Fast clicks on image title
                print("[INFO] METHOD 2: Fast clicks on image title")
                try:
                    image_title_selector = 'p.title-Epqee6'
                    page.wait_for_selector(image_title_selector, timeout=5000, state='visible')
                    image_titles = page.query_selector_all(image_title_selector)
                    
                    if len(image_titles) > 0 and image_titles[0].is_visible():
                        print("[INFO] Found first image title, doing 4 fast clicks")
                        
                        # 4 fast clicks
                        for i in range(4):
                            image_titles[0].click(force=True)
                            time.sleep(0.1)  # Very short delay between clicks
                        
                        time.sleep(3)  # Wait to see if it worked
                        
                        if check_image_selected():
                            print("[INFO] METHOD 2 SUCCEEDED: Image selected!")
                        else:
                            print("[INFO] METHOD 2 failed, trying next method")
                    else:
                        print("[WARNING] No visible image titles found for Method 2")
                except Exception as e:
                    print(f"[WARNING] Method 2 failed with error: {e}")
                
                # Method 3: JavaScript rapid clicks
                print("[INFO] METHOD 3: JavaScript rapid clicks")
                try:
                    result = page.evaluate('''
                    () => {
                        const imageInfos = document.querySelectorAll('div.info-FG7ssj');
                        if (imageInfos.length > 0) {
                            // Simulate multiple rapid clicks
                            for (let i = 0; i < 4; i++) {
                                imageInfos[0].click();
                            }
                            
                            // Also try the title
                            const title = imageInfos[0].querySelector('p.title-Epqee6');
                            if (title) {
                                for (let i = 0; i < 4; i++) {
                                    title.click();
                                }
                            }
                            
                            return "Executed JavaScript rapid clicks";
                        }
                        return "No image info containers found for JavaScript clicks";
                    }
                    ''')
                    print(f"[DEBUG] JavaScript rapid clicks result: {result}")
                    time.sleep(3)  # Wait to see if it worked
                    
                    if check_image_selected():
                        print("[INFO] METHOD 3 SUCCEEDED: Image selected!")
                    else:
                        print("[INFO] METHOD 3 failed, trying next method")
                except Exception as e:
                    print(f"[WARNING] Method 3 failed with error: {e}")
                
                # Method 4: Double clicks
                print("[INFO] METHOD 4: Double clicks")
                try:
                    # Try double-clicking on image container
                    image_info_selector = 'div.info-FG7ssj'
                    if page.is_visible(image_info_selector):
                        image_infos = page.query_selector_all(image_info_selector)
                        if len(image_infos) > 0:
                            print("[INFO] Double-clicking on image container")
                            for i in range(2):  # Two double-clicks
                                image_infos[0].dblclick(force=True)
                                time.sleep(0.5)
                            
                            time.sleep(3)  # Wait to see if it worked
                            
                            if check_image_selected():
                                print("[INFO] METHOD 4 SUCCEEDED: Image selected!")
                            else:
                                print("[INFO] METHOD 4 failed, trying next method")
                        else:
                            print("[WARNING] No image containers found for Method 4")
                    else:
                        print("[WARNING] Image container not visible for Method 4")
                except Exception as e:
                    print(f"[WARNING] Method 4 failed with error: {e}")
                    
                    # Verify we've selected an image by checking for the output mode radio group
                    print("[INFO] Verifying image selection by checking for output mode radio group...")
                    output_mode_selector = 'div[aria-label="Output mode"][role="radiogroup"]'
                    
                    try:
                        page.wait_for_selector(output_mode_selector, timeout=10000)
                        print("[INFO] Successfully selected an image! Output mode radio group is visible.")
                        # Set a flag to indicate we've successfully selected an image
                        image_selected = True
                    except Exception as e:
                        print(f"[WARNING] Could not verify image selection: {e}")
                        # Try clicking again on any visible image
                        print("[INFO] Trying alternative approach to click an image...")
                        
                        # Try to click on any visible image element
                        images = page.query_selector_all('img')
                        print(f"[DEBUG] Found {len(images)} image elements")
                        
                        for img in images:
                            if img.is_visible():
                                print("[INFO] Clicking on a visible image element")
                                img.click()
                                time.sleep(5)
                                # Check again if we've selected an image
                                if page.is_visible(output_mode_selector):
                                    print("[INFO] Image selected after alternative approach")
                                    image_selected = True
                                break
                except Exception as e:
                    print(f"[WARNING] JavaScript image click failed: {e}")
                    image_selected = False
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
                    image_selected = False
                except Exception as e:
                    print(f"[ERROR] Fallback also failed: {e}")
                    raise Exception("Failed to navigate to 7.5 folder")
            
            # Skip the wait for images if we've already confirmed the image is selected
            if not image_selected:
                print("[INFO] Waiting for images to be visible...")
                try:
                    page.wait_for_selector('img.image-F76umv', timeout=5000, state='visible')
                    time.sleep(2)
                except Exception as e:
                    print(f"[WARNING] Could not find images, but continuing anyway: {e}")
                    # Continue anyway since we might already be at the prompt stage
            
            # We've already clicked an image in the folder verification section,
            # so we can skip the image selection step here and go directly to the prompt
            
            # Wait longer for UI to update after image selection
            print("[INFO] Waiting for UI to update after image selection...")
            time.sleep(10)  # Increased wait time
            
            # Input prompt using the exact selector from the HTML
            print("[INFO] Looking for text prompt input...")
            # Use the exact selector provided by the user
            exact_prompt_selector = 'div.textbox-lvV8X2[contenteditable="true"][role="textbox"][data-lexical-editor="true"]'
            
            # Wait for the prompt input to appear (with a longer timeout)
            try:
                print("[INFO] Waiting for text prompt input to appear...")
                page.wait_for_selector(exact_prompt_selector, timeout=10000, state='visible')
                print("[INFO] Text prompt input found!")
            except Exception as e:
                print(f"[WARNING] Could not find exact text prompt input: {e}")
                # Try a more general selector
                print("[INFO] Trying more general selector...")
                try:
                    # Try the simpler selector
                    simple_selector = 'div.textbox-lvV8X2'
                    page.wait_for_selector(simple_selector, timeout=5000, state='visible')
                    print("[INFO] Found textbox-lvV8X2 class element")
                    exact_prompt_selector = simple_selector
                except Exception as e2:
                    print(f"[WARNING] Could not find textbox class either: {e2}")
                    # Try even more general selectors in order of specificity
                    general_selectors = [
                        'div[aria-label="Text Prompt Input"]',
                        'div[data-lexical-editor="true"]',
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
            
            # Try using JavaScript to find and interact with the text prompt input
            if exact_prompt_selector is None:
                print("[INFO] Using JavaScript to find and interact with text prompt input")
                try:
                    result = page.evaluate('''
                    () => {
                        // Try multiple ways to find the text input
                        let promptInput = document.querySelector('div[aria-label="Text Prompt Input"]');
                        if (!promptInput) {
                            promptInput = document.querySelector('div[contenteditable="true"][role="textbox"]');
                        }
                        if (!promptInput) {
                            promptInput = document.querySelector('div.textbox-lvV8X2');
                        }
                        if (!promptInput) {
                            promptInput = document.querySelector('div[data-lexical-editor="true"]');
                        }
                        
                        if (promptInput) {
                            // Try to focus and click the element
                            promptInput.focus();
                            promptInput.click();
                            return "Found and focused text prompt input via JavaScript";
                        }
                        return "Could not find text prompt input via JavaScript";
                    }
                    ''')
                    print(f"[DEBUG] JavaScript text input result: {result}")
                    time.sleep(2)
                except Exception as e:
                    print(f"[WARNING] JavaScript text input approach failed: {e}")
            
            # Try to input the prompt
            try:
                print(f"[INFO] Entering prompt: {prompt}")
                # First try to click on the input field
                page.click(exact_prompt_selector)
                time.sleep(1)
                
                # Try multiple methods to enter the text, starting with the most reliable ones
                methods_tried = 0
                success = False
                
                # Method 1: JavaScript direct content setting
                try:
                    js_result = page.evaluate(f"""
                    const element = document.querySelector('{exact_prompt_selector}');
                    if (element) {{
                        // Clear any existing content first
                        element.innerHTML = '<p>' + '{prompt}' + '</p>';
                        // Dispatch input event to trigger any listeners
                        const event = new Event('input', {{ bubbles: true }});
                        element.dispatchEvent(event);
                        return 'Prompt set via JavaScript';
                    }} else {{
                        return 'Element not found';
                    }}
                    """)
                    print(f"[INFO] JavaScript result: {js_result}")
                    if "Prompt set" in js_result:
                        success = True
                    methods_tried += 1
                except Exception as e:
                    print(f"[WARNING] JavaScript method failed: {e}")
                
                # Method 2: Try to use fill method if JavaScript failed
                if not success:
                    try:
                        page.fill(exact_prompt_selector, prompt)
                        print("[INFO] Entered prompt using fill method")
                        success = True
                        methods_tried += 1
                    except Exception as e:
                        print(f"[WARNING] Could not fill prompt: {e}")
                
                # Method 3: Try to use type method if previous methods failed
                if not success:
                    try:
                        page.type(exact_prompt_selector, prompt)
                        print("[INFO] Entered prompt using type method")
                        success = True
                        methods_tried += 1
                    except Exception as e:
                        print(f"[WARNING] Could not type prompt: {e}")
                
                # Method 4: Try keyboard shortcuts (Ctrl+A, Delete, then type)
                if not success:
                    try:
                        page.keyboard.press("Control+a")
                        page.keyboard.press("Delete")
                        page.keyboard.type(prompt)
                        print("[INFO] Entered prompt using keyboard shortcuts")
                        success = True
                        methods_tried += 1
                    except Exception as e:
                        print(f"[WARNING] Keyboard method failed: {e}")
                
                if success:
                    print(f"[INFO] Successfully entered prompt after trying {methods_tried} methods")
                else:
                    print("[ERROR] All methods to enter prompt failed")
                    raise Exception("Failed to enter prompt")
                
                # Let the page process the input
                time.sleep(2)
            except Exception as e:
                print(f"[ERROR] Failed to enter prompt: {e}")
                continue
                
            # Click Generate button
            print("[INFO] Looking for Generate button...")
            generate_selector = 'button[data-soft-disabled="false"][type="button"][data-rac]:has-text("Generate")'
            try:
                page.wait_for_selector(generate_selector, timeout=10000)
                print("[INFO] Found Generate button, clicking it...")
                page.click(generate_selector)
                print("[INFO] Clicked Generate button")
                time.sleep(3)  # Wait for the UI to update
            except Exception as e:
                print(f"[ERROR] Failed to click Generate button: {e}")
                # Try a more general selector
                try:
                    fallback_selector = 'button:has-text("Generate")'
                    page.wait_for_selector(fallback_selector, timeout=5000)
                    page.click(fallback_selector)
                    print("[INFO] Clicked Generate button using fallback selector")
                    time.sleep(3)  # Wait for the UI to update
                except Exception as e2:
                    print(f"[ERROR] Fallback also failed: {e2}")
                    continue
            
            # Focus on the virtuoso-item-list element and scroll to see the queue status
            print("[INFO] Focusing on the virtuoso-item-list and scrolling to check queue status...")
            try:
                # First try to focus on the virtuoso-item-list
                virtuoso_item_list = 'div[data-testid="virtuoso-item-list"]'
                if page.is_visible(virtuoso_item_list):
                    # Click on the list to focus it
                    page.click(virtuoso_item_list)
                    print("[INFO] Successfully focused on the virtuoso-item-list")
                    time.sleep(0.5)
                    
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
                    
                    # Scroll up just a little bit (like a mouse wheel)
                    result = page.evaluate(f"""
                    () => {{
                        const list = document.querySelector('{virtuoso_item_list}');
                        if (list) {{
                            // Find the parent scroller
                            const scroller = list.closest('[data-testid="virtuoso-scroller"]');
                            if (scroller) {{
                                // Store current position
                                const currentPos = scroller.scrollTop;
                                // Scroll up just a little bit (150 pixels, like a few mouse wheel scrolls)
                                scroller.scrollTop = currentPos - 150;
                                return `Scrolled up a little from ${{currentPos}} to ${{scroller.scrollTop}}`;
                            }}
                            return "Parent scroller not found";
                        }}
                        return "List not found";
                    }}
                    """)
                    print(f"[INFO] {result}")
                    
                    # Stay at this position for 1 second
                    print("[INFO] Staying at this position for 1 second...")
                    time.sleep(1)
                    
                    # No screenshot needed
                    
                    # Now scroll down aggressively to check for 'In queue' text
                    print("[INFO] Now scrolling down aggressively to check for queue status...")
                    
                    # Scroll down by a large increment
                    result = page.evaluate(f"""
                    () => {{
                        const list = document.querySelector('{virtuoso_item_list}');
                        if (list) {{
                            // Find the parent scroller
                            const scroller = list.closest('[data-testid="virtuoso-scroller"]');
                            if (scroller) {{
                                const currentPos = scroller.scrollTop;
                                // Scroll down by a large increment (1000 pixels)
                                scroller.scrollTop = currentPos + 1000;
                                return `Scrolled down aggressively from ${{currentPos}} to ${{scroller.scrollTop}}`;
                            }}
                            return "Parent scroller not found";
                        }}
                        return "List not found";
                    }}
                    """)
                    print(f"[INFO] {result}")
                    time.sleep(1)  # Give time for content to load
                    
                    # No screenshot needed
                else:
                    print("[WARNING] Virtuoso-item-list not visible, trying general scroll")
                    page.evaluate("window.scrollBy(0, 300)")
                time.sleep(1)
            except Exception as e:
                print(f"[WARNING] Error focusing on virtuoso-item-list: {e}")
                # Fall back to general scroll
                page.evaluate("window.scrollBy(0, 300)")
                time.sleep(1)
            
            # Try multiple selectors to find the queue status
            queue_selectors = [
                'div.percentage-o2hVFS:text("In queue")',  # Direct text match
                'div.percentage-o2hVFS',                   # Class only
                'div.progress-bar-container-lIQqmt div.percentage-o2hVFS'  # Parent-child relationship
            ]
            
            in_queue_found = False
            queue_element = None
            
            # Try each selector until we find the queue status
            for selector in queue_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    print(f"[DEBUG] Found {len(elements)} elements with selector '{selector}'")
                    
                    for element in elements:
                        if element.is_visible():
                            text = element.inner_text().strip()
                            print(f"[DEBUG] Found visible element with text: '{text}'")
                            
                            if "In queue" in text:
                                in_queue_found = True
                                queue_element = element
                                print(f"[INFO] Found 'In queue' status with selector: {selector}")
                                break
                    
                    if in_queue_found:
                        break
                        
                except Exception as e:
                    print(f"[WARNING] Error with selector '{selector}': {e}")
            
            # If we found the queue status
            if in_queue_found:
                print("[INFO] Video is in queue")
                
                # Wait for the video to be ready (check every 30 seconds for up to 2 minutes)
                max_wait_time = 120  # 2 minutes
                start_time = time.time()
                
                while time.time() - start_time < max_wait_time:
                    print("\n[INFO] Checking queue status...")
                    
                    # Perform a more thorough check by scrolling both up and down
                    try:
                        # Focus on the virtuoso-item-list again
                        if page.is_visible(virtuoso_item_list):
                            # Click on the list to focus it
                            page.click(virtuoso_item_list)
                            print("[INFO] Focused on virtuoso-item-list for queue check")
                            time.sleep(0.5)
                            
                            # First scroll up to check for queue message in upper areas
                            print("[INFO] Scrolling up to check for queue message...")
                            page.evaluate(f"""
                            () => {{
                                const list = document.querySelector('{virtuoso_item_list}');
                                if (list) {{
                                    const scroller = list.closest('[data-testid="virtuoso-scroller"]');
                                    if (scroller) {{
                                        const currentPos = scroller.scrollTop;
                                        scroller.scrollTop = currentPos - 300;
                                    }}
                                }}
                            }}
                            """)
                            time.sleep(1)
                            
                            # Check for queue message or percentage
                            still_in_queue = False
                            percentage_text = None
                            
                            # First check for the queue message
                            for selector in queue_selectors:
                                elements = page.query_selector_all(selector)
                                for element in elements:
                                    if element.is_visible():
                                        text = element.inner_text().strip()
                                        if "In queue" in text:
                                            still_in_queue = True
                                            print("[INFO] Video still in queue (found while scrolling up)")
                                            break
                                        elif "%" in text:
                                            still_in_queue = True
                                            percentage_text = text
                                            print(f"[INFO] Video processing: {percentage_text} (found while scrolling up)")
                                            break
                                if still_in_queue:
                                    break
                            
                            # If not found while scrolling up, scroll down to check lower areas
                            if not still_in_queue:
                                print("[INFO] Scrolling down to check for queue message...")
                                page.evaluate(f"""
                                () => {{
                                    const list = document.querySelector('{virtuoso_item_list}');
                                    if (list) {{
                                        const scroller = list.closest('[data-testid="virtuoso-scroller"]');
                                        if (scroller) {{
                                            const currentPos = scroller.scrollTop;
                                            scroller.scrollTop = currentPos + 600; // Scroll down significantly
                                        }}
                                    }}
                                }}
                                """)
                                time.sleep(1)
                                
                                # No screenshot needed
                                
                                # Check again after scrolling down
                                for selector in queue_selectors:
                                    elements = page.query_selector_all(selector)
                                    for element in elements:
                                        if element.is_visible():
                                            text = element.inner_text().strip()
                                            if "In queue" in text:
                                                still_in_queue = True
                                                print("[INFO] Video still in queue (found while scrolling down)")
                                                break
                                            elif "%" in text:
                                                still_in_queue = True
                                                percentage_text = text
                                                print(f"[INFO] Video processing: {percentage_text} (found while scrolling down)")
                                                break
                                    if still_in_queue:
                                        break
                            
                            # If we found the queue message, the video is still processing
                            if still_in_queue:
                                print("[INFO] 'In queue' message found - video is still processing")
                            # If we didn't find any queue messages after scrolling both up and down
                            else:
                                print("[INFO] No 'In queue' message found - video is ready!")
                                return True  # Return True when the queue message disappears
                        else:
                            print("[WARNING] Virtuoso-item-list not visible for queue check")
                    except Exception as e:
                        print(f"[WARNING] Error during queue check scrolling: {e}")
                    
                    # If we're still in the loop, the video is still in queue
                    print("[INFO] Video still in queue, waiting 30 seconds before checking again...")
                    time.sleep(30)  # Wait 30 seconds before checking again
                    
                # If we've waited the maximum time and it's still in queue
                try:
                    if queue_element and queue_element.is_visible() and "In queue" in queue_element.inner_text().strip():
                        print("[WARNING] Video still in queue after maximum wait time")
                    else:
                        print("[INFO] Video is ready after waiting")
                        return True
                except Exception as e:
                    print(f"[WARNING] Error checking final queue status: {e}")
                    return True
            else:
                print("[INFO] Video is not in queue - checking if it's ready")
                time.sleep(5)  # Give it a moment to process
                return True

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
                
                # Test video generation with our default prompt
                print(f"[INFO] Testing video generation with prompt: {DEFAULT_PROMPT}")
                success = generate_video(page, DEFAULT_PROMPT)
                
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