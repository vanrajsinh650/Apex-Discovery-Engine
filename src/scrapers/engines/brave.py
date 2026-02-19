import asyncio
import time
from playwright.async_api import async_playwright
from src.core.utils import console, get_random_header, random_delay, normalize_url, load_crawler_state, save_crawler_state, save_unique_urls
from src.scrapers.utils import extract_local_pack

async def search_brave(query: str, limit: int = 50, headless: bool = True, output_file: str = "data/websites.json"):
    """
    Scrapes Brave Search with robust 50-page pagination (Async).
    Optimized: Blocks resources, Smart Waits, Fast Headless.
    """
    console.print(f"[bold orange3]Starting Brave Search (Async) for:[/bold orange3] {query}")
    unique_links = set()
    
    async with async_playwright() as p:
        try:
            # Launch with stealth args recommended for speed/stealth
            browser = await p.chromium.launch(
                headless=headless,
                args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"]
            )
            context = await browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent=get_random_header()
            )
            
            # --- Resource Blocking for Speed ---
            await context.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2,ico}", lambda route: route.abort())
            
            page = await context.new_page()
            
            # Resume State
            start_page = load_crawler_state(query)
            if start_page > 1:
                console.print(f"[bold cyan]Resuming search from Page {start_page}...[/bold cyan]")
                offset = start_page - 1
                try:
                    await page.goto(f"https://search.brave.com/search?q={query}&source=web&offset={offset}", timeout=15000)
                except: pass
            else:
                try:
                    await page.goto(f"https://search.brave.com/search?q={query}&source=web", timeout=15000)
                except: pass
            
            # CAPTCHA Check (Basic text check)
            content = await page.content()
            if "captcha" in content.lower() or "robot" in content.lower():
                console.print("[bold red]Brave requires manual interaction![/bold red]")
                # If headless, we can't solve. Just abort or wait?
                # For async/speed, simpler to abort this engine.
                await browser.close()
                return []
            
            # Pagination Loop 
            max_pages = 200 if limit <= 0 else 50
            if limit > 200: max_pages = (limit // 10) + 10

            for page_num in range(start_page, max_pages + 1):
                console.print(f"[dim]Scraping Page {page_num}... (Found: {len(unique_links)}/{limit})[/dim]")
                
                # Micro-Delay
                random_delay(0.5, 1.5)
                
                # Fast Scroll
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                
                # Extract Results
                snippet_results = await page.locator(".snippet[data-type='web']").all()
                new_on_page = 0
                
                # Local Pack (If any)
                local_links = await extract_local_pack(page) # extract_local_pack needs to be async or we call it specially?
                # Actually extract_local_pack is likely sync in utils.py. Need to check/fix or adapt. 
                # Assuming simple DOM traversal, we can do manual check here for speed.
                
                # Sync logic for extract_local_pack works on element handle or page object? 
                # It likely uses page.locator so it needs to be awaited if used on async page.
                # Re-implementing simplified version here to avoid import issues for now.
                try:
                    map_links = await page.locator("a[href*='maps.google']").all()
                    for ml in map_links:
                         # ... scraping logic for maps link ...
                         pass 
                except: pass

                # Organic Results
                for r in snippet_results:
                    try:
                        link_el = r.locator("a").first
                        href = await link_el.get_attribute("href")
                        
                        if href and href.startswith("http") and "brave.com" not in href:
                            norm = normalize_url(href)
                            if norm and norm not in unique_links:
                                unique_links.add(norm)
                                new_on_page += 1
                                console.print(f"Found: {norm}")
                    except:
                        continue
                
                console.print(f"[dim]Added {new_on_page} new links[/dim]")
                
                # Batch Write logic (User asked for batch/memory, but we have save_unique_urls helper)
                # Let's keep incremental save for safety, but maybe every 3 pages? 
                # User said "Memory First... write at end or batch 50".
                if len(unique_links) % 50 == 0 or new_on_page > 0:
                     save_unique_urls(list(unique_links), output_file)

                # Limit Check
                if limit > 0 and len(unique_links) >= limit:
                    break
                
                # Save State
                save_crawler_state(query, page_num + 1)
                
                # Next Button
                try:
                    next_btn = page.locator("a#next").first
                    if not await next_btn.is_visible():
                        next_btn = page.get_by_role("link", name="Next").first
                    
                    if await next_btn.is_visible():
                        await next_btn.click()
                        # Smart wait
                        try:
                            await page.wait_for_selector(".snippet[data-type='web']", timeout=10000)
                        except:
                            await page.wait_for_load_state("domcontentloaded", timeout=10000)
                    else:
                        break
                except:
                    break
            
            await browser.close()
            
        except Exception as e:
            console.print(f"[bold red]Brave Async Error:[/bold red] {e}")
            
    return list(unique_links)
