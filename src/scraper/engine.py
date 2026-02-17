import random
import time
from playwright.sync_api import sync_playwright
from src.common.utils import console, get_random_header, random_delay

def search_google(query: str, limit: int = 50, headless: bool = True):
    """
    Main search function. Now defaults to DuckDuckGo as Google is blocked.
    Kept name 'search_google' for compatibility with main.py.
    """
    console.print(f"[bold green]Using DuckDuckGo (Primary) for:[/bold green] {query}")
    results = search_ddg(query, limit, headless)
    
    if not results:
        console.print("[yellow]DDG returned no results. Trying Google (Risky)...[/yellow]")
        return search_google_fallback(query, limit, headless)
        
    return results

def search_google_fallback(query: str, limit: int = 50, headless: bool = True):
    """
    Legacy Google Search (Blocked often). Used as backup.
    """
    console.print(f"[bold blue]Starting Stealth Search (Fallback) for:[/bold blue] {query}")
    
    unique_links = set()
    max_retries = 3
    base_url = "https://www.google.com/search?q={}&num={}"
    fetch_num = min(limit, 100) 
    target_url = base_url.format(query.replace(" ", "+"), fetch_num)
    
    with sync_playwright() as p:
        for attempt in range(max_retries):
            try:
                user_agent = get_random_header()
                console.print(f"[dim]Attempt {attempt+1}/{max_retries} with UA: ...{user_agent[-20:]}[/dim]")
                
                browser = p.chromium.launch(
                    headless=headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        f"--user-agent={user_agent}"
                    ]
                )
                
                context = browser.new_context(
                    user_agent=user_agent,
                    viewport={"width": random.randint(1280, 1920), "height": random.randint(720, 1080)},
                    locale="en-US",
                    timezone_id="Asia/Kolkata"
                )
                
                context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
                
                page = context.new_page()
                random_delay(1.0, 3.0)
                
                console.print(f"Navigating to search page...")
                try:
                    page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
                except:
                    pass # Timeout

                if "sorry/index" in page.url or "captcha" in page.content().lower():
                    console.print("[bold red]Hit Google Captcha/Block![/bold red]")
                    browser.close()
                    time.sleep(2 ** (attempt + 2))
                    continue

                try:
                    page.wait_for_selector("#search", timeout=10000)
                except:
                    pass
                
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
                    break
                else:
                    time.sleep(2)
                    
            except Exception as e:
                console.print(f"[bold red]Error in attempt {attempt+1}:[/bold red] {e}")
                time.sleep(2 ** (attempt + 2))
            
    return list(unique_links)

def search_ddg(query: str, limit: int = 50, headless: bool = True):
    """
    Searches DuckDuckGo HTML version as a fallback.
    """
    console.print(f"[bold blue]Starting DuckDuckGo Search for:[/bold blue] {query}")
    unique_links = set()
    
    # DDG HTML is simpler and often less blocked
    url = "https://html.duckduckgo.com/html/"
    
    # DDG often blocks headless, so we force visible mode for now
    # This is a trade-off for getting results without complex solving.
    console.print("[dim]Launching visible browser to bypass DDG bot check...[/dim]")
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            # Navigate to DDG HTML
            console.print("Navigating to DDG HTML...")
            page.goto(url, timeout=60000)
            
            # Fill query and submit
            page.fill("input[name='q']", query)
            page.click("input[type='submit']")
            page.wait_for_load_state("networkidle")
            
            # Extract links
            try:
                page.wait_for_selector(".result__a", timeout=5000)
            except:
                pass
            
            results = page.locator(".result__a").all()
            
            for r in results:
                href = r.get_attribute("href")
                if href and href.startswith("http"):
                    if href not in unique_links:
                        unique_links.add(href)
                        console.print(f"Found (DDG): {href}")
                        if len(unique_links) >= limit:
                            break
                            
            browser.close()
            
        except Exception as e:
            console.print(f"[bold red]DDG Error:[/bold red] {e}")
            try:
                page.screenshot(path="debug_tools/debug_ddg_fail.png")
                console.print("[dim]Saved debug_tools/debug_ddg_fail.png[/dim]")
            except:
                pass
            
    return list(unique_links)
