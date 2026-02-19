from src.exporters.excel import export_to_excel_perfect

def save_lead_to_excel(input_json="data/master_pg_list.json", output_xlsx="data/perfect_pg_list.xlsx"):
    """Bridge function for export_to_excel_perfect"""
    return export_to_excel_perfect(input_json, output_xlsx)
