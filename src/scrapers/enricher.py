import pandas as pd
import time
import re
import os
import json
from rich.console import Console
from src.core.utils import get_random_header, random_delay, normalize_url
from src.scrapers.maps import search_google_maps
from src.scrapers.brave import search_brave
from src.scrapers.bing import search_bing
from src.scrapers.listing import extract_pg_data, clean_phone, PHONE_REGEX

console = Console()

def enrich_data(input_file: str, output_file: str = None):
    """
    Reads an Excel/CSV file, finds missing contact info for PGs,
    and saves the enriched data.
    """
    if not os.path.exists(input_file):
        console.print(f"[red]Input file {input_file} not found.[/red]")
        return

    # Load Data
    try:
        if input_file.endswith(".csv"):
            df = pd.read_csv(input_file)
        else:
            df = pd.read_excel(input_file)
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        return

    console.print(f"[bold blue]Loaded {len(df)} records from {input_file}.[/bold blue]")

    # Ensure columns exist
    if "Contact_Number" not in df.columns:
        df["Contact_Number"] = ""
    if "Source_Link" not in df.columns:
        df["Source_Link"] = ""
    if "Enrichment_Status" not in df.columns:
        df["Enrichment_Status"] = ""

    # Identify columns for Name and Location
    # Heuristic: Find first column with "Name" or "PG" and "Address" or "Location"
    name_col = next((col for col in df.columns if "name" in col.lower() or "pg" in col.lower()), None)
    loc_col = next((col for col in df.columns if "address" in col.lower() or "location" in col.lower() or "city" in col.lower()), None)

    if not name_col:
        console.print("[red]Could not identify a 'Name' column. Please rename columns in your file.[/red]")
        return
        
    console.print(f"[green]Using Name Column: {name_col}[/green]")
    if loc_col:
        console.print(f"[green]Using Location Column: {loc_col}[/green]")
    else:
        console.print("[yellow]No Location column found. Using Name only.[/yellow]")

    # Iterate and Enrich
    total_found = 0
    
    # Determine output file name
    if not output_file:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_enriched{ext}"

    for index, row in df.iterrows():
        # Skip if already has number (optional, user might want to overwrite? Assuming fill gaps)
        current_number = str(row["Contact_Number"])
        if current_number and current_number != "nan" and len(clean_phone(current_number) or "") == 10:
             continue
             
        name = str(row[name_col]).strip()
        location = str(row[loc_col]).strip() if loc_col else ""
        
        if not name or name == "nan": continue

        query = f"{name} {location}".strip()
        console.print(f"\n[bold]Enriching item {index+1}/{len(df)}:[/bold] {query}")
        
        found_phone = None
        found_source = None
        method = ""

        # Strategy 1: Google Maps (High Precision)
        try:
            # We use a strict limit of 1 to find the specific place
            # scrape_google_maps matches query. 
            maps_results = search_google_maps(query, limit=1, headless=True) 
            if maps_results:
                res = maps_results[0]
                if res.get("phone"):
                    p = clean_phone(res["phone"])
                    if p:
                        found_phone = p
                        found_source = "Google Maps"
                        method = "Maps"
                        console.print(f"   [green]Found via Maps: {p}[/green]")
        except Exception as e:
            console.print(f"   [dim]Maps error: {e}[/dim]")

        # Strategy 2: Web Search (Brave/Bing) - ALWAYS RUN per user request
        # "if google map works or not you need go on brave"
        web_phone = None
        web_source_url = None
        
        try:
            search_q = f"{query} contact number"
            urls = search_brave(search_q, limit=3, headless=True)
            if not urls:
                 # Fallback to Bing
                 urls = search_bing(search_q, limit=3, headless=True)
            
            if urls:
                # Visit top result
                top_url = urls[0]
                # console.print(f"   [dim]Checking Web: {top_url}...[/dim]")
                
                # Extract from page
                pg_data = extract_pg_data(top_url, headless=True)
                if pg_data:
                    for item in pg_data:
                        if item.get("mobile"):
                            web_phone = item["mobile"][0] 
                            web_source_url = top_url
                            
                            if not found_phone:
                                console.print(f"   [green]Found via Web: {web_phone}[/green]")
                            else:
                                console.print(f"   [dim]Web also found: {web_phone}[/dim]")
                            break
        except Exception as e:
            console.print(f"   [dim]Web search error: {e}[/dim]")
            
        # Consolidation: Prefer Maps, fallback to Web
        if not found_phone and web_phone:
            found_phone = web_phone
            found_source = web_source_url
            method = "Web Crawl"
        elif found_phone and web_phone and found_phone != web_phone:
             # If mismatch, maybe store both? 
             # For now, Maps is trusted source.
             pass

        # Update Row
        if found_phone:
            df.at[index, "Contact_Number"] = found_phone
            df.at[index, "Source_Link"] = found_source
            df.at[index, "Enrichment_Status"] = f"Found via {method}"
            total_found += 1
        else:
            df.at[index, "Enrichment_Status"] = "Not Found"
            
        # Periodic Save (Every 5 rows)
        if (index + 1) % 5 == 0:
            console.print(f"[dim]Saving progress to {output_file}...[/dim]")
            if output_file.endswith(".csv"):
                df.to_csv(output_file, index=False)
            else:
                df.to_excel(output_file, index=False)

    # Final Save
    if output_file.endswith(".csv"):
        df.to_csv(output_file, index=False)
    else:
        df.to_excel(output_file, index=False)
        
    console.print(f"[bold green]Enrichment Complete![/bold green]")
    console.print(f"Stats: Found numbers for {total_found} listings.")
    console.print(f"Saved to: {output_file}")
