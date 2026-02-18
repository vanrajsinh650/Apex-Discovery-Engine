import re
import json
import time
import os
from playwright.sync_api import sync_playwright
from rich.console import Console
from src.core.utils import get_random_header, random_delay

console = Console()

# Regex Patterns
# regex for 10-13 digit numbers, likely mobiles
# Matches: +91 9999999999, 99999 99999, 09999999999, 999-999-9999
PHONE_REGEX = r"(?:\+91|91|0)?\s?[\-]?\s?([6-9][0-9\s\-]{8,13})"
PINCODE_REGEX = r"\b\d{6}\b"
EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PRICE_REGEX = r"(₹|Rs\.?)\s?(\d{1,2}(,\d{2})*(,\d{3})*)"

def clean_phone(phone_str):
    """Normalize phone string to 10 digits"""
    if not phone_str: return None
    # Remove all non-digits
    digits = re.sub(r"\D", "", phone_str)
    
    # Handle country codes
    if len(digits) > 10:
        if digits.startswith("91"):
            digits = digits[2:]
        elif digits.startswith("0") and len(digits) == 11:
             digits = digits[1:]
             
    return digits if len(digits) == 10 else None

def extract_emails(text):
    """Extracts unique emails from text"""
    return set(re.findall(EMAIL_REGEX, text))

def extract_meta_data(page):
    """Extracts description and other meta tags"""
    text = ""
    try:
        desc = page.locator("meta[name='description'], meta[property='og:description']").first
        if desc.count() > 0:
            text += desc.get_attribute("content") or ""
    except: pass
    return text

def extract_tel_links(container):
    """Extracts numbers from href='tel:...' attributes"""
    phones = set()
    try:
        links = container.locator("a[href^='tel:']").all()
        for link in links:
            href = link.get_attribute("href")
            if href:
                p = clean_phone(href.replace("tel:", ""))
                if p: phones.add(p)
    except:
        pass
    return phones

def reveal_contacts(page):
    """Try to click 'Show Number' or similar buttons"""
    try:
        # Common text for reveal buttons
        keywords = ["Show Number", "View Phone", "View Contact", "Call Now", "Show Contact"]
        for kw in keywords:
            # Look for buttons or links with this text
            buttons = page.locator(f"button:has-text('{kw}'), a:has-text('{kw}'), span:has-text('{kw}')").all()
            for btn in buttons[:5]: # Click max 5 to save time/avoid bans
                if btn.is_visible():
                    try:
                        btn.click(timeout=1000)
                        time.sleep(0.5)
                    except:
                        pass
    except:
        pass

def handle_blocking_elements(page):
    """
    Checks for and handles common blocking elements like overlays, modals, and cookie banners.
    Returns (interacted, captcha_found).
    """
    interacted = False
    captcha_found = False
    try:
        # 99acres "Ok, understood" overlay
        # Generic "Accept Cookies", "Continue", "Close" buttons
        blocking_selectors = [
            "button:has-text('Ok, understood')",
            "button:has-text('Accept')",
            "button:has-text('Allow')",
            "button:has-text('Continue')",
            "div[class*='overlay'] button",
            "div[id*='modal'] button",
            ".close-btn",
            "span:has-text('Close')"
        ]
        
        for selector in blocking_selectors:
            # Check if visible
            element = page.locator(selector).first
            if element.is_visible():
                # console.print(f"   [dim]Found blocking element: {selector}. Clicking...[/dim]")
                element.click(timeout=1000)
                time.sleep(1) # Wait for dismissal
                interacted = True
                
        # CAPTCHA / Unusual Traffic Check
        # CAPTCHA / Unusual Traffic Check
        content = page.content().lower()
        # More specific phrases to avoid false positives
        captcha_phrases = [
            "verify you are human",
            "access denied",
            "security challenge",
            "unusual traffic from your computer",
            "confirm you are not a robot",
            "please complete the security check",
            "attention required! | cloudflare" 
        ]
        
        for phrase in captcha_phrases:
            if phrase in content:
                 console.print(f"   [bold red]Blocking detected ({phrase})! Aborting use of this URL...[/bold red]")
                 captcha_found = True
                 break

    except:
        pass
        
    return interacted, captcha_found

