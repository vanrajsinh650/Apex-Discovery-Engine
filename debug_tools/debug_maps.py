from playwright.sync_api import sync_playwright
import time
import random

def debug_maps():
    query = "PG in Ahmedabad"
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
    
    print(f"Navigating to: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # Headless False to see interaction
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            page.goto(url, timeout=60000)
            print("Navigation complete.")
            page.wait_for_load_state("networkidle")
            print("Network idle.")
            
            # Additional wait for content
            time.sleep(5)
            page.screenshot(path="debug_maps_success.png")
            
            # Simple selector strategy: look for links that are NOT internal google maps nav links
            # This is tricky in maps. Let's dump titles first.
            
            # Try to identify main listing text
            # Usually div[role="article"] contains the listing
            articles = page.locator('div[role="article"]').all()
            print(f"Found {len(articles)} articles (initially).")
            
            for i, article in enumerate(articles[:5]):
                try:
                    text = article.inner_text().split('\n')[0]
                    print(f"Listing {i}: {text}")
                    
                    # Try to find a website link inside?
                    # usually a.lcr4fd (changes often)
                    # Let's look for any 'a' tag with http that isn't google.
                    links = article.locator("a").all()
                    for l in links:
                        href = l.get_attribute("href")
                        if href and "google.com" not in href and "http" in href:
                            print(f"  -> Website: {href}")
                except:
                    pass
            
            page.screenshot(path="debug_maps_result.png")
            print("Saved screenshot.")
            
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="debug_maps_error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    debug_maps()
