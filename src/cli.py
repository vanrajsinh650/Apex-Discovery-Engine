import typer
import json
import os
from rich.console import Console
from src.scrapers.core.search_coordinator import search_google
import random

app = typer.Typer()
console = Console()

@app.callback()
def callback():
    pass

@app.command()
def discover(
    query: str = typer.Option(..., help="Search query (e.g., 'PG in Bangalore')"),
    limit: int = typer.Option(0, help="Max number of URLs to find (0 for unlimited)"),
    output: str = typer.Option("data/websites.json", help="Output JSON file"),
    headless: bool = typer.Option(False, help="Run in headless mode (False is safer for stealth)"),
    engine: str = typer.Option("auto", help="Search Engine: 'auto' (default), 'google', 'bing', 'brave', 'ddg'"),
    reset: bool = typer.Option(False, help="Reset progress for this query and start from Page 1")
):
    """
    Discover websites matching a query using the Apex Discovery Agent.
    """
    console.print(f"[bold green]Starting Discovery for:[/bold green] {query} using [bold]{engine}[/bold]")
    
    if reset:
        from src.core.utils import reset_crawler_state
        reset_crawler_state(query)

    urls = []
    if engine.lower() == "auto":
        from src.scrapers.core.search_coordinator import search_waterfall
        urls = search_waterfall(query, limit, headless, output_file=output)
    elif engine.lower() == "bing":
        from src.scrapers.engines.bing import search_bing
        urls = search_bing(query, limit, headless)
    elif engine.lower() == "google":
        from src.scrapers.core.search_coordinator import search_google_fallback
        urls = search_google_fallback(query, limit, headless)
    elif engine.lower() == "brave":
        from src.scrapers.engines.brave import search_brave
        urls = search_brave(query, limit, headless, output_file=output)
    elif engine.lower() == "ddg":
        from src.scrapers.engines.duckduckgo import search_ddg
        urls = search_ddg(query, limit, headless)
    else:
        console.print(f"[red]Unknown engine: {engine}. Defaulting to Auto Waterfall.[/red]")
        from src.scrapers.core.search_coordinator import search_waterfall
        urls = search_waterfall(query, limit, headless, output_file=output)
    
    console.print(f"[bold]Found {len(urls)} unique URLs from this search.[/bold]")
    
    from src.core.utils import save_unique_urls
    save_unique_urls(urls, output)

@app.command()
def extract(
    input: str = typer.Option("data/websites.json", help="Input JSON file with URLs"),
    output: str = typer.Option("data/master_pg_list.json", help="Output Master List JSON"),
    fresh: bool = typer.Option(False, help="Delete processed log and start fresh")
):
    """
    Deep Scan websites for contact info (BFS: Home -> Contact/About).
    """
    
    if fresh:
        processed_file = "data/processed_sites.txt"
        if os.path.exists(processed_file):
            os.remove(processed_file)
            console.print(f"[bold yellow]Deleted {processed_file}. Starting Fresh![/bold yellow]")
            
    from src.scrapers.core.deep_crawler import process_deep_study
    process_deep_study(input, output)

@app.command()
def export(
    input: str = typer.Option("data/pg.json", help="Input JSON file from extractor"),
    output: str = typer.Option("data/pg_data.xlsx", help="Output Excel file path")
):
    """
    Deduplicate and Export PG Data to Excel.
    """
    from src.exporters.excel import export_to_excel_perfect
    export_to_excel_perfect(input, output)

@app.command()
def maps(
    query: str = typer.Option(..., help="Search query (e.g., 'PG in Ahmedabad')"),
    limit: int = typer.Option(50, help="Max number of records to find"),
    output: str = typer.Option("data/master_pg_list.json", help="Output JSON file"),
    headless: bool = typer.Option(False, help="Run in headless mode (False recommended for Maps)")
):
    """
    Scrape Google Maps Side Panel for Direct Phone Numbers.
    """
    from src.scrapers.engines.google_maps import search_google_maps
    search_google_maps(query, limit, headless, output)

@app.command()
def enrich(
    input: str = typer.Option(..., help="Input Excel/CSV file with Name and Location columns"),
    output: str = typer.Option(None, help="Output file path (optional)")
):
    """
    Find missing contact numbers for a list of PGs/Businesses.
    """
    from src.scrapers.core.enricher import enrich_data
    enrich_data(input, output)


@app.command()
def harvest(
    city: str = typer.Option(..., help="City name to harvest locations for (e.g., 'Ahmedabad')")
):
    """
    Scrape Google Maps for high-density locations (Suburbs, Bus Stops, Colleges) to build a target list.
    """
    from src.scrapers.core.harvester import LocationHarvester
    harvester = LocationHarvester(city)
    harvester.harvest()

