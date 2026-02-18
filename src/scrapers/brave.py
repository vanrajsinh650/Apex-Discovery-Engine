import time
from playwright.sync_api import sync_playwright
from src.core.utils import console, get_random_header, random_delay, normalize_url, load_crawler_state, save_crawler_state, save_unique_urls
from src.scrapers.utils import extract_local_pack

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
            max_pages = 200 if limit <= 0 else 50
            if limit > 200: max_pages = (limit // 10) + 10 # heuristic

            for page_num in range(start_page, max_pages + 1):
                console.print(f"[dim]Scraping Page {page_num}... (Found: {len(unique_links)}/{limit})[/dim]")
                
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
                
                # Incremental Save
                if unique_links:
                     save_unique_urls(list(unique_links), output_file)

                # Limit Check
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
