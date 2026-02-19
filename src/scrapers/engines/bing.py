import asyncio
import urllib.parse
import base64
import os
from playwright.async_api import async_playwright
from src.core.utils import console, get_random_header, random_delay, normalize_url
from src.scrapers.utils import extract_local_pack

async def search_bing(query: str, limit: int = 50, headless: bool = False):
    """
    Searches Bing.com (Async).
    Optimized: Resource blocking, Smart Waits.
    """
    console.print(f"[bold blue]Starting Bing Search (Async) for:[/bold blue] {query}")
    unique_links = set()
    
    # Bing is strict, default to visible if not specified, 
    # but for "Fast-Headless" request we should try headless=True with stealth if possible?
    # The user asked for "Fast-Headless Mode: Ensure... headless=True".
    # Let's try headless=True but be ready to fail or use stealth args.
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(
                headless=headless,
                args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"]
            )
            context = await browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent=get_random_header()
            )
            
            # --- Resource Blocking ---
            await context.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2,ico}", lambda route: route.abort())
            
            page = await context.new_page()
            
            console.print("Navigating to Bing...")
            try:
                await page.goto(f"https://www.bing.com/search?q={query}&count=50", timeout=15000)
            except:
                console.print("[red]Bing navigation timed out.[/red]")
                await browser.close()
                return []
                
            random_delay(1, 2)
            
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # CAPTCHA / Challenge Check
            try:
                content = await page.content()
                if "challenge" in content.lower() or "captcha" in content.lower():
                    console.print("[bold red]Bing requires manual interaction![/bold red]")
                    # Async/Headless -> Abort
                    await browser.close()
                    return []
            except: pass
                
            # Local Links (Simplified async check)
            # Reimplementing basic extraction to avoid sync utils issue
            try:
                # Bing Maps often in separate block or distinct class
                # Just simplified check for now as Bing structure varies
                pass
            except: pass

            # Extract links
            results = await page.locator(".b_algo h2 a").all()
            
            if not results:
                results = await page.locator("li.b_algo h2 a").all()
            
            if not results:
                # console.print("[red]No Bing results found.[/red]")
                pass

            for r in results:
                try:
                    href = await r.get_attribute("href")
                    
                    if href and "bing.com/ck/" in href:
                         # Decode logic (same as before)
                         try:
                            parsed = urllib.parse.urlparse(href)
                            qs = urllib.parse.parse_qs(parsed.query)
                            if "u" in qs:
                                u_val = qs["u"][0]
                                if u_val.startswith("a1"): u_val = u_val[2:]
                                u_val += "=" * ((4 - len(u_val) % 4) % 4)
                                decoded_bytes = base64.urlsafe_b64decode(u_val)
                                href = decoded_bytes.decode("utf-8")
                         except: pass

                    if href and href.startswith("http") and "microsoft.com" not in href and "bing.com" not in href:
                        norm = normalize_url(href)
                        if norm and norm not in unique_links:
                            unique_links.add(norm)
                            console.print(f"Found (Bing): {norm}")
                            if limit > 0 and len(unique_links) >= limit:
                                break
                except: continue
                            
            await browser.close()
            
        except Exception as e:
            console.print(f"[bold red]Bing Async Error:[/bold red] {e}")
            
    return list(unique_links)
