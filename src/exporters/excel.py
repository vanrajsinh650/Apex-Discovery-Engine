import pandas as pd
import json
import os
from rich.console import Console

console = Console()

def export_to_excel(input_file="data/master_pg_list.json", output_file="data/final_pg_leads.xlsx"):
    """
    Reads Master List JSON and exports to a formatted Excel file.
    """
    if not os.path.exists(input_file):
        console.print(f"[red]Input file {input_file} not found.[/red]")
        return

    try:
        with open(input_file, "r") as f:
            data = json.load(f)
            
        console.print(f"[blue]Loaded {len(data)} records. Preparing export...[/blue]")

        export_data = []
        
        for entry in data:
            name = entry.get("name", "").strip()
            # Skip empty names if no phone either
            if not name and not entry.get("mobile"):
                continue
                
            # Flatten lists
            mobiles = ", ".join(entry.get("mobile", []))
            emails = ", ".join(entry.get("email", []))
            
            # Location pages
            loc_pages = ""
            if entry.get("location_pages"):
                # limit to first 3 to avoid cell overflow?
                loc_pages = "\n".join(entry.get("location_pages")[:3])
            
            # Source
            source = entry.get("source") or entry.get("website") or ""

            export_data.append({
                "Business Name": name,
                "Mobile Number": mobiles,
                "Email Address": emails,
                "Address": entry.get("address", ""),
                "Rating": entry.get("rating", ""),
                "Review Count": entry.get("reviews", ""),
                "Source Link": source,
                "Other Links": loc_pages
            })

        if export_data:
            df = pd.DataFrame(export_data)
            
            # Reorder columns if needed (optional, pandas preserves dict order mostly)
            cols = ["Business Name", "Mobile Number", "Email Address", "Address", "Rating", "Review Count", "Source Link", "Other Links"]
            # Filter cols that exist
            cols = [c for c in cols if c in df.columns]
            df = df[cols]
            
            df.to_excel(output_file, index=False)
            console.print(f"[bold green]Successfully exported {len(export_data)} leads to {output_file}[/bold green]")
        else:
            console.print("[yellow]No extracted data to export.[/yellow]")

    except Exception as e:
        console.print(f"[red]Export failed: {e}[/red]")
