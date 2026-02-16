import random
import time
from playwright.sync_api import sync_playwright
from rich.console import Console

console = Console()

# List of real, modern browser User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def get_random_header():
    """Returns a random User-Agent from the list."""
    return random.choice(USER_AGENTS)

def random_delay(min_seconds: float = 2.0, max_seconds: float = 5.0):
    """Sleeps for a random amount of time to mimic human behavior."""
    delay = random.uniform(min_seconds, max_seconds)
    console.print(f"[dim]Sleeping for {delay:.2f}s...[/dim]")
    time.sleep(delay)

def search_google(query: str, limit: int = 50, headless: bool = True):
    """
    Searches Google using Playwright with robust anti-bot stealth mechanics.
    """
    console.print(f"[bold blue]Starting Stealth Search for:[/bold blue] {query}")
    
    unique_links = set()
    max_retries = 3
    base_url = "https://www.google.com/search?q={}&num={}"
    
    # Calculate how many results to fetch (Google supports num param up to 100 usually)
    # effectively getting one big page if possible, or paginating.
    # For robust discovery, getting 100 on first page is most efficient stealth-wise.
    fetch_num = min(limit, 100) 
    
    target_url = base_url.format(query.replace(" ", "+"), fetch_num)
    
    with sync_playwright() as p:
        for attempt in range(max_retries):
            try:
                # 1. Rotate User-Agent
                user_agent = get_random_header()
                console.print(f"[dim]Attempt {attempt+1}/{max_retries} with UA: ...{user_agent[-20:]}[/dim]")
                
                # Launch browser with specific args to reduce bot detection
                browser = p.chromium.launch(
                    headless=headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        f"--user-agent={user_agent}"
                    ]
                )
                
                # Create context with random viewport to add variance
                context = browser.new_context(
                    user_agent=user_agent,
                    viewport={"width": random.randint(1280, 1920), "height": random.randint(720, 1080)},
                    locale="en-US",
                    timezone_id="Asia/Kolkata" # Match user region if relevant or generic
                )
                
                # Add init script to mask webdriver
                context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                
                page = context.new_page()
                
                # 2. Random Delay before request
                random_delay(1.0, 3.0)
                
                console.print(f"Navigating to search page...")
                response = page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
                
                # Check for 429 or captcha
                if "sorry/index" in page.url or "captcha" in page.content().lower():
                    console.print("[bold red]Hit Google Captcha/Block![/bold red]")
                    browser.close()
                    time.sleep(2 ** (attempt + 2)) # Exponential backoff
                    continue

                # Wait for results to load
                try:
                    page.wait_for_selector("#search", timeout=10000)
                except:
                    console.print("[yellow]Search results selector not found. Page might be different structure.[/yellow]")
                    # Take screenshot for debug
                    page.screenshot(path="debug_stealth_fail.png")
                
                # 3. Extract Links
                # Generic selector for Google results
                elements = page.locator("#search .g a").all()
                
                for el in elements:
                    href = el.get_attribute("href")
                    if href and href.startswith("http") and "google.com" not in href:
                        if href not in unique_links:
                            unique_links.add(href)
                            console.print(f"Found: {href}")
                            if len(unique_links) >= limit:
                                break
                
                browser.close()
                
                if unique_links:
                    break # Success
                else:
                    console.print("[yellow]No links found on this attempt.[/yellow]")
                    time.sleep(2)
                    
            except Exception as e:
                console.print(f"[bold red]Error in attempt {attempt+1}:[/bold red] {e}")
                time.sleep(2 ** (attempt + 2)) # Backoff
                
    return list(unique_links)