@app.command()
def run_all(
    query: str = typer.Option(None, help="Search query. If None, runs default batch."),
    limit: int = typer.Option(50, help="Limit for search results"),
    fresh: bool = typer.Option(False, help="Delete processed log and start fresh"),
    use_harvested: bool = typer.Option(False, help="Use harvested location keywords for massive coverage"),
    city: str = typer.Option("Ahmedabad", help="City to use for harvested keywords")
):
    """
    Executes the full pipeline: Discovery -> Deep Study -> Maps Verification -> Export.
    """
    
    if fresh:
        processed_file = "data/processed_sites.txt"
        status_file = "data/run_all_status.json"
        for f_path in [processed_file, status_file]:
            if os.path.exists(f_path):
                os.remove(f_path)
        console.print(f"[bold yellow]Cleaned state. Starting Fresh![/bold yellow]")

    # Load Progress
    completed_queries = set()
    status_file = "data/run_all_status.json"
    if os.path.exists(status_file):
        with open(status_file, "r") as f:
            completed_queries = set(json.load(f))

    queries = []
    # ... (Query generation logic remains the same)
    if query:
        queries = [query]
    else:
        # Default Batch
        queries = [
            f"pg in navrangpura {city}", 
            f"boys hostel s.g. highway {city}", 
            f"girls pg satellite {city}", 
            f"paying guest near nirma university {city}", 
            f"hostel in gurukul {city}"
        ]
        
    if use_harvested:
        json_path = f"data/{city.lower().replace(' ', '_')}_locations.json"
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                locs = json.load(f)
            
            # Generate Queries
            new_queries = []
            for loc in locs:
                new_queries.append(f"PG in {loc} {city}")
                new_queries.append(f"Boys Hostel near {loc} {city}")
                new_queries.append(f"Girls PG in {loc} {city}")
                
            queries.extend(new_queries)
            # Randomize to avoid pattern blocks
            random.shuffle(queries)
            
            # DEBUG Stats per User Phase 4
            console.print(f"[bold yellow][Harvested Locations: {len(locs)}] -> [Queries Generated: {len(new_queries)}][/bold yellow]")
        else:
            console.print(f"[red]Harvest file not found: {json_path}. Run 'python main.py harvest --city \"{city}\"' first.[/red]")

    # Filter out completed queries
    total_queries = len(queries)
    queries = [q for q in queries if q not in completed_queries]
    
    if total_queries > len(queries):
        console.print(f"[bold green]Skipping {total_queries - len(queries)} areas already completed.[/bold green]")

    console.print(f"[bold magenta]Starting Full Run for {len(queries)} remaining queries...[/bold magenta]")
    
    for i, q in enumerate(queries):
        console.print(f"\n[bold cyan]Processing Batch {i+1}/{len(queries)}: {q}[/bold cyan]")
        
        # Step 1: Discovery (Waterfal)
        console.print(f"\n[bold]Step 1: Discovery ({q})[/bold]")
        found_urls = []
        try:
            from src.scrapers.core.search_coordinator import search_waterfall
            found_urls = search_waterfall(q, limit=limit, city=city)
        except Exception as e:
            console.print(f"[red]Step 1 Failed: {e}[/red]")

        # Step 2: Deep Study
        if found_urls:
            console.print(f"\n[bold]Step 2: Deep Study (Enriching {len(found_urls)} new links)[/bold]")
            try:
                from src.scrapers.core.deep_crawler import process_deep_study
                process_deep_study(input_file="data/websites.json", output_file="data/master_pg_list.json", city=city)
            except Exception as e:
                console.print(f"[red]Step 2 Failed: {e}[/red]")
        else:
            console.print("[dim]No new website URLs to study in Step 2.[/dim]")

        # Step 3: Incremental Export (Refresh Excel after every batch)
        console.print(f"\n[bold yellow]Step 3: Refreshing Excel Export...[/bold yellow]")
        try:
            from src.exporters.excel import export_to_excel
            export_to_excel(input_file="data/master_pg_list.json", output_file="data/verified_pg_database.xlsx")
            
            # Record Success
            completed_queries.add(q)
            with open(status_file, "w") as f:
                json.dump(list(completed_queries), f)
                
        except Exception as e:
            console.print(f"[dim red]Incremental export failed: {e}[/dim red]")

    console.print(f"\n[bold green]Full Run Complete! All results are in 'data/verified_pg_database.xlsx'.[/bold green]")

if __name__ == "__main__":
    app()
