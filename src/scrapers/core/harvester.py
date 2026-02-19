
import json
import os
import re
import time
from playwright.sync_api import sync_playwright
from rich.console import Console
from src.core.utils import get_random_header, random_delay

console = Console()

class LocationHarvester:
    def __init__(self, city: str):
        self.city = city
        self.output_file = f"data/{city.lower().replace(' ', '_')}_locations.json"
        self.unique_locations = set()
        
    def _clean_keyword(self, name: str) -> str:
        """
        Removes generic suffixes to extract the core area name.
        e.g., "Nehrunagar Bus Stop" -> "Nehrunagar"
        """
        # Remove common transport suffixes
        name = re.sub(r'(?i)\b(Bus Station|Bus Stop|BRTS|Depot|Terminus|Stand)\b', '', name)
        
        # Remove institutional suffixes (optional, sometimes good to keep for "near X")
        # name = re.sub(r'(?i)\b(Campus|University|College|School|Hospital)\b', '', name)
        
        # Remove noise
        name = re.sub(r'(?i)\b(Public Toilet|Parking|ATM)\b', '', name)
        
        # Remove coords or codes if any (basic)
        
        return name.strip().strip(",-")

    def _scrape_category(self, page, category: str):
        query = f"{category} in {self.city}"
        console.print(f"[bold cyan]Searching for:[/bold cyan] {query}")
        
        url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        page.goto(url, timeout=60000)
        
        try:
            page.wait_for_selector('div[role="feed"]', timeout=30000)
        except:
            console.print(f"[yellow]Feed not found for {category}. Skipping...[/yellow]")
            return

        feed = page.locator('div[role="feed"]')
        
        # Scroll Loop
        end_of_list = False
        consecutive_no_new = 0
        last_count = 0
        
        while not end_of_list:
            # Extract Names
            elements = feed.locator("div[role='article']").all()
            if not elements:
                # Fallback for some views
                elements = feed.locator("a[href*='/maps/place/']").all()
            
            current_names = []
            for el in elements:
                try:
                    # Aria label usually has the name
                    name = el.get_attribute("aria-label")
                    if not name:
                        # Try finding h1/div inside
                        text_el = el.locator(".fontHeadlineSmall").first
                        if text_el.is_visible():
                            name = text_el.inner_text()
                    
                    if name:
                        current_names.append(name)
                except: pass
            
            # Process extracted names
            new_in_batch = 0
            for raw_name in current_names:
                if not raw_name: continue
                clean = self._clean_keyword(raw_name)
                if len(clean) > 2 and clean not in self.unique_locations:
                    self.unique_locations.add(clean)
                    new_in_batch += 1
                    # console.print(f"  [dim]+ {clean}[/dim]")
            
            if len(self.unique_locations) == last_count:
                consecutive_no_new += 1
            else:
                consecutive_no_new = 0
                
            last_count = len(self.unique_locations)
            
            # Scroll
            feed.focus()
            page.mouse.wheel(0, 3000)
            time.sleep(2)
            
            # End Check
            msg = page.locator("text=You've reached the end of the list")
            if msg.is_visible():
                end_of_list = True
            elif consecutive_no_new > 5:
                end_of_list = True
                
        console.print(f"[green]Finished {category}. Total Unique So Far: {len(self.unique_locations)}[/green]")


    def harvest(self):
        categories = [
            "Suburbs",
            "Bus Stations",
            "Colleges",
            "Industrial Estates"
        ]
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=get_random_header())
            page = context.new_page()
            
            for cat in categories:
                try:
                    self._scrape_category(page, cat)
                except Exception as e:
                    console.print(f"[red]Error scraping {cat}: {e}[/red]")
                    
            browser.close()
            
        self.save()
        
    def save(self):
        sorted_locs = sorted(list(self.unique_locations))
        with open(self.output_file, "w") as f:
            json.dump(sorted_locs, f, indent=2)
        console.print(f"[bold green]Harvest Complete! Saved {len(sorted_locs)} locations to {self.output_file}[/bold green]")

def run_harvester(city: str):
    harvester = LocationHarvester(city)
    harvester.harvest()
