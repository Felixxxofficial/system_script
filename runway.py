import os
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Runway credentials from environment variables
RUNWAY_EMAIL = os.getenv("RUNWAY_EMAIL")
RUNWAY_PASSWORD = os.getenv("RUNWAY_PASSWORD")

# List of prompts to cycle through (can be expanded)
PROMPTS = [
    "A serene beach at sunset with waves crashing gently",
    "A futuristic cityscape with flying cars at night",
    "A cozy cabin in a snowy forest with a warm fireplace"
]
PROMPT_INDEX = 0

def login(page):
    """Log into Runway account."""
    page.goto("https://app.runwayml.com/login")
    page.fill('input[name="email"]', RUNWAY_EMAIL)
    page.fill('input[name="password"]', RUNWAY_PASSWORD)
    page.click('button[type="submit"]')
    # Wait for dashboard to load
    page.wait_for_url("https://app.runwayml.com/**", timeout=30000)
    print("Logged in successfully")

def navigate_to_video_generation(page):
    """Navigate to the Gen-3 Alpha or Gen-4 video generation page."""
    # Go to Generative Video section
    page.goto("https://app.runwayml.com/video")
    # Ensure Gen-3 Alpha or Gen-4 is selected (assuming default or dropdown)
    try:
        page.wait_for_selector('select[model-selector]', timeout=10000)
        page.select_option('select[model-selector]', 'Gen-3 Alpha')  # Adjust if Gen-4 is needed
        print("Selected video generation model")
    except PlaywrightTimeoutError:
        print("Model selector not found, assuming default model")

def submit_prompt(page, prompt):
    """Input prompt and generate two videos."""
    try:
        # Locate the prompt input field
        prompt_input = page.locator('textarea[placeholder*="Enter a prompt"]')
        prompt_input.fill(prompt)
        # Click the generate button
        page.click('button:has-text("Generate")')
        print(f"Submitted prompt: {prompt}")
        # Wait for generation to start (queue confirmation)
        page.wait_for_selector('div.queue-status', timeout=20000)
        print("Video generation queued")
    except PlaywrightTimeoutError:
        print("Failed to submit prompt or queue videos")
        raise

def monitor_queue(page):
    """Monitor the generation queue and wait until slots are available."""
    while True:
        try:
            # Check if queue is full (assuming 2 videos max)
            queue_status = page.locator('div.queue-status').inner_text()
            if "2/2" in queue_status:
                print("Queue full, waiting for slots...")
                time.sleep(30)  # Check every 30 seconds
            else:
                print("Queue has available slots")
                break
        except PlaywrightTimeoutError:
            print("Queue status not found, assuming slots available")
            break

def main():
    global PROMPT_INDEX
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Headful for debugging
        context = browser.new_context()
        page = context.new_page()

        try:
            # Log in
            login(page)
            # Navigate to video generation
            navigate_to_video_generation(page)

            # Main loop to generate videos
            while True:
                # Get current prompt
                prompt = PROMPTS[PROMPT_INDEX % len(PROMPTS)]
                PROMPT_INDEX += 1

                # Submit prompt and generate videos
                submit_prompt(page, prompt)
                
                # Monitor queue until slots are available
                monitor_queue(page)
                
                # Add delay to respect server load
                print("Waiting before next generation...")
                time.sleep(60)  # Wait 1 minute between cycles

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    if not RUNWAY_EMAIL or not RUNWAY_PASSWORD:
        raise ValueError("Please set RUNWAY_EMAIL and RUNWAY_PASSWORD in .env file")
    main()