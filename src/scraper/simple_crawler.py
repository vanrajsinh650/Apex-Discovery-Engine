from playwright.sync_api import sync_playwright
import time
from src.common.utils import console, get_random_header

def simple_crawl(url: str, selector: str):
    """
    Crawls a generic directory page using a CSS selector for links.
    """
    console.print(f"[bold blue]Crawling:[/bold blue] {url}")
    unique_links = set()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=get_random_header())
        
        try:
            page.goto(url, timeout=60000)
            time.sleep(5)
            
            # Auto-scroll
            for _ in range(5):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
            
            # Extract
            elements = page.locator(selector).all()
            console.print(f"Found {len(elements)} elements matching '{selector}'")
            
            for el in elements:
                href = el.get_attribute("href")
                if href and href.startswith("http"):
                    unique_links.add(href)
                    console.print(f"Found: {href}")
                    
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            
        browser.close()
        return list(unique_links)

if __name__ == "__main__":
    # Test on a known directory-like page (e.g., a search result from our previous step)
    # Using a MagicBricks or similar URL if available, or just a generic test
    pass
