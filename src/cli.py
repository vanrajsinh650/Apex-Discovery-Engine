import typer
import json
import os
from rich.console import Console
from src.scrapers.search import search_google

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
        from src.scrapers.search import search_waterfall
        urls = search_waterfall(query, limit, headless, output_file=output)
    elif engine.lower() == "bing":
        from src.scrapers.bing import search_bing
        urls = search_bing(query, limit, headless)
    elif engine.lower() == "google":
        from src.scrapers.search import search_google_fallback
        urls = search_google_fallback(query, limit, headless)
    elif engine.lower() == "brave":
        from src.scrapers.brave import search_brave
        urls = search_brave(query, limit, headless, output_file=output)
    elif engine.lower() == "ddg":
        from src.scrapers.duckduckgo import search_ddg
        urls = search_ddg(query, limit, headless)
    else:
        console.print(f"[red]Unknown engine: {engine}. Defaulting to Auto Waterfall.[/red]")
        from src.scrapers.search import search_waterfall
        urls = search_waterfall(query, limit, headless, output_file=output)
    
    console.print(f"[bold]Found {len(urls)} unique URLs from this search.[/bold]")
    
    from src.core.utils import save_unique_urls
    save_unique_urls(urls, output)

@app.command()
def extract(
    input: str = typer.Option("data/websites.json", help="Input JSON file with URLs"),
    output: str = typer.Option("data/master_pg_list.json", help="Output Master List JSON")
):
    """
    Deep Scan websites for contact info (BFS: Home -> Contact/About).
    """
    from src.scrapers.deep_crawler import process_deep_study
    process_deep_study(input, output)

@app.command()
def export(
    input: str = typer.Option("data/pg.json", help="Input JSON file from extractor"),
    output: str = typer.Option("data/pg_data.xlsx", help="Output Excel file path")
):
    """
    Deduplicate and Export PG Data to Excel.
    """
    from src.exporters.excel import export_to_excel
    export_to_excel(input, output)

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
    from src.scrapers.maps import search_google_maps
    search_google_maps(query, limit, headless, output)

@app.command()
def enrich(
    input: str = typer.Option(..., help="Input Excel/CSV file with Name and Location columns"),
    output: str = typer.Option(None, help="Output file path (optional)")
):
    """
    Find missing contact numbers for a list of PGs/Businesses.
    """
    from src.scrapers.enricher import enrich_data
    enrich_data(input, output)


@app.command()
def run_all(
    query: str = typer.Option(None, help="Search query (e.g., 'PG in Ahmedabad'). If None, runs default batch."),
    limit: int = typer.Option(50, help="Limit for search results"),
):
    """
    Executes the full pipeline: Discovery -> Deep Study -> Maps Verification -> Export.
    Runs a batch of 5 high-value queries if no query is provided.
    """
    
    queries = [query] if query else [
        "pg in navrangpura ahmedabad", 
        "boys hostel s.g. highway", 
        "girls pg satellite ahmedabad", 
        "paying guest near nirma university", 
        "hostel in gurukul ahmedabad"
    ]

    console.print(f"[bold magenta]Starting Full Run for {len(queries)} queries...[/bold magenta]")
    
    for i, q in enumerate(queries):
        console.print(f"\n[bold cyan]Processing Batch {i+1}/{len(queries)}: {q}[/bold cyan]")
        
        # Step 1: Discovery (Waterfal)
        console.print(f"\n[bold]Step 1: Discovery ({q})[/bold]")
        try:
            from src.scrapers.search import search_waterfall
            search_waterfall(q, limit=limit)
        except Exception as e:
            console.print(f"[red]Step 1 Failed: {e}[/red]")

        # Step 2: Deep Study
        console.print(f"\n[bold]Step 2: Deep Study (Enrichment)[/bold]")
        try:
            from src.scrapers.deep_crawler import process_deep_study
            # Reads websites.json -> updates master_pg_list.json
            process_deep_study(input_file="data/websites.json", output_file="data/master_pg_list.json")
        except Exception as e:
            console.print(f"[red]Step 2 Failed: {e}[/red]")

        # Step 3: Maps Verification
        console.print(f"\n[bold]Step 3: Maps Verification ({q})[/bold]")
        try:
            from src.scrapers.maps import search_google_maps
            # Upserts to master_pg_list.json
            search_google_maps(q, limit=limit, headless=False, output_file="data/master_pg_list.json")
        except Exception as e:
            console.print(f"[red]Step 3 Failed: {e}[/red]")

    # Step 4: Final Export
    console.print("\n[bold]Step 4: Final Export[/bold]")
    try:
        from src.exporters.excel import export_to_excel
        export_to_excel(input_file="data/master_pg_list.json", output_file="data/verified_pg_database.xlsx")
    except Exception as e:
        console.print(f"[black on red]Step 4 Failed: {e}[/black on red]")

    console.print(f"\n[bold green]Full Run Complete! Check 'data/verified_pg_database.xlsx'.[/bold green]")

if __name__ == "__main__":
    app()
