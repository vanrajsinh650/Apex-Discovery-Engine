from playwright.sync_api import sync_playwright
import time

def debug_pagination():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://search.brave.com/search?q=PG+in+Ahmedabad&source=web")
        
        print("Scraping Page 1...")
        time.sleep(3)
        
        # Scroll to bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
        
        # Find Next
        try:
            # Try selector from engine.py
            next_btn = page.locator("a#next").first
            if not next_btn.is_visible():
                print("a#next not visible, trying text...")
                next_btn = page.get_by_role("link", name="Next").first
            
            if next_btn.is_visible():
                print(f"Found Next Button: {next_btn}")
                
                # Check href
                print(f"Next HREF: {next_btn.get_attribute('href')}")
                
                print("Clicking Next...")
                next_btn.click()
                
                print("Waiting for navigation...")
                # Test different waits
                # page.wait_for_load_state("networkidle", timeout=10000) # This failed
                page.wait_for_load_state("domcontentloaded", timeout=10000)
                print("Navigation complete (domcontentloaded).")
                time.sleep(2)
                
                print("Page 2 Title:", page.title())
                
                # Take screenshot
                page.screenshot(path="debug_tools/brave_page_2.png")
            else:
                print("Next button NOT found!")
                page.screenshot(path="debug_tools/brave_no_next.png")
                
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="debug_tools/brave_error.png")
            
        browser.close()

if __name__ == "__main__":
    debug_pagination()
