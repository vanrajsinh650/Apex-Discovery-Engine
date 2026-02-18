import re
import asyncio
import json
import os
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright
from rich.console import Console
from tqdm.asyncio import tqdm
from src.core.utils import get_random_header, random_delay
from src.core.data_manager import MasterDataManager
from src.scrapers.listing import (
    clean_phone, extract_emails, extract_tel_links, 
    handle_blocking_elements, reveal_contacts, 
    PHONE_REGEX, PINCODE_REGEX
)

console = Console()

# --- Configuration ---
BLACKLIST_DOMAINS = ["quora.com", "reddit.com", "translate.google.com", "twitter.com", "youtube.com"]

SKIP_KEYWORDS = ["news", "article", "headline", "report", "blog"]
REQUIRED_KEYWORDS = ["book", "room", "stay", "accommodation", "hostel", "pg", "paying guest", "residency", "living"]

class AsyncDeepCrawler:
    def __init__(self, headless: bool = True):
        self.headless = headless
        
    def is_relevant_content(self, text, url):
        """
        Filters out noise (News, Blogs) unless they mention 'Room'/'Stay'.
        """
        text_lower = text.lower()
        url_lower = url.lower()
        
        for domain in BLACKLIST_DOMAINS:
            if domain in url_lower:
                return False
                
        has_skip = any(k in text_lower for k in SKIP_KEYWORDS)
        has_required = any(k in text_lower for k in REQUIRED_KEYWORDS)
        
        if has_skip and not has_required:
            return False
            
        return True

    def sanitize_address(self, address_text):
        if not address_text: return None
        if re.search(PHONE_REGEX, address_text):
            return None
        valid_indicators = ["pin", "zip", "road", "sector", "block", "opp", "near", "behind", "colony", "nagar", "street", "lane"]
        if not any(ind in address_text.lower() for ind in valid_indicators):
            return None
        return address_text

    async def extract_smart_name(self, page):
        try:
            h1s = page.locator("h1").all()
            for h1_handle in await h1s:
                text = (await h1_handle.inner_text()).strip()
                if len(text) > 3 and len(text) < 50:
                    bad_words = ["best", "affordable", "cheap", "top", "list", "pg in", "hostel in"]
                    if not any(w in text.lower() for w in bad_words):
                        return text
        except: pass
        
        try:
            imgs = page.locator("img[alt*='logo'], img[class*='logo']").all()
            for img in await imgs:
                alt = await img.get_attribute("alt")
                if alt and len(alt) > 3:
                    bad_words = ["logo", "brand", "header", "image"]
                    clean_alt = alt
                    for w in bad_words:
                        clean_alt = clean_alt.replace(w, "").replace(w.title(), "")
                    clean_alt = clean_alt.strip()
                    if len(clean_alt) > 3:
                        return clean_alt
        except: pass
        
        try:
            title = await page.title()
            clean_title = re.split(r"[|\-:]", title)[0].strip()
            return clean_title
        except: 
            return "Unknown Entity"

    async def get_priority_links(self, page, base_url):
        priority_keywords = ["contact", "about", "reach", "location", "connect"]
        links = []
        try:
            elements = await page.locator("a[href]").all()
            domain = urlparse(base_url).netloc
            for el in elements:
                href = await el.get_attribute("href")
                if not href or href.startswith("#") or "javascript" in href: continue
                full_url = urljoin(base_url, href)
                if urlparse(full_url).netloc != domain: continue
                text = (await el.inner_text() or "").lower()
                href_lower = href.lower()
                if any(kw in href_lower or kw in text for kw in priority_keywords):
                    links.append(full_url)
        except: pass
        return list(set(links))

    async def sub_process_domain(self, browser, root_domain, sub_pages):
        entity = {
            "root_domain": root_domain,
            "name": "",
            "mobile": set(),
            "email": set(),
            "address": None,
            "location_pages": list(sub_pages),
            "website": "https://" + root_domain, # Generic website for matching
            "source": "https://" + root_domain
        }
        
        context = await browser.new_context(user_agent=get_random_header())
        page = await context.new_page()
        start_url = "https://" + root_domain
        targets = [start_url]
        
        try:
            try:
                await page.goto(start_url, timeout=30000)
            except:
                try: await page.goto(start_url.replace("https", "http"), timeout=20000)
                except: 
                    await context.close()
                    return None
            
            body_text = await page.locator("body").inner_text()
            if not self.is_relevant_content(body_text, start_url):
                await context.close()
                return None
            
            # Name
            entity["name"] = await self.extract_smart_name(page)
            
            # Data
            phones = set()
            for match in re.finditer(PHONE_REGEX, body_text):
                p = clean_phone(match.group(0))
                if p: phones.add(p)
            entity["mobile"].update(phones)
            entity["email"].update(extract_emails(body_text))
            
            lines = body_text.split('\n')
            for line in lines:
                if len(line) < 150:
                    sanitized = self.sanitize_address(line)
                    if sanitized:
                        entity["address"] = sanitized
                        break
            
            priority = await self.get_priority_links(page, start_url)
            targets.extend(priority[:4])
            
            for link in targets[1:]:
                try:
                    await page.goto(link, timeout=20000)
                    random_delay(1, 2)
                    sub_text = await page.locator("body").inner_text()
                    
                    for match in re.finditer(PHONE_REGEX, sub_text):
                        p = clean_phone(match.group(0))
                        if p: entity["mobile"].update([p])
                    entity["email"].update(extract_emails(sub_text))
                    
                    if not entity["address"]:
                        for line in sub_text.split('\n'):
                             if len(line) < 150:
                                sanitized = self.sanitize_address(line)
                                if sanitized:
                                    entity["address"] = sanitized
                                    break
                except: pass
                
        except Exception as e:
            pass
        finally:
            await context.close()
            
        entity["mobile"] = list(entity["mobile"])
        entity["email"] = list(entity["email"])
        
        if not entity["mobile"] and not entity["email"] and not entity["address"]:
             return None
             
        return entity

