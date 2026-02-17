import random
import time
import base64
import urllib.parse
from playwright.sync_api import sync_playwright
from src.common.utils import console, get_random_header, random_delay, normalize_url, load_crawler_state, save_crawler_state, save_unique_urls

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

    return list(unique_links)

def search_bing(query: str, limit: int = 50, headless: bool = False):
    """
    Searches Bing.com. Often better than DDG, closer to Google.
    """
    console.print(f"[bold blue]Starting Bing Search for:[/bold blue] {query}")
    unique_links = set()
    
    # Bing is strict, so we default to visible mode
    headless = False # Force visible for Bing to avoid immediate blocks
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent=get_random_header()
            )
            page = context.new_page()
            
            console.print("Navigating to Bing...")
            page.goto(f"https://www.bing.com/search?q={query}&count=50", timeout=60000)
            random_delay(2, 4)
            
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            random_delay(1, 2)
            
            try:
                if "challenge" in page.content().lower() or "captcha" in page.content().lower():
                    console.print("[bold red]Bing requires manual interaction (CAPTCHA/Challenge)![/bold red]")
                    console.print("[bold green]Please solve it in the browser window...[/bold green]")
                    # Wait loop
                    for i in range(30):
                        time.sleep(1)
                        try:
                            if "challenge" not in page.content().lower() and "captcha" not in page.content().lower():
                                console.print("[green]Challenge passed![/green]")
                                break
                        except:
                            # If page is navigating, content() might fail. Ignore and wait.
                            pass
            except:
                pass
                
                
            # Check for Local Pack (Bing Maps)
            local_links = extract_local_pack(page)
            if local_links:
                console.print(f"[green]Found {len(local_links)} Local Pack links (Bing)![/green]")
                for l in local_links:
                    if l not in unique_links:
                        unique_links.add(l)
                        console.print(f"Found (Bing Local): {l}")

            # Extract links - Bing organic results usually have class 'b_algo'
            results = page.locator(".b_algo h2 a").all()
            
            if not results:
                 # Fallback selector
                results = page.locator("li.b_algo h2 a").all()
            
            if not results:
                # One last check after wait
                console.print("[yellow]Re-checking for results after potential manual fix...[/yellow]")
                results = page.locator(".b_algo h2 a").all()

            if not results:
                console.print("[red]No Bing results found. Saving screenshot and HTML...[/red]")
                page.screenshot(path="debug_tools/debug_bing_empty.png")
                with open("debug_tools/debug_bing_empty.html", "w") as f:
                    f.write(page.content())

            console.print(f"[dim]Bing Raw Results Found: {len(results)}[/dim]")
            
            for r in results:
                href = r.get_attribute("href")
                
                if href and "bing.com/ck/" in href:
                    try:
                        parsed = urllib.parse.urlparse(href)
                        qs = urllib.parse.parse_qs(parsed.query)
                        if "u" in qs:
                            u_val = qs["u"][0]
                            # Remove 'a1' prefix pattern seen in logs
                            if u_val.startswith("a1"):
                                u_val = u_val[2:]
                            # Add padding
                            u_val += "=" * ((4 - len(u_val) % 4) % 4)
                            # Decode
                            decoded_bytes = base64.urlsafe_b64decode(u_val)
                            href = decoded_bytes.decode("utf-8")
                            console.print(f"[dim]Decoded Bing URL: {href}[/dim]")
                    except Exception as e:
                        console.print(f"[dim]Failed to decode Bing URL: {e}[/dim]")

                if href and href.startswith("http") and "microsoft.com" not in href and "bing.com" not in href:
                    norm = normalize_url(href)
                    if norm and norm not in unique_links:
                        unique_links.add(norm)
                        console.print(f"Found (Bing): {norm}")
                        if limit > 0 and len(unique_links) >= limit:
                            break
                            
            browser.close()
            
        except Exception as e:
            console.print(f"[bold red]Bing Error:[/bold red] {e}")
            
    return list(unique_links)