def extract_pg_data(url: str, headless: bool = True):
    """
    Universal List Scraper.
    Attempts to find 'cards' or 'listings' on a page and extract data from each.
    """
    results = []
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(user_agent=get_random_header())
            page = context.new_page()
            
            # --- 3-Try Logic ---
            for attempt in range(1, 4):
                if attempt > 1:
                     console.print(f"   [yellow]Attempt {attempt}: Retrying extraction...[/yellow]")

                try:
                    # Navigate if first attempt OR if page is blank/failed previous load
                    if attempt == 1 or page.url == "about:blank":
                         page.goto(url, timeout=45000)
                    
                    # Wait for load
                    random_delay(1, 2)

                    # Handle Blocks/Overlays BEFORE extraction
                    interacted, captcha = handle_blocking_elements(page)
                    if captcha:
                        browser.close()
                        return []
                    if interacted:
                        # If we closed something, maybe wait a bit/scroll again
                        time.sleep(1)

                    # Scroll to load dynamic lists
                    for _ in range(3):
                        page.evaluate("window.scrollBy(0, 1000)")
                        time.sleep(0.5)

                    # Post-Scroll Block Check (Some popups appear on scroll)
                    interacted, captcha = handle_blocking_elements(page)
                    if captcha:
                        browser.close()
                        return []
                    if interacted:
                        time.sleep(1)

                except:
                    if attempt == 3:
                        browser.close()
                        return []
                    continue
                
                # Double check before clicking reveal
                interacted, captcha = handle_blocking_elements(page)
                if captcha:
                    browser.close()
                    return []
                
                # CLICK TO REVEAL
                reveal_contacts(page)
                
                content_text = page.locator("body").inner_text()
                page_title = page.title().strip()

                # --- Strategy 1: Smart Card Detection ---
                # Look for repeating elements that look like property cards
                card_selectors = [
                    "div[class*='card']", "div[class*='listing']", "div[class*='property']", 
                    "div[class*='result']", "article", "div[shadow]", "li.list-item",
                    ".srpTuple__tuple" # 99acres specific
                ]
                
                found_cards = False
                results = [] # Reset results for this attempt
                
                for selector in card_selectors:
                    elements = page.locator(selector).all()
                    valid_cards = [el for el in elements if len(el.inner_text()) > 100]
                    
                    if len(valid_cards) >= 2: # Lower threshold slightly
                        found_cards = True
                        for card in valid_cards:
                            card_text = card.inner_text()
                            
                            name = "Unknown Listing"
                            detail_url = None
                            
                            try:
                                heading = card.locator("h2, h3, h4, .title, .name, .store-name").first
                                if heading.is_visible():
                                    name = heading.inner_text().strip()
                                    # Try to find link in heading
                                    link = heading.locator("a").first
                                    if link.count() > 0:
                                        href = link.get_attribute("href")
                                        if href: detail_url = href
                                    else:
                                        # Try parent if heading itself isn't a link
                                        parent_link = card.locator("a").first
                                        if parent_link.count() > 0:
                                             href = parent_link.get_attribute("href")
                                             if href: detail_url = href
                            except: pass
                            
                            # Normalize URL
                            if detail_url and not detail_url.startswith("http"):
                                # Handle relative URLs
                                base_domain = "/".join(url.split("/")[:3]) # https://example.com
                                if detail_url.startswith("/"):
                                    detail_url = base_domain + detail_url
                                else:
                                    detail_url = base_domain + "/" + detail_url

                            phones = set()
                            for match in re.finditer(PHONE_REGEX, card_text):
                                p = clean_phone(match.group(0))
                                if p: phones.add(p)
                            phones.update(extract_tel_links(card))
                            
                            emails = extract_emails(card_text)
                                
                            address = "Not Found"
                            lines = card_text.split('\n')
                            for line in lines:
                                if re.search(PINCODE_REGEX, line) or "Sector" in line or "Road" in line or "Opp" in line or "Near" in line:
                                    if len(line) > 15 and len(line) < 150:
                                        address = line.strip()
                                        break
                            
                            # DEEP CRAWL LOGIC: If no contact info but we have a link, visit it!
                            if not phones and not emails and detail_url:
                                try:
                                    # console.print(f"   [dim]Deep Crawling: {detail_url}...[/dim]")
                                    new_page = context.new_page()
                                    new_page.goto(detail_url, timeout=30000)
                                    
                                    # Handle blocks/clicks on detail page
                                    handle_blocking_elements(new_page)
                                    reveal_contacts(new_page)
                                    
                                    detail_text = new_page.locator("body").inner_text()
                                    detail_meta = extract_meta_data(new_page)
                                    detail_full_scan = detail_text + " " + detail_meta
                                    
                                    # Extract from detail page
                                    for match in re.finditer(PHONE_REGEX, detail_full_scan):
                                        p = clean_phone(match.group(0))
                                        if p: phones.add(p)
                                    phones.update(extract_tel_links(new_page))
                                    emails.update(extract_emails(detail_full_scan))
                                    
                                    new_page.close()
                                    time.sleep(1) # Be nice
                                except:
                                    try: new_page.close() 
                                    except: pass
                            
                            if phones or emails or (address != "Not Found" and name != "Unknown Listing"):
                                results.append({
                                    "name": name,
                                    "mobile": list(phones),
                                    "email": list(emails),
                                    "address": address,
                                    "source": detail_url if detail_url else url,
                                    "type": "Aggregator Listing"
                                })
                        break 
                
                # --- Strategy 2: Whole Page Fallback (Direct Site) ---
                if not results and not found_cards:
                    # Combined content source: Body + Title + Meta Description
                    meta_desc = extract_meta_data(page)
                    full_text_scan = content_text + " " + page_title + " " + meta_desc
                    
                    unique_phones = set([clean_phone(p[0]) for p in re.finditer(PHONE_REGEX, full_text_scan) if clean_phone(p[0])])
                    unique_phones.update(extract_tel_links(page))
                    
                    unique_emails = extract_emails(full_text_scan)

                    # If no phones, try Contact button then retry scraping phones
                    if not unique_phones:
                        try:
                            # 1. Click Reveal Buttons on current page
                            contact_btn = page.locator("a:has-text('Contact'), a:has-text('Call'), a:has-text('Reach Us')").first
                            if contact_btn.is_visible():
                                 contact_btn.click(timeout=3000)
                                 time.sleep(2)
                                 # Re-grab content
                                 content_text = page.locator("body").inner_text()
                                 for match in re.finditer(PHONE_REGEX, content_text):
                                    p = clean_phone(match.group(0))
                                    if p: unique_phones.add(p)
                                 unique_phones.update(extract_tel_links(page))
                                 unique_emails.update(extract_emails(content_text))
                            
                            # 2. DEEP CRAWL: Visit "Contact Us" page if still no data
                            if not unique_phones and not unique_emails:
                                contact_link = page.locator("a[href*='contact'], a[href*='about'], a:has-text('Contact Us')").first
                                if contact_link.count() > 0:
                                    href = contact_link.get_attribute("href")
                                    if href:
                                        # console.print(f"   [dim]Visiting Contact Page: {href}...[/dim]")
                                        page.goto(href, timeout=30000) # Navigate main page
                                        time.sleep(2)
                                        
                                        c_text = page.locator("body").inner_text()
                                        c_meta = extract_meta_data(page)
                                        c_scan = c_text + " " + c_meta
                                        
                                        for match in re.finditer(PHONE_REGEX, c_scan):
                                            p = clean_phone(match.group(0))
                                            if p: unique_phones.add(p)
                                        unique_phones.update(extract_tel_links(page))
                                        unique_emails.update(extract_emails(c_scan))

                        except: pass
                    
                    address = "Not Found"
                    lines = content_text.split('\n')
                    for line in lines:
                        if re.search(PINCODE_REGEX, line):
                            address = line.strip()
                            break
                            
                    results.append({
                        "name": page_title,
                        "mobile": list(unique_phones),
                        "email": list(unique_emails),
                        "address": address,
                        "source": url,
                        "type": "Direct Site"
                    })

                # If we found data, break the retry loop
                # Check validation: at least 1 valid result with some data?
                valid_data_found = False
                if len(results) > 0:
                    for r in results:
                        if r['mobile'] or r['address'] != "Not Found":
                            valid_data_found = True
                            break
                
                if valid_data_found:
                    break
                else:
                    # If we are on the last attempt, don't clear results, just return what we have (even if empty/poor)
                    if attempt < 3:
                        interacted, captcha = handle_blocking_elements(page) # Try harder to clear blocks
                        if captcha:
                            browser.close()
                            return []
                        time.sleep(2)

            browser.close()
            return results
            
        except Exception as e:
            # console.print(f"[red]Error {url}: {e}[/red]")
            return []

