from playwright.sync_api import sync_playwright
import time

def inspect_brave():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        print("Navigating to Brave Search...")
        page.goto("https://search.brave.com/search?q=PG+in+Ahmedabad", timeout=60000)
        time.sleep(5)
        
        # Try to find result links
        # Brave structure often uses a specific class for result containers
        # Let's try generic first
        links = page.locator("a").all()
        print(f"Found {len(links)} links total.")
        
        # Look for search result specific patterns
        # Typically inside a container like #results or .snippet
        
        # Dump HTML to file for inspection
        with open("debug_tools/brave_search.html", "w") as f:
            f.write(page.content())
            
        print("Saved HTML to debug_tools/brave_search.html")
        browser.close()

if __name__ == "__main__":
    inspect_brave()
