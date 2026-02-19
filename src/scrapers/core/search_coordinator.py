
import asyncio
from src.core.utils import console
from src.scrapers.engines.google_maps import search_google_maps
from src.scrapers.engines.brave import search_brave
from src.scrapers.engines.bing import search_bing
from src.scrapers.engines.duckduckgo import search_ddg

async def run_parallel_searches(query: str, limit: int, headless: bool, output_file: str):
    """
    Runs Brave and Bing in parallel.
    """
    console.print("[bold cyan]Running Brave and Bing in Parallel...[/bold cyan]")
    
    # Brave is primary for organic
    # Bing is secondary/fallback
    
    results = await asyncio.gather(
        search_brave(query, limit, headless, output_file),
        search_bing(query, limit, headless)
    )
    
    # helper to flatten
    flat_results = []
    for r in results:
        flat_results.extend(r)
        
    return flat_results

def search_waterfall(query: str, limit: int = 50, headless: bool = False, output_file: str = "data/websites.json", city: str = None):
    """
    Robust Discovery: Aggregates results from Google Maps (Local) AND Brave+Bing (Organic Parallel).
    """
    console.print(f"[bold magenta]Starting Multi-Source Discovery for: {query}[/bold magenta]")
    
    all_results = []
    
    # 1. Google Maps (Sync, Best for Local)
    try:
        console.print("[bold yellow]1. Google Maps (Local)[/bold yellow]")
        maps_results = search_google_maps(query, limit, headless, city=city)
        if maps_results:
            console.print(f"[green]Maps found {len(maps_results)} links.[/green]")
            all_results.extend(maps_results)
    except Exception as e:
        console.print(f"[dim]Google Maps failed: {e}[/dim]")

    # 2. Parallel Web Search (Brave + Bing)
    try:
        console.print("[bold yellow]2. Organic Web Search (Brave + Bing Parallel)[/bold yellow]")
        web_results = asyncio.run(run_parallel_searches(query, limit, headless, output_file))
        if web_results:
            console.print(f"[green]Web Search found {len(web_results)} links.[/green]")
            all_results.extend(web_results)
    except Exception as e:
        console.print(f"[dim]Web Search failed: {e}[/dim]")
        
    # Deduplicate
    unique_results = list(set(all_results))
    console.print(f"[bold]Total Combined Unique URLs: {len(unique_results)}[/bold]")
        
    return unique_results

# Backwards compatibility
def search_google_fallback(query: str, limit: int = 50, headless: bool = False):
   return search_google_maps(query, limit, headless)

def search_google(query: str, limit: int = 50, headless: bool = True):
    return search_waterfall(query, limit, headless)
