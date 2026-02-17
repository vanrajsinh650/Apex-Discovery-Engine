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
    
    # 1. Get input from user
    query = input("\nEnter what to find (e.g., 'PG in Ahmedabad', 'Hostels in Mumbai'): ").strip()
    
    if not query:
        console.print("[yellow]No query provided. Exiting.[/yellow]")
        return

    # 2. Run search
    console.print(f"\n[bold blue]Searching for:[/bold blue] {query}...")
    try:
        # Default settings for interactive mode
        limit = 50
        output_file = "data/websites.json"
        
        # search_google now routes to DDG automatically
        urls = search_google(query, limit=limit, headless=True)
        
        # 3. Save results
        if urls:
            console.print(f"\n[bold green]Found {len(urls)} unique URLs.[/bold green]")
            
            # Ensure data directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, "w") as f:
                json.dump(urls, f, indent=2)
            console.print(f"Results saved to [bold]{output_file}[/bold]")
        else:
            console.print("\n[bold red]No URLs found.[/bold red]")
            console.print("Note: Search might be blocked on this network. Please check 'data/websites.json' manually.")
            
    except Exception as e:
        console.print(f"[bold red]An error occurred:[/bold red] {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # User provided arguments (e.g., `python main.py discover ...`)
        app()
    else:
        # No arguments, run interactive wizard
        interactive()
