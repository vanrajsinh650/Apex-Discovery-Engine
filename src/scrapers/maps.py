import time
import re
import json
import os
from playwright.sync_api import sync_playwright
from rich.console import Console
from src.core.utils import get_random_header, random_delay, normalize_url, save_unique_urls
from src.core.data_manager import MasterDataManager

console = Console()

def search_google_maps(query: str, limit: int = 50, headless: bool = False, output_file: str = "data/master_pg_list.json"):
    """
    Scrapes Google Maps and upserts data into the Master List.
    """
    console.print(f"[bold blue]Starting Google Maps Data Scraper for:[/bold blue] {query}")
    
    # Initialize Data Manager
    manager = MasterDataManager(output_file)
    
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
    
    found_websites = set() # Optional: keep saving to websites.json for compatibility
    count = 0
    unique_ids = set() # Local session deduping to avoid clicking same thing twice
    
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
                page.wait_for_selector('div[role="feed"]', timeout=30000)
            except:
                console.print("[yellow]Feed not found. Checking for consent/captcha...[/yellow]")
                time.sleep(5)
            
            feed = page.locator('div[role="feed"]')
            
            processed_indices = set()
            end_of_list = False
            consecutive_no_new_items = 0
            
            while count < limit or (limit <= 0 and not end_of_list):
                items = feed.locator("div[role='article']").all()
                if not items:
                     items = feed.locator("a[href*='/maps/place/']").all()

                new_items_found_in_batch = 0
                
                for i, item in enumerate(items):
                    if i in processed_indices:
                        continue
                        
                    processed_indices.add(i)
                    new_items_found_in_batch += 1
                    
                    try:
                        item.scroll_into_view_if_needed()
                        item.click() 
                        random_delay(1, 2)
                        
                        try:
                            page.wait_for_selector("div[role='main'] h1", timeout=3000)
                        except:
                            time.sleep(1)
                            
                        # EXTRACT DATA
                        data = extract_panel_data(page)
                        
                        # Session Dedupe
                        key = data["name"] + "|" + data["address"]
                        if key not in unique_ids:
                            unique_ids.add(key)
                            
                            # Standardize for Manager
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
                            count += 1
                            
                            console.print(f"   [green]{status}:[/green] {data['name']} | :phone: {data['phone']}")
                            
                            if data.get("website"):
                                norm_url = normalize_url(data["website"])
                                if norm_url: found_websites.add(norm_url)
 
                            # Incremental Save
                            if count % 5 == 0:
                                manager.save_master()
                                # Legacy support
                                if found_websites:
                                    save_unique_urls(list(found_websites), "data/websites.json")
                                    found_websites.clear()
                                    
                        if limit > 0 and count >= limit:
                            break
                            
                    except Exception as e:
                        pass
                
                if limit > 0 and count >= limit:
                    console.print(f"[green]Hit limit of {limit} records.[/green]")
                    break

                # Scroll
                feed.focus()
                page.mouse.wheel(0, 3000)
                time.sleep(2)
                
                if page.locator("text=You've reached the end of the list").is_visible():
                    end_of_list = True
                    break
                    
                if new_items_found_in_batch == 0:
                    consecutive_no_new_items += 1
                    if consecutive_no_new_items > 5:
                        break
                else:
                    consecutive_no_new_items = 0

            # Final Save
            manager.save_master()
            if found_websites:
                save_unique_urls(list(found_websites), "data/websites.json")
                
            console.print(f"[bold green]Scraping Complete. Processed {count} records.[/bold green]")
            browser.close()
            
        except Exception as e:
            console.print(f"[bold red]Critical Error:[/bold red] {e}")

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
