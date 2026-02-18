import random
import time
from rich.console import Console
from .config import USER_AGENTS

console = Console()

def get_random_header():
    """Returns a random User-Agent from the list."""
    return random.choice(USER_AGENTS)

def random_delay(min_seconds: float = 2.0, max_seconds: float = 5.0):
    """Sleeps for a random amount of time to mimic human behavior."""
    delay = random.uniform(min_seconds, max_seconds)
    console.print(f"[dim]Sleeping for {delay:.2f}s...[/dim]")
    time.sleep(delay)

import json
import os
import urllib.parse
from .config import USER_AGENTS

KNOWN_AGGREGATORS = {
    "magicbricks.com", "99acres.com", "justdial.com", 
    "housing.com", "sulekha.com", "commonfloor.com", 
    "nobroker.in", "facebook.com", "instagram.com", 
    "twitter.com", "linkedin.com", "youtube.com"
}

def normalize_url(url: str) -> str:
    """
    Normalizes URLs:
    1. Ensures https://
    2. Removes www.
    3. Strips trailing slashes and params
    4. For KNOWN_AGGREGATORS, returns only the root domain (e.g. magicbricks.com)
    5. Exceptions: subdomains like *.business.site are preserving full path if needed, 
       but user asked to keep full path for 'small business sites'. 
       Actually, standard business.site usually has the business name in subdomain, 
       so root domain logic works fine if we consider 'something.business.site' as the root.
       But for 'magicbricks.com/property...' we want 'magicbricks.com'.
    """
    if not url: return ""
    
    # 1. Basic Clean
    # 1. Basic Clean
    url = url.strip()
    # Force HTTPS scheme
    if url.startswith("http://"):
        url = "https://" + url[7:]
    elif not url.startswith("http"):
        url = "https://" + url
        
    try:
        parsed = urllib.parse.urlparse(url)
        
        # 2. Hostname clean
        hostname = parsed.netloc.lower()
        if hostname.startswith("www."):
            hostname = hostname[4:]
            
        # 3. Check Aggregator - REMOVED per user request (User wants full deep links)
        # is_aggregator = False
        # for agg in KNOWN_AGGREGATORS: ...
        
        # 4. Standard Normalize
        # We keep the path but strip trailing slash for consistency
        path = parsed.path.rstrip("/")
        if not path: path = "/"
        
        # Reconstruct with query params if any (User said "same url", so keep params?)
        # Actually user said "same same url you got", so we should preserve query if it's not tracking specific?
        # Let's keep query params to be safe as search results often rely on them.
        query = parsed.query
        
        final = f"{parsed.scheme}://{hostname}{path}"
        if query:
            final += f"?{query}"
            
        return final
        
    except:
        return url

def save_unique_urls(new_urls: list, output_file: str):
    """
    Saves URLs to JSON, avoiding duplicates with existing file content.
    """
    existing_urls = []
    
    # Load existing
    if os.path.exists(output_file):
        try:
            with open(output_file, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    existing_urls = data
        except Exception as e:
            console.print(f"[yellow]Warning: Could not read existing file {output_file}: {e}[/yellow]")
    
    # Merge using set for uniqueness
    unique_set = set(existing_urls)
    added_count = 0
    
    for url in new_urls:
         # Double check normalization just in case
        normalized = normalize_url(url)
        if normalized and normalized not in unique_set:
            unique_set.add(normalized)
            added_count += 1
    
    # Save back
    final_list = sorted(list(unique_set))
    
    # Ensure directory
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(final_list, f, indent=2)
        
    console.print(f"[green]Added {added_count} new URLs. Total unique: {len(final_list)}[/green]")
    console.print(f"Results saved to [bold]{output_file}[/bold]")

def load_crawler_state(query: str) -> int:
    """Loads the last scraped page number for a query."""
    state_file = "data/crawler_state.json"
    if not os.path.exists(state_file):
        return 1
    
    try:
        with open(state_file, "r") as f:
            state = json.load(f)
            return state.get(query, 1)
    except:
        return 1

def save_crawler_state(query: str, page_num: int):
    """Saves the current page number for a query."""
    state_file = "data/crawler_state.json"
    state = {}
    
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                state = json.load(f)
        except:
            pass
            
    state[query] = page_num
    
    # Atomic-ish write check could be good but simple is fine for now
    try:
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not save state: {e}[/yellow]")

def reset_crawler_state(query: str):
    """ Remove the state for a query to start fresh """
    state_file = "data/crawler_state.json"
    if not os.path.exists(state_file):
        return
        
    try:
        with open(state_file, "r") as f:
            state = json.load(f)
        
        if query in state:
            del state[query]
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)
            console.print(f"[bold green]Reset progress for: {query}[/bold green]")
    except Exception as e:
        console.print(f"[red]Failed to reset state: {e}[/red]")

