import time
import urllib.parse
import base64
from playwright.sync_api import sync_playwright
from src.core.utils import console, get_random_header, random_delay, normalize_url
from src.scrapers.utils import extract_local_pack

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
                if not os.path.exists("debug_tools"): os.makedirs("debug_tools", exist_ok=True)
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
