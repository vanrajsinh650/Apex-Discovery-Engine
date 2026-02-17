import random
import time
import base64
import urllib.parse
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
            
            if "challenge" in page.content().lower() or "captcha" in page.content().lower():
                console.print("[bold red]Bing requires manual interaction (CAPTCHA/Challenge)![/bold red]")
                console.print("[bold green]Please solve it in the browser window...[/bold green]")
                # Wait loop
                for i in range(30):
                    time.sleep(1)
                    if "challenge" not in page.content().lower() and "captcha" not in page.content().lower():
                        console.print("[green]Challenge passed![/green]")
                        break
                
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
                    if href not in unique_links:
                        unique_links.add(href)
                        console.print(f"Found (Bing): {href}")
                        if len(unique_links) >= limit:
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
    fetch_num = min(limit, 100) 
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
                    if href not in unique_links:
                        unique_links.add(href)
                        console.print(f"Found: {href}")
                        if len(unique_links) >= limit:
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

def search_brave(query: str, limit: int = 50, headless: bool = True):
    """
    Scrapes Brave Search with pagination support.
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
            
            page.goto(f"https://search.brave.com/search?q={query}&source=web", timeout=60000)
            
            page_num = 1
            while len(unique_links) < limit:
                console.print(f"[dim]Scraping Page {page_num}... (Found: {len(unique_links)}/{limit})[/dim]")
                random_delay(2, 4)
                
                for _ in range(3):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                
                results = page.locator(".snippet[data-type='web']").all()
                new_on_page = 0
                
                for r in results:
                    try:
                        link_el = r.locator("a").first
                        href = link_el.get_attribute("href")
                        
                        if href and href.startswith("http") and "brave.com" not in href:
                            if href not in unique_links:
                                unique_links.add(href)
                                new_on_page += 1
                                console.print(f"Found: {href}")
                                if len(unique_links) >= limit:
                                    break
                    except:
                        continue

                console.print(f"[dim]Added {new_on_page} new links from page {page_num}[/dim]")
                
                if len(unique_links) >= limit:
                    break

                # Find 'Next' button
                try:
                    next_btn = page.get_by_role("link", name="Next").first
                    if not next_btn.is_visible():
                        next_btn = page.locator("a:has-text('Next')").first
                    
                    if next_btn.is_visible():
                        console.print("[dim]Navigating to next page...[/dim]")
                        next_btn.click()
                        # 'networkidle' can be flaky on dynamic sites, use 'domcontentloaded' + buffer
                        page.wait_for_load_state("domcontentloaded", timeout=30000)
                        random_delay(2, 4) # Buffer for dynamic content
                        page_num += 1
                    else:
                        console.print("[yellow]No 'Next' button found. End of results.[/yellow]")
                        break
                except Exception as e:
                    console.print(f"[dim]Pagination error: {e}[/dim]")
                    # Don't break immediately on minor errors, but for navigation failure we should probably stop
                    break
            
            browser.close()
            
        except Exception as e:
            console.print(f"[bold red]Brave Error:[/bold red] {e}")
            
    return list(unique_links)

def search_waterfall(query: str, limit: int = 50, headless: bool = False):
    """
    Robust Discovery: Brave -> Bing -> DuckDuckGo
    """
    console.print(f"[bold magenta]Starting Waterfall Search Strategy for: {query}[/bold magenta]")
    
    # 1. Try Brave (Primary)
    results = search_brave(query, limit, headless)
    if results:
        return results
        
    console.print("[bold yellow]Brave failed/blocked. Switching to Bing...[/bold yellow]")

    # 2. Try Bing (Visible)
    results = search_bing(query, limit, False) # Force visible for Bing
    if results:
        return results

    console.print("[bold yellow]Bing failed. Switching to DuckDuckGo (Last Resort)...[/bold yellow]")
    
    # 3. Try DDG
    return search_ddg(query, limit, headless)
