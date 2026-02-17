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
