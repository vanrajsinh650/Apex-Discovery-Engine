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
            
            # Reorder columns
            cols = ["Business Name", "Mobile Number", "Email Address", "Address", "Rating", "Review Count", "Source Link", "Other Links"]
            cols = [c for c in cols if c in df.columns]
            df = df[cols]
            
            # --- Premium Styling with XlsxWriter ---
            writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name='PG Leads')
            
            workbook  = writer.book
            worksheet = writer.sheets['PG Leads']
            
            # Formats
            header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#4472C4',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })
            
            cell_format = workbook.add_format({
                'valign': 'top',
                'text_wrap': True,
                'border': 1
            })
            
            zebra_format = workbook.add_format({
                'bg_color': '#D9E1F2',
                'valign': 'top',
                'text_wrap': True,
                'border': 1
            })

            # Apply Zebra Striping and Cell Formatting
            for row_num in range(1, len(df) + 1):
                fmt = zebra_format if row_num % 2 == 0 else cell_format
                worksheet.set_row(row_num, None, fmt)

            # Apply Header Format
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Auto-Adjust Column Widths
            for i, col in enumerate(df.columns):
                try:
                    # Use pandas .str.len() accessor for safety
                    max_len = df[col].astype(str).str.len().max()
                    if pd.isna(max_len):
                        max_len = 0
                    
                    # Ensure max_len is a number (int or float)
                    column_width = max(float(max_len), len(str(col))) + 4
                    # Cap width to 60 for readability
                    worksheet.set_column(i, i, min(column_width, 60))
                except:
                    # Fallback to sensible default
                    worksheet.set_column(i, i, 20)
            
            # Special formatting for Rating/Reviews (Center align)
            center_fmt = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
            for col_idx, col_name in enumerate(df.columns):
                if col_name in ["Rating", "Review Count"]:
                    worksheet.set_column(col_idx, col_idx, 15, center_fmt)

            # Freeze the header row
            worksheet.freeze_panes(1, 0)
            
            writer.close()
            console.print(f"[bold green]Successfully exported {len(export_data)} leads to {output_file}[/bold green]")
        else:
            console.print("[yellow]No extracted data to export.[/yellow]")

    except Exception as e:
        console.print(f"[red]Export failed: {e}[/red]")

def export_to_excel_perfect(input_file="data/master_pg_list.json", output_file="data/perfect_pg_list.xlsx"):
    """
    Exports PG data to a perfectly formatted Excel matching the user's reference.
    Columns: PG Name, Mobile number, Location
    """
    if not os.path.exists(input_file):
        console.print(f"[red]Input file {input_file} not found.[/red]")
        return

    try:
        with open(input_file, "r") as f:
            data = json.load(f)

        AREAS = [
            "Navrangpura", "Vastrapur", "Thaltej", "Bopal", "Paldi", "Satellite", "Ambawadi",
            "Gulbai Tekra", "Memnagar", "Gurukul", "Prahaladnagar", "Makarba", "Vejalpur",
            "Naranpura", "Ghatlodia", "Chandkheda", "Motera", "Sabarmati", "Usmanpura",
            "Ellisbridge", "Ranip", "Gota"
        ]

        def extract_location(address):
            if not address: return "No info"
            address_lower = address.lower()
            for area in AREAS:
                if area.lower() in address_lower:
                    return area
            return "Ahmedabad" # Default if no specific area found

        export_data = []
        for entry in data:
            if entry.get("name") == "Results": # Skip meta entries
                continue
                
            name = entry.get("name", "Unknown PG")
            mobile = entry.get("mobile", ["No info"])[0] if entry.get("mobile") else "No info"
            location = extract_location(entry.get("address"))

            export_data.append({
                "PG Name": name,
                "Mobile number": mobile,
                "Location": location,
                "Address": entry.get("address", "No info"),
                "Source Link": entry.get("source") or entry.get("website") or "No info"
            })

        if export_data:
            df = pd.DataFrame(export_data)
            writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            
            workbook = writer.book
            worksheet = writer.sheets['Sheet1']

            # Minimalist formatting to match the image
            header_format = workbook.add_format({
                'bold': False,
                'border': 1,
                'align': 'left',
                'valign': 'vcenter'
            })
            
            cell_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'top',
                'text_wrap': True
            })

            # Style headers
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)

            # Style data rows and set column widths dynamically
            for i, col in enumerate(df.columns):
                # Calculate max length in the column safely
                lengths = [len(str(x)) for x in df[col] if pd.notnull(x) and str(x).lower() not in ['nan', 'none']]
                max_len = max(lengths) if lengths else 0
                
                # Compare with header length and add buffer
                header_len = len(str(col))
                final_width = max(float(max_len), float(header_len)) + 5
                
                # Cap column widths for readability
                if col == "PG Name":
                    cap = 60
                elif col == "Address":
                    cap = 80
                elif col == "Source Link":
                    cap = 50
                else:
                    cap = 30
                    
                worksheet.set_column(i, i, min(final_width, cap), cell_format)

            writer.close()
            console.print(f"[bold green]Successfully exported perfect list to {output_file}[/bold green]")
        else:
            console.print("[yellow]No data to export for perfect list.[/yellow]")

    except Exception as e:
        console.print(f"[red]Perfect export failed: {e}[/red]")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        app()
    else:
        interactive()
# Bridge Alias
save_lead_to_excel = export_to_excel_perfect
