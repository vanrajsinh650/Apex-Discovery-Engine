from playwright.sync_api import sync_playwright

def debug_ddg_headless():
    url = "https://html.duckduckgo.com/html/"
    
    with sync_playwright() as p:
        # Mimic search_engine.py (headless=True, no args)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Navigating to DDG HTML (Headless)...")
        try:
            page.goto(url, timeout=30000)
            print("Navigation done.")
            
            # Print UA
            ua = page.evaluate("navigator.userAgent")
            print(f"UA: {ua}")
            
            page.screenshot(path="debug_ddg_headless_initial.png")
            
            # Check for input
            if page.locator("input[name='q']").count() > 0:
                print("Input found.")
            else:
                print("Input NOT found.")
                print("Page content dump:")
                print(page.content()[:500]) # First 500 chars
                
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="debug_ddg_headless_error.png")
            
        browser.close()

if __name__ == "__main__":
    debug_ddg_headless()
