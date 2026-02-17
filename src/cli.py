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
    headless: bool = typer.Option(True, help="Run in headless mode")
):
    """
    Discover websites matching a query using the Apex Discovery Agent.
    """
    console.print(f"[bold green]Starting Discovery for:[/bold green] {query}")
    
    # search_google now routes to DDG automatically
    urls = search_google(query, limit, headless)
    
    console.print(f"[bold]Found {len(urls)} unique URLs.[/bold]")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output), exist_ok=True)
    
    with open(output, "w") as f:
        json.dump(urls, f, indent=2)
        
    console.print(f"Results saved to [blue]{output}[/blue]")

if __name__ == "__main__":
    app()
