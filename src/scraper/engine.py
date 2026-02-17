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

def search_google_maps(query: str, limit: int = 50, headless: bool = False):
    """
    Scrapes Google Maps for website links. 
    Bypasses main Search CAPTCHA and gets high quality local results.
    """
    console.print(f"[bold blue]Starting Google Maps Search for:[/bold blue] {query}")
    unique_links = set()
    
    # Maps allows scrolling for many results
    # We should use headless=False to be safe, but it often works headless too.
    # User asked for 'Chrome' which usually implies visible.
    
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent=get_random_header()
            )
            page = context.new_page()
            
            console.print(f"Navigating to Maps: {url}...")
            page.goto(url, timeout=60000)
            
            # Wait for feed
            try:
                page.wait_for_selector('div[role="feed"]', timeout=20000)
            except:
                console.print("[yellow]Maps feed not found immediately. Checking for consent...[/yellow]")
                if "consent.google" in page.url:
                     console.print("[bold red]Google requires interaction![/bold red]")
                     # Wait for manual fix
                     time.sleep(15) 
            
            # Scroll Loop
            # We scroll the feed container
            feed = page.locator('div[role="feed"]')
            
            # If limit is 0 (unlimited), scroll A LOT (e.g., 500 times ~ 5000+ results)
            max_scrolls = 500 if limit <= 0 else (limit // 2) + 5
            
            for i in range(max_scrolls):
                # console.print(f"[dim]Scrolling batch {i+1}...[/dim]")
                
                # Extract visible cards
                # Selectors: div[jsaction] inside feed.
                # Find website buttons: a[data-value="Website"]
                
                # We can extract all current visible buttons
                buttons = page.locator('a[data-value="Website"]').all()
                new_found = 0
                
                for btn in buttons:
                    href = btn.get_attribute("href")
                    if href:
                        norm = normalize_url(href)
                        if norm and norm not in unique_links:
                            unique_links.add(norm)
                            new_found += 1
                            console.print(f"Found (Maps): {norm}")
                            
                # Scroll
                feed.hover()
                page.mouse.wheel(0, 3000)
                time.sleep(2) # Wait for load
                
                if limit > 0 and len(unique_links) >= limit:
                    console.print(f"[green]Hit limit of {limit} URLs.[/green]")
                    break
                    
                # End of list check?
                if "You've reached the end of the list" in page.content():
                    break
                    
            browser.close()
            
        except Exception as e:
            console.print(f"[bold red]Maps Error:[/bold red] {e}")
            
    return list(unique_links)

def search_google_fallback(query: str, limit: int = 50, headless: bool = False):
   # Redirect to Maps scraper as it is superior
   return search_google_maps(query, limit, headless)

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
            
            # Massive Pagination Loop 
            # If unlimited, go up to 200 pages
            max_pages = 200 if limit <= 0 else 50
            if limit > 200: max_pages = (limit // 10) + 10 # heuristic

            for page_num in range(start_page, max_pages + 1):
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
    Robust Discovery: Aggregates results from Google Maps (Local) AND Brave (Organic).
    Get EVERYTHING: Maps + Websites.
    """
    console.print(f"[bold magenta]Starting Multi-Source Discovery for: {query}[/bold magenta]")
    
    all_results = []
    
    # 1. Google Maps (Best for Local/PGs)
    try:
        maps_results = search_google_maps(query, limit, headless)
        if maps_results:
            console.print(f"[green]Maps found {len(maps_results)} links.[/green]")
            all_results.extend(maps_results)
    except Exception as e:
        console.print(f"[dim]Google Maps failed: {e}[/dim]")

    # 2. Brave Search (Best for Aggregators/Directories like Justdial)
    # We always run this too, to get the "websites" the user requested.
    try:
        organic_limit = limit 
        # If limit is 0, we pass 0 (unlimited) to Brave
        
        console.print("[bold orange3]Now searching Organic Results (Websites/Directories)...[/bold orange3]")
        brave_results = search_brave(query, organic_limit, headless, output_file)
        if brave_results:
             console.print(f"[green]Brave found {len(brave_results)} organic links.[/green]")
             all_results.extend(brave_results)
    except Exception as e:
        console.print(f"[dim]Brave failed: {e}[/dim]")
        
    # 3. Fallback to Bing if total is low?
    if len(all_results) < 5:
         console.print("[yellow]Low results. Adding Bing Search...[/yellow]")
         try:
             bing_results = search_bing(query, limit, False)
             if bing_results:
                 all_results.extend(bing_results)
         except:
             pass

    # Deduplicate
    unique_results = list(set(all_results))
    console.print(f"[bold]Total Combined Unique URLs: {len(unique_results)}[/bold]")
        
    return unique_results

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