def process_websites_list(input_file: str = "data/websites.json", output_file: str = "data/pg.json"):
    """
    Reads websites.json and runs extraction on each.
    """
    if not os.path.exists(input_file):
        console.print(f"[red]Input file {input_file} not found.[/red]")
        return
        
    with open(input_file, "r") as f:
        urls = json.load(f)
        
    console.print(f"[bold blue]Starting Universal List Extraction on {len(urls)} URLs...[/bold blue]")
    
    all_pgs = []
    # Load existing to append? Or overwrite? 
    # Usually safer to append or merge unique
    if os.path.exists(output_file):
        try:
            with open(output_file, "r") as f:
                all_pgs = json.load(f)
        except:
            pass
            
    # Simple dedupe by source+name
    seen_entries = set()
    for pg in all_pgs:
        seen_entries.add(pg.get("source", "") + pg.get("name", ""))
    
    for i, url in enumerate(urls):
        console.print(f"[{i+1}/{len(urls)}] Scanning: {url}...")
        
        # Determine strictness or headless based on URL?
        # Justdial blocks headless often. Maybe use False for specific domains?
        headless = True
        if "justdial" in url or "indiamart" in url:
             # console.print("   [yellow]Aggregator detected. Using Visible mode for data extraction...[/yellow]")
             # headless = False
             pass # Stick to headless for speed unless forced. user asked "no error".
             # Justdial might need visible mode to render phones.
             # but keeping headless=True is cleaner for now. If it fails, we can prompt. 
             # Actually, let's keep it robust.
        
        pg_data_list = extract_pg_data(url, headless=headless)
        
        new_count = 0
        if pg_data_list:
            for pg in pg_data_list:
                key = pg["source"] + pg["name"]
                if key not in seen_entries:
                    seen_entries.add(key)
                    all_pgs.append(pg)
                    new_count += 1
                    
            if new_count > 0:
                console.print(f"   [green]Found {new_count} listings![/green]")
                # Sample output
                if pg_data_list[0]['mobile']:
                     console.print(f"   Sample Mobile: {pg_data_list[0]['mobile']}")
        else:
            console.print("   [dim]No data found.[/dim]")
            
        # Incremental Save
        with open(output_file, "w") as f:
            json.dump(all_pgs, f, indent=2)

    console.print(f"\n[bold green]Extraction Complete! Total PGs: {len(all_pgs)}[/bold green]")