async def run_batch(urls, output_file):
    # Initialize Manager
    manager = MasterDataManager(output_file)
    
    domain_map = {}
    for u in urls:
        if not u.startswith("http"): u = "https://" + u
        parsed = urlparse(u)
        root = parsed.netloc.replace("www.", "")
        if root not in domain_map:
            domain_map[root] = []
        domain_map[root].append(u)
        
    console.print(f"[bold]Identified {len(domain_map)} unique entities from {len(urls)} URLs.[/bold]")
    
    crawler = AsyncDeepCrawler(headless=True)
    
    # Check processed?
    # Hard to check processed status easily with upserts.
    # We can check if domain already exists in manager.data?
    # But we want to re-process if we have better logic?
    # Let's assume re-processing is okay or user manages input list.
    
    roots_to_process = list(domain_map.keys())
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        sem = asyncio.Semaphore(3)
        
        async def sem_task(root):
            async with sem:
                return await crawler.sub_process_domain(browser, root, domain_map[root])
        
        batch_size = 10
        total = len(roots_to_process)
        
        with tqdm(total=total, desc="Analyzing Entities") as pbar:
            for i in range(0, total, batch_size):
                batch_roots = roots_to_process[i:i+batch_size]
                coroutines = [sem_task(r) for r in batch_roots]
                batch_results = await asyncio.gather(*coroutines)
                
                # Upsert Results
                valid_count = 0
                for entity in batch_results:
                    if entity:
                        manager.upsert_entity(entity)
                        valid_count += 1
                
                # Save
                manager.save_master()
                pbar.update(len(batch_roots))
                
        await browser.close()
        
    console.print(f"[bold green]Entity Analysis Complete. Master List Updated.[/bold green]")

def process_deep_study(input_file: str, output_file: str):
    if not os.path.exists(input_file):
        print("Input not found")
        return
    with open(input_file, "r") as f:
        urls = json.load(f)
    asyncio.run(run_batch(urls, output_file))
