import typer
import json
import os
from rich.console import Console
from src.scraper.engine import search_google

app = typer.Typer()
console = Console()

@app.callback()
def callback():
    """
    Apex Discovery Engine CLI
    """
    pass

@app.command()
def discover(
    query: str = typer.Option(..., help="Search query (e.g., 'PG in Bangalore')"),
    limit: int = typer.Option(50, help="Max number of URLs to find"),
    output: str = typer.Option("data/websites.json", help="Output JSON file"),
    headless: bool = typer.Option(False, help="Run in headless mode (False is safer for stealth)"),
    engine: str = typer.Option("auto", help="Search Engine: 'auto' (default), 'google', 'bing', 'brave', 'ddg'")
):
    """
    Discover websites matching a query using the Apex Discovery Agent.
    """
    console.print(f"[bold green]Starting Discovery for:[/bold green] {query} using [bold]{engine}[/bold]")
    
    urls = []
    if engine.lower() == "auto":
        from src.scraper.engine import search_waterfall
        urls = search_waterfall(query, limit, headless)
    elif engine.lower() == "bing":
        from src.scraper.engine import search_bing
        urls = search_bing(query, limit, headless)
    elif engine.lower() == "google":
        from src.scraper.engine import search_google_fallback
        urls = search_google_fallback(query, limit, headless)
    elif engine.lower() == "brave":
        from src.scraper.engine import search_brave
        urls = search_brave(query, limit, headless)
    elif engine.lower() == "ddg":
        from src.scraper.engine import search_ddg
        urls = search_ddg(query, limit, headless)
    else:
        console.print(f"[red]Unknown engine: {engine}. Defaulting to Auto Waterfall.[/red]")
        from src.scraper.engine import search_waterfall
        urls = search_waterfall(query, limit, headless)
    
    console.print(f"[bold]Found {len(urls)} unique URLs from this search.[/bold]")
    
    from src.common.utils import save_unique_urls
    save_unique_urls(urls, output)

if __name__ == "__main__":
    app()