def search_google_fallback(query: str, limit: int = 50, headless: bool = False):
    """
    Interactive Google Search. Waits for user if blocked.
    """
    console.print(f"[bold blue]Starting Interactive Google Search for:[/bold blue] {query}")
    console.print("[yellow]NOTE: If a CAPTCHA appears, please solve it manually in the browser window![/yellow]")
    
    unique_links = set()
    # Force visible for interactive solving
    headless = False 
    
    base_url = "https://www.google.com/search?q={}&num={}"
    fetch_num = 100 if limit <= 0 else min(limit, 100) 
    target_url = base_url.format(query.replace(" ", "+"), fetch_num)
    
    with sync_playwright() as p:
        try:
            user_agent = get_random_header()
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(user_agent=user_agent)
            page = context.new_page()
            
            console.print(f"Navigating to Google...")
            page.goto(target_url, timeout=60000)
            
            # Check for captcha/consent
            if "sorry/index" in page.url or "captcha" in page.content().lower() or "consent.google" in page.url:
                console.print("[bold red]Google requires manual interaction![/bold red]")
                console.print("[bold green]Please solve the CAPTCHA or click 'I agree' in the browser...[/bold green]")
                console.print("Waiting for you to solve it...")
                
                # Wait loop
                for i in range(60):
                    time.sleep(1)
                    if "sorry/index" not in page.url and "captcha" not in page.content().lower() and "consent.google" not in page.url:
                        console.print("[green]Challenge passed![/green]")
                        break
                
            # Scroll a bit
            page.evaluate("window.scrollTo(0, 1000)")
            random_delay(1, 3)

            # Standard Google Selectors
            elements = page.locator("#search .g a").all()
            
            for el in elements:
                href = el.get_attribute("href")
                if href and href.startswith("http") and "google.com" not in href:
                    norm = normalize_url(href)
                    if norm and norm not in unique_links:
                        unique_links.add(norm)
                        console.print(f"Found: {norm}")
                        if limit > 0 and len(unique_links) >= limit:
                            break
                            
            if not unique_links:
                console.print("[red]No Google results found. Saving screenshot and HTML...[/red]")
                page.screenshot(path="debug_tools/debug_google_empty.png")
                with open("debug_tools/debug_google_empty.html", "w") as f:
                    f.write(page.content())
            
            browser.close()
            
        except Exception as e:
            console.print(f"[bold red]Google Error:[/bold red] {e}")
            
    return list(unique_links)

def search_brave(query: str, limit: int = 50, headless: bool = False, output_file: str = "data/websites.json"):
    """
    Scrapes Brave Search with robust 50-page pagination.
    """
    console.print(f"[bold orange3]Starting Brave Search for:[/bold orange3] {query}")
    unique_links = set()
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent=get_random_header()
            )
            page = context.new_page()
            
            # Resume State
            start_page = load_crawler_state(query)
            if start_page > 1:
                console.print(f"[bold cyan]Resuming search from Page {start_page}...[/bold cyan]")
                # Calculate offset. Brave uses 0-indexed offset? 
                # Page 1 = offset 0, Page 2 = offset 1. 
                # So Page N = offset N-1.
                offset = start_page - 1
                page.goto(f"https://search.brave.com/search?q={query}&source=web&offset={offset}", timeout=60000)
            else:
                page.goto(f"https://search.brave.com/search?q={query}&source=web", timeout=60000)
            
            # CAPTCHA Check
            if "captcha" in page.content().lower() or "robot" in page.content().lower():
                console.print("[bold red]Brave requires manual interaction![/bold red]")
                console.print("[bold green]Please solve the CAPTCHA in the browser... (Waiting 30s)[/bold green]")
                time.sleep(30)
            
            # Massive Pagination Loop (Max 50 Pages)
            # Range should start from start_page
            for page_num in range(start_page, 51):
                console.print(f"[dim]Scraping Page {page_num}... (Found: {len(unique_links)}/{limit})[/dim]")
                
                # Save State immediately or after success? 
                # Better to save after success to avoid skipping if it crashes.
                
                random_delay(2, 4)
                
                # Scroll to trigger lazy loading
                for _ in range(3):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                
                # Extract Results
                snippet_results = page.locator(".snippet[data-type='web']").all()
                new_on_page = 0
                
                # Check for Local Pack & Maps
                local_links = extract_local_pack(page)
                if local_links:
                    for l in local_links:
                        norm = normalize_url(l)
                        if norm and norm not in unique_links:
                            unique_links.add(norm)
                            console.print(f"Found (Local): {norm}")

                # Extract Organic Results
                for r in snippet_results:
                    try:
                        link_el = r.locator("a").first
                        href = link_el.get_attribute("href")
                        
                        if href and href.startswith("http") and "brave.com" not in href:
                            norm = normalize_url(href)
                            if norm and norm not in unique_links:
                                unique_links.add(norm)
                                new_on_page += 1
                                console.print(f"Found: {norm}")
                                
                    except:
                        continue

                console.print(f"[dim]Added {new_on_page} new links from page {page_num}[/dim]")
                
                # Limit Check? 
                # User asked for "50-Page Pagination Loop", possibly ignoring limit or just scraping deep?
                # Usually we respect limit, but let's relax it if we want "Massive Upgrade"
                # But to save time we should probably respect limit if it's hit?
                # User said: "Implement a for loop that iterates up to 50 times"
                # Let's keep scraping until 50 or end of results, but maybe check limit if we have enough?
                # If limit is default 50, we might stop too early. 
                # Let's assume 'limit' is soft or user will increase it. 
                # Incremental Save
                if unique_links:
                     save_unique_urls(list(unique_links), output_file)

                # Limit Check
                # If limit is 0, we don't stop based on count.
                if limit > 0 and len(unique_links) >= limit:
                    console.print(f"[green]Hit limit of {limit} URLs.[/green]")
                    break

                # Save Progress
                save_crawler_state(query, page_num + 1) # Next time start from next page
                
                # Next Button Logic
                try:
                    # Specific selectors requested
                    next_btn = page.locator("a#next").first
                    if not next_btn.is_visible():
                        next_btn = page.get_by_role("link", name="Next").first
                    
                    if next_btn.is_visible():
                        console.print("[dim]Navigating to next page...[/dim]")
                        next_btn.click()
                        # 'networkidle' is flaky on Brave, use 'domcontentloaded' + slight delay
                        page.wait_for_load_state("domcontentloaded", timeout=30000)
                        random_delay(3, 5) # Extra buffer for content render
                    else:
                        console.print("[yellow]No 'Next' button found. End of results.[/yellow]")
                        break
                except Exception as e:
                    console.print(f"[dim]Pagination error: {e}[/dim]")
                    break
            
            browser.close()
            
        except Exception as e:
            console.print(f"[bold red]Brave Error:[/bold red] {e}")
            
    return list(unique_links)

