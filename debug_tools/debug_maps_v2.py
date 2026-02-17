from playwright.sync_api import sync_playwright
import time

def debug_maps():
    # Use exact query format user mentioned
    url = "https://www.google.com/maps/search/pg+and+hostels+in+ahamadabad"
    
    print(f"Navigating to: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # Go to page, wait for DOM
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            print("Navigation complete (DOM loaded).")
            
            # Wait for specific Maps element (e.g., the side panel)
            # Role "feed" usually holds the results
            try:
                page.wait_for_selector('div[role="feed"]', timeout=30000)
                print("Results feed found!")
            except:
                print("Feed not found, taking screenshot.")
            
            time.sleep(5)
            page.screenshot(path="debug_maps_feed.png")
            print("Screenshot saved.")
            
            # Try to grab some text
            titles = page.locator('div[role="article"] >> h3').all_inner_texts()
            print(f"Found {len(titles)} titles: {titles[:5]}")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="debug_maps_retry_error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    debug_maps()
