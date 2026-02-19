import time
import re
import json
import os
from playwright.sync_api import sync_playwright
from rich.console import Console
from src.core.utils import get_random_header, random_delay, normalize_url, save_unique_urls
from src.core.data_manager import MasterDataManager

console = Console()

def search_google_maps(query: str, limit: int = 50, headless: bool = False, output_file: str = "data/master_pg_list.json", city: str = None):
    """
    Scrapes Google Maps and upserts data into the Master List.
    Returns: List of unique website URLs found.
    """
    console.print(f"[bold blue]Starting Google Maps Data Scraper for:[/bold blue] {query}")
    
    # Initialize Data Manager
    manager = MasterDataManager(output_file, city=city)
    
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
    
    found_websites = set()
    count = 0
    unique_ids = set() 
    
    # --- Velocity Optimization ---
    consecutive_duplicates = 0
    MAX_CONSECUTIVE_DUPLICATES = 5 # Exit early if we hit 5 existing PGs in a row
    consecutive_no_new_data = 0
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent=get_random_header(),
                locale="en-US"
            )
            page = context.new_page()
            
            console.print(f"Navigating to: {url}")
            page.goto(url, timeout=60000)
            
            try:
                page.wait_for_selector('div[role="feed"]', timeout=20000)
            except:
                console.print("[yellow]Feed not found. Checking for results...[/yellow]")
                time.sleep(2)
            
            feed = page.locator('div[role="feed"]')
            
            processed_indices = set()
            end_of_list = False
            
            while count < limit or (limit <= 0 and not end_of_list):
                items = feed.locator("div[role='article']").all()
                if not items:
                     items = feed.locator("a[href*='/maps/place/']").all()

                new_items_in_loop = 0
                
                for i, item in enumerate(items):
                    if i in processed_indices:
                        continue
                        
                    processed_indices.add(i)
                    new_items_in_loop += 1
                    
                    try:
                        item.scroll_into_view_if_needed()
                        item.click() 
                        # snappier delay
                        random_delay(0.8, 1.5)
                        
                        try:
                            # Short timeout for panel load
                            page.wait_for_selector("div[role='main'] h1", timeout=2000)
                        except: pass
                            
                        # EXTRACT DATA
                        data = extract_panel_data(page)
                        
                        # Session Dedupe
                        key = (data["name"] + "|" + data["address"]).lower()
                        
                        if key not in unique_ids:
                            unique_ids.add(key)
                            
                            entity = {
                                "name": data["name"],
                                "address": data["address"],
                                "mobile": [data["phone"]] if data["phone"] else [],
                                "website": data["website"],
                                "source": "google.com/maps",
                                "rating": data["rating"],
                                "reviews": data["reviews"]
                            }
                            
                            # UPSERT to Master List
                            status = manager.upsert_entity(entity)
                            
                            if "Matched" in status or "Updated" in status or "Added" in status:
                                # This is "New" or "Useful" data
                                if "Skipped" not in status:
                                    count += 1
                                    consecutive_duplicates = 0 # Reset duplicate counter
                                    console.print(f"   [green]{status}:[/green] {data['name']} | :phone: {data['phone']}")
                                else:
                                    # It matched but was skipped (blacklist/wrong city)
                                    consecutive_duplicates += 1
                            else:
                                if "Skipped (Already exists)" in status:
                                    consecutive_duplicates += 1
                                    console.print(f"   [dim yellow]Duplicate:[/dim yellow] {data['name']}")
                                else:
                                    console.print(f"   [dim red]{status}:[/dim red] {data['name']}")
                            
                            if data.get("website"):
                                norm_url = normalize_url(data["website"])
                                if norm_url: found_websites.add(norm_url)
  
                            if count % 5 == 0:
                                manager.save_master()
                                    
                        if limit > 0 and count >= limit:
                            break
                        
                        # --- EARLY EXIT LOGIC ---
                        if consecutive_duplicates >= MAX_CONSECUTIVE_DUPLICATES:
                            console.print(f"[bold yellow]Early Exit: Hit {MAX_CONSECUTIVE_DUPLICATES} consecutive existing records. Moving to next search.[/bold yellow]")
                            end_of_list = True
                            break
                            
                    except Exception as e:
                        pass
                
                if end_of_list or (limit > 0 and count >= limit):
                    break

                # Scroll
                feed.focus()
                page.mouse.wheel(0, 3000)
                time.sleep(1.5)
                
                if page.locator("text=You've reached the end of the list").is_visible():
                    break
                    
                if new_items_in_loop == 0:
                    consecutive_no_new_data += 1
                    if consecutive_no_new_data > 3: # Faster bail out if scrolling isn't working
                        break
                else:
                    consecutive_no_new_data = 0

            # Final Save
            manager.save_master()
            if found_websites:
                save_unique_urls(list(found_websites), "data/websites.json")
                
            console.print(f"[bold green]Scraping Complete. Processed {count} useful records.[/bold green]")
            browser.close()
            return list(found_websites)
            
        except Exception as e:
            console.print(f"[bold red]Critical Error Maps:[/bold red] {e}")
            return []

def extract_panel_data(page):
    """
    Extracts details from the currently open side panel.
    """
    data = {"name": "", "phone": "", "address": "", "website": "", "rating": "", "reviews": ""}
    
    try:
        h1 = page.locator("div[role='main'] h1").first
        if h1.is_visible():
            data["name"] = h1.inner_text()
            
        try:
            stars = page.locator("div[role='main'] span[aria-label*='stars']").first
            if stars.is_visible():
                 aria = stars.get_attribute("aria-label")
                 data["rating"] = aria
        except: pass

        try:
            addr_btn = page.locator("button[data-item-id='address']").first
            if addr_btn.is_visible():
                data["address"] = addr_btn.get_attribute("aria-label").replace("Address: ", "")
        except: pass
        
        try:
            phone_btn = page.locator("button[data-item-id*='phone']").first
            if phone_btn.is_visible():
                raw_phone = phone_btn.get_attribute("aria-label").replace("Phone: ", "")
                data["phone"] = raw_phone
        except: pass
        
        try:
            web_link = page.locator("a[data-item-id='authority']").first
            if web_link.is_visible():
                href = web_link.get_attribute("href")
                data["website"] = href
        except: pass
        
    except: pass
    return data
