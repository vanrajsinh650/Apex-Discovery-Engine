import time
import random
import os
from src.core.utils import console
from src.scraper.engine import search_waterfall, process_deep_study
from src.scraper.utils import save_lead_to_excel

# Hardcoded High-Density Hubs
AHMEDABAD_HUBS = [
    'Nirma University', 'IIM Ahmedabad', 'Gujarat University', 
    'LD College of Engineering', 'Silver Oak University', 'St Xaviers College', 
    'Geeta Mandir Bus Station', 'Nehrunagar GSRTC', 'Kalupur Railway Station', 
    'Prahlad Nagar', 'Satellite', 'Bodakdev', 'Thaltej', 'Gota', 'Vastrapur', 
    'Navrangpura', 'Paldi', 'Maninagar', 'Bopal', 'Science City Road', 'SG Highway'
]

def run_fast_hub_discovery():
    """
    Iterates through hubs and discovers PG leads with strict validation.
    """
    console.print("[bold green]Starting Fast Hub Discovery for Ahmedabad...[/bold green]")
    
    master_output = "data/master_pg_list.json"
    excel_output = "data/perfect_pg_list.xlsx"
    temp_urls = "data/websites.json"

    for hub in AHMEDABAD_HUBS:
        queries = [
            f'PG near {hub} Ahmedabad',
            f'Boys Hostel near {hub} Ahmedabad',
            f'Girls PG in {hub} Ahmedabad'
        ]
        
        console.print(f"\n[bold cyan]Processing Hub:[/bold cyan] {hub}")
        
        all_hub_urls = []
        for query in queries:
            try:
                console.print(f"[dim]Searching: {query}[/dim]")
                # Discover URLs for this hub
                urls = search_waterfall(query, limit=10) # limit per hub query to keep it 'fast'
                if urls:
                    all_hub_urls.extend(urls)
                
                # Anti-Block Sleep
                time.sleep(random.uniform(1.0, 2.5))
                
            except Exception as e:
                console.print(f"[red]Error searching for {query}: {e}[/red]")
                continue

        if all_hub_urls:
            # Deduplicate URLs found for this hub
            unique_hub_urls = list(set(all_hub_urls))
            console.print(f"[green]Found {len(unique_hub_urls)} unique URLs for {hub}. Starting extraction...[/green]")
            
            try:
                # Save temp URLs for deep_study
                import json
                with open(temp_urls, "w") as f:
                    json.dump(unique_hub_urls, f)

                # Extract and Validate (Validation is now handled in MasterDataManager.upsert_entity)
                process_deep_study(temp_urls, master_output, city="ahmedabad")
                
                # Export to Excel
                save_lead_to_excel(master_output, excel_output)
                
            except Exception as e:
                console.print(f"[red]Extraction failed for hub {hub}: {e}[/red]")
        else:
            console.print(f"[yellow]No results found for hub {hub}.[/yellow]")

    console.print("\n[bold green]Fast Hub Discovery Completed![/bold green]")

if __name__ == "__main__":
    try:
        run_fast_hub_discovery()
    except KeyboardInterrupt:
        console.print("\n[bold red]Operation cancelled by user.[/bold red]")
    except Exception as e:
        console.print(f"\n[bold red]Critical Error:[/bold red] {e}")
