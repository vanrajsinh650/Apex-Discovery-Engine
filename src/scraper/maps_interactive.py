from playwright.sync_api import sync_playwright
import time
from src.common.utils import console, get_random_header, random_delay

def scrape_google_maps_interactive(limit: int = 50):
    """
    Interactive Google Maps Scraper.
    User performs the search, we scrape the results.
    """
    console.print(f"[bold blue]Starting Interactive Google Maps Scraper...[/bold blue]")
    unique_places = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()
        
        console.print("[yellow]Navigate to Google Maps and SEARCH for your query manually![/yellow]")
        page.goto("https://www.google.com/maps", timeout=60000)
        
        # Wait for user to search
        console.print("[bold green]Waiting for you to search... (Press Enter in terminal when results are loaded)[/bold green]")
        input("Press Enter AFTER results appear in the sidebar...")
        
        console.print("[bold]Starting extraction...[/bold]")
        
        # We need to find the scrollable feed div
        # Common Strategy: identifying the div that contains the results
        # Usually it has role='feed'
        
        try:
            # Try to find the feed element
            # This selector is tricky and changes often. 
            # We look for a div with role 'feed'
            feed = page.locator("div[role='feed']").first
            
            if not feed.is_visible():
                console.print("[red]Could not auto-detect result feed. Trying fallback...[/red]")
                # Fallback: Look for the container of the first result
                first_result = page.locator("a[href*='/maps/place/']").first
                if first_result.is_visible():
                    # The feed is likely a parent of this
                    feed = first_result.locator("xpath=./ancestor::div[contains(@role, 'feed')]")
            
            if not feed.count():
                console.print("[bold red]Critical: Result feed not found. Aborting.[/bold red]")
                # Dump HTML for debugging
                page.screenshot(path="debug_tools/maps_failed_feed.png")
                with open("debug_tools/maps_failed_feed.html", "w") as f:
                    f.write(page.content())
                return []
            console.print("[green]Feed found. Scrolling...[/green]")
            
            while len(unique_places) < limit:
                # Extract current visible results
                # Class 'hfpxzc' is the link overlay for places (headless)
                # Class 'Nv2PK' is the card container
                
                places = page.locator("a[href*='/maps/place/']").all()
                new_count = 0
                
                for place in places:
                    url = place.get_attribute("href")
                    # Clean URL (remove query params mostly)
                    if url:
                        url = url.split("?")[0]
                        
                        # Get Title (aria-label usually has it)
                        title = place.get_attribute("aria-label")
                        
                        if url not in unique_places:
                            unique_places[url] = title
                            new_count += 1
                            console.print(f"Found: [bold]{title}[/bold] ({url})")
                
                if len(unique_places) >= limit:
                    break
                    
                # Scroll down
                # We need to scroll the FEED element, not the window
                feed.evaluate("el => el.scrollBy(0, 1000)")
                time.sleep(2)
                
                # Check end of list detection (omitted for simple version)
                if new_count == 0:
                     # Attempt more aggressive scroll or wait
                     time.sleep(2)
                     feed.evaluate("el => el.scrollBy(0, 2000)")
                     
        except Exception as e:
            console.print(f"[red]Error during scraping: {e}[/red]")
            
        console.print(f"Captured {len(unique_places)} places.")
        browser.close()
        return list(unique_places.keys())

if __name__ == "__main__":
    scrape_google_maps_interactive()
