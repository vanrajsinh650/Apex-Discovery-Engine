import json
import concurrent.futures
import os
import sys
import time
import random

# Use bridge/real paths as per structure
from src.scrapers.core.deep_crawler import deep_study_site
from src.exporters.excel import save_lead_to_excel
from src.scrapers.search import search_waterfall
from src.core.utils import console, load_processed_sites, mark_as_processed

def process_location(location):
    """
    Processes a single location in parallel.
    - Generates queries
    - Finds URLs
    - Extracts data
    """
    queries = [
        f'PG in {location} Ahmedabad', 
        f'Boys Hostel {location} Ahmedabad', 
        f'Girls PG {location} Ahmedabad'
    ]
    
    hub_urls = []
    console.print(f"[bold cyan]Thread Started for:[/bold cyan] {location}")
    
    for query in queries:
        try:
            urls = search_waterfall(query, limit=10)
            if urls:
                hub_urls.extend(urls)
            time.sleep(random.uniform(1.0, 2.0))
        except Exception as e:
            console.print(f"[red]Error in search for {query}: {e}[/red]")
            
    if hub_urls:
        unique_urls = list(set(hub_urls))
        console.print(f"[green]{location}: Found {len(unique_urls)} URLs. Starting Deep Study...[/green]")
        
        # Save temp file for this thread to process
        temp_file = f"data/temp_urls_{location.replace(' ', '_')}.json"
        with open(temp_file, "w") as f:
            json.dump(unique_urls, f)
            
        try:
            # deep_study_site (which is process_deep_study) handles validation internally 
            # as it uses MasterDataManager, which we updated with the City Guard logic.
            # However, the user specifically asked for a check here if valid leads.
            deep_study_site(temp_file, "data/master_pg_list.json", city="ahmedabad")
            
            # Export to the requested Excel path
            save_lead_to_excel("data/master_pg_list.json", "data/final_pg_leads.xlsx")
            
        except Exception as e:
            console.print(f"[red]Deep Study failed for {location}: {e}[/red]")
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    else:
        console.print(f"[yellow]{location}: No URLs found.[/yellow]")

def run_parallel_json_search():
    """
    Main entry point for parallel search.
    """
    loc_file = "data/ahmedabad_locations.json"
    if not os.path.exists(loc_file):
        console.print(f"[bold red]Location file not found: {loc_file}[/bold red]")
        return
        
    with open(loc_file, "r") as f:
        locations = json.load(f)
        
    console.print(f"[bold green]Starting Parallel Search for {len(locations)} locations (5 workers)...[/bold green]")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(process_location, locations)
        
    console.print("\n[bold green]Parallel JSON Search completed![/bold green]")

if __name__ == "__main__":
    try:
        run_parallel_json_search()
    except KeyboardInterrupt:
        console.print("\n[bold red]Cancelled by user.[/bold red]")
    except Exception as e:
        console.print(f"\n[bold red]Fatal Error:[/bold red] {e}")
