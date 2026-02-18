from src.core.utils import console
from src.scrapers.maps import search_google_maps
from src.scrapers.brave import search_brave
from src.scrapers.bing import search_bing
from src.scrapers.duckduckgo import search_ddg

def search_waterfall(query: str, limit: int = 50, headless: bool = False, output_file: str = "data/websites.json"):
    """
    Robust Discovery: Aggregates results from Google Maps (Local) AND Brave (Organic).
    Get EVERYTHING: Maps + Websites.
    """
    console.print(f"[bold magenta]Starting Multi-Source Discovery for: {query}[/bold magenta]")
    
    all_results = []
    
    # 1. Google Maps (Best for Local/PGs)
    try:
        maps_results = search_google_maps(query, limit, headless)
        if maps_results:
            console.print(f"[green]Maps found {len(maps_results)} links.[/green]")
            all_results.extend(maps_results)
    except Exception as e:
        console.print(f"[dim]Google Maps failed: {e}[/dim]")

    # 2. Brave Search (Best for Aggregators/Directories like Justdial)
    # We always run this too, to get the "websites" the user requested.
    try:
        organic_limit = limit 
        # If limit is 0, we pass 0 (unlimited) to Brave
        
        console.print("[bold orange3]Now searching Organic Results (Websites/Directories)...[/bold orange3]")
        brave_results = search_brave(query, organic_limit, headless, output_file)
        if brave_results:
             console.print(f"[green]Brave found {len(brave_results)} organic links.[/green]")
             all_results.extend(brave_results)
    except Exception as e:
        console.print(f"[dim]Brave failed: {e}[/dim]")
        
    # 3. Fallback to Bing if total is low?
    if len(all_results) < 5:
         console.print("[yellow]Low results. Adding Bing Search...[/yellow]")
         try:
             bing_results = search_bing(query, limit, False)
             if bing_results:
                 all_results.extend(bing_results)
         except:
             pass

    # Deduplicate
    unique_results = list(set(all_results))
    console.print(f"[bold]Total Combined Unique URLs: {len(unique_results)}[/bold]")
        
    return unique_results

def search_google_fallback(query: str, limit: int = 50, headless: bool = False):
   # Redirect to Maps scraper as it is superior
   return search_google_maps(query, limit, headless)

# Keep search_google for backward compatibility if needed, but waterfall handles it
def search_google(query: str, limit: int = 50, headless: bool = True):
    return search_waterfall(query, limit, headless)
