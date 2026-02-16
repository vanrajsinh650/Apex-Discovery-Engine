import typer
from rich.console import Console
from playwright.sync_api import sync_playwright
import json
try:
    from .search_engine import search_google
except ImportError:
    from search_engine import search_google

app = typer.Typer()
console = Console()

@app.command()
def search(
    keyword: str = typer.Option(..., help="Search keyword"),
    location: str = typer.Option(..., help="Search location"),
    headless: bool = typer.Option(True, help="Run in headless mode")
):
    """
    [Legacy] Scrape local businesses from Google Maps.
    """
    console.print(f"[bold green]Starting Maps scraper for:[/bold green] {keyword} in {location}")
    
    url = f"https://www.google.com/maps/search/{keyword}+in+{location}"
    console.print(f"Navigating to: [blue]{url}[/blue]")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        
        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle")
            
            title = page.title()
            console.print(f"Page Title: [bold]{title}[/bold]")
            
            # Temporary: just take a screenshot to prove it works
            screenshot_path = "debug_screenshot.png"
            page.screenshot(path=screenshot_path)
            console.print(f"Screenshot saved to {screenshot_path}")
            
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
        finally:
            browser.close()
    
@app.command()
def discover(
    query: str = typer.Option(..., help="Search query (e.g., 'PG in Bangalore')"),
    limit: int = typer.Option(50, help="Max number of URLs to find"),
    output: str = typer.Option("data/websites.json", help="Output JSON file"),
    headless: bool = typer.Option(True, help="Run in headless mode")
):
    """
    Discover websites matching a query using Google Search.
    """
    console.print(f"[bold green]Starting Discovery for:[/bold green] {query}")
    
    urls = search_google(query, limit, headless)
    
    console.print(f"[bold]Found {len(urls)} unique URLs.[/bold]")
    
    with open(output, "w") as f:
        json.dump(urls, f, indent=2)
        
    console.print(f"Results saved to [blue]{output}[/blue]")

if __name__ == "__main__":
    app()
