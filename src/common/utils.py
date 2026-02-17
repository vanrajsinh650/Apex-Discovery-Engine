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
        if url not in unique_set:
            unique_set.add(url)
            added_count += 1
    
    # Save back
    final_list = sorted(list(unique_set))
    
    # Ensure directory
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(final_list, f, indent=2)
        
    console.print(f"[green]Added {added_count} new URLs. Total unique: {len(final_list)}[/green]")
    console.print(f"Results saved to [bold]{output_file}[/bold]")

