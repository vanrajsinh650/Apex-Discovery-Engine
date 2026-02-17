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
        limit = 0 # Unlimited by default
        output_file = "data/websites.json"
        
        # Check for existing state
        from src.common.utils import load_crawler_state, reset_crawler_state
        start_page = load_crawler_state(query)
        if start_page > 1:
            console.print(f"[yellow]Previous progress found (Page {start_page}).[/yellow]")
            action = typer.prompt("Resume or Reset?", default="Resume")
            if action.lower() == "reset":
                reset_crawler_state(query)
        
        # Default to Waterfall (Auto)
        from src.scraper.engine import search_waterfall
        urls = search_waterfall(query, limit=limit, headless=False, output_file=output_file)
        

        
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
