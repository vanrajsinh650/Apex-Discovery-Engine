import sys
import json
import os
from rich.console import Console

from src.cli import app
from src.scraper.engine import search_google

console = Console()

def interactive():
    """
    Run the interactive wizard for the Apex Discovery Agent.
    """
    console.print("[bold green]Apex Discovery Agent - Interactive Mode[/bold green]")
    console.print("This tool will help you discover website URLs for your search query.")
    
    query = input("\nEnter what to find (e.g., 'PG in Ahmedabad', 'Hostels in Mumbai'): ").strip()
    
    if not query:
        console.print("[yellow]No query provided. Exiting.[/yellow]")
        return

    console.print(f"\n[bold blue]Searching for:[/bold blue] {query}...")
    try:
        # Default settings for interactive mode
        limit = 50
        output_file = "data/websites.json"
        
        # Default to Waterfall (Auto)
        from src.scraper.engine import search_waterfall
        urls = search_waterfall(query, limit=limit, headless=False)
        
        urls = search_waterfall(query, limit=limit, headless=False)
        
        if urls:
            console.print(f"\n[bold green]Found {len(urls)} unique URLs from this search.[/bold green]")
            
            from src.common.utils import save_unique_urls
            save_unique_urls(urls, output_file)
        else:
            console.print("\n[bold red]No URLs found.[/bold red]")
            console.print("Note: Search might be blocked on this network. Please check 'data/websites.json' manually.")
            
    except Exception as e:
        console.print(f"[bold red]An error occurred:[/bold red] {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        app()
    else:
        interactive()