def search_waterfall(query: str, limit: int = 50, headless: bool = False, output_file: str = "data/websites.json"):
    """
    Robust Discovery: Brave -> Bing -> DuckDuckGo
    With Deep Scraping for Aggregators.
    """
    console.print(f"[bold magenta]Starting Waterfall Search Strategy for: {query}[/bold magenta]")
    
    results = []
    
    # 1. Try Brave (Primary)
    results = search_brave(query, limit, headless, output_file)
    
    if not results:
        console.print("[bold yellow]Brave failed/blocked. Switching to Bing...[/bold yellow]")
        # 2. Try Bing (Visible)
        results = search_bing(query, limit, False) 
        
        if not results:
            console.print("[bold yellow]Bing failed. Switching to DuckDuckGo (Last Resort)...[/bold yellow]")
            # 3. Try DDG
            results = search_ddg(query, limit, headless)

    # Post-Processing: Maps
    if results:
        # Deduplicate first
        results = list(set(results))
        
    return list(set(results))

def extract_local_pack(page) -> list[str]:
    """ Extract links from Local/Map Pack if present """
    local_links = []
    try:
        # Brave Local Pack
        # Look for map entries or direction links that might contain website info
        # This is tricky as often the website button is hidden or requires click.
        # We look for direct 'Website' links in the map card.
        
        # Generic approach for Brave/Bing map cards
        cards = page.locator(".local-pack-item, .map-card, .loc-card").all()
        for card in cards:
            web_link = card.locator("a[title='Website'], a:has-text('Website')").first
            if web_link.is_visible():
                href = web_link.get_attribute("href")
                if href: local_links.append(href)
    except:
        pass
    return local_links

def search_ddg(query: str, limit: int = 50, headless: bool = True):
    """
    Searches DuckDuckGo using the DDGS library.
    """
    console.print(f"[bold yellow]Starting DuckDuckGo Search for:[/bold yellow] {query}")
    unique_links = set()
    
    try:
        from duckduckgo_search import DDGS
        
        # DDGS is synchronous
        max_results = 100 if limit <= 0 else min(limit, 100)
        
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
            
            if results:
                for r in results:
                    href = r.get("href")
                    if href:
                        norm = normalize_url(href)
                        if norm and norm not in unique_links:
                            unique_links.add(norm)
                            console.print(f"Found (DDG): {norm}")
                            if limit > 0 and len(unique_links) >= limit:
                                break
            else:
                console.print("[red]DDG returned no results.[/red]")
                
    except Exception as e:
        console.print(f"[bold red]DDG Error:[/bold red] {e}")
        
    return list(unique_links)
