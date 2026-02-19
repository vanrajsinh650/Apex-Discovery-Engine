from src.scrapers.core.search_coordinator import search_waterfall
from src.scrapers.core.deep_crawler import process_deep_study

def deep_study_site(urls, output_file="data/master_pg_list.json"):
    """Bridge function for process_deep_study"""
    return process_deep_study(None, output_file) # Note: URLs are usually passed via file, but we can adapt
