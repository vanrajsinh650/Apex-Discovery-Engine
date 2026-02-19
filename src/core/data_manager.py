import json
import os
import re
from urllib.parse import urlparse
from rich.console import Console
from src.exporters.excel import export_to_excel_perfect

console = Console()

class MasterDataManager:
    BLACKLIST_TERMS = ["news", "samachar", "quora", "wikipedia", "article", "report", "times of india", "divya bhaskar"]

    def __init__(self, master_file: str = "data/master_pg_list.json", city: str = None):
        self.master_file = master_file
        self.city = city.lower() if city else None
        self.data = []
        self.unverified_numbers = []
        self.load_master()
        
    def load_master(self):
        """Loads existing master list."""
        if os.path.exists(self.master_file):
            try:
                with open(self.master_file, "r") as f:
                    self.data = json.load(f)
            except json.JSONDecodeError:
                self.data = []
        else:
            self.data = []
            
    def save_master(self):
        """Atomically saves master list."""
        try:
            # Save main data
            with open(self.master_file, "w") as f:
                json.dump(self.data, f, indent=2)
                
            # Save verification log if needed
            if self.unverified_numbers:
                with open("data/unverified_numbers.json", "w") as f:
                    json.dump(self.unverified_numbers, f, indent=2)
        except Exception as e:
            console.print(f"[red]Error saving master data: {e}[/red]")
            
        # Trigger perfect excel export
        try:
            export_to_excel_perfect(self.master_file)
        except Exception as e:
            console.print(f"[red]Error triggering excel export: {e}[/red]")

    def clean_phone_10_digit(self, phone):
        """
        Standardizes phone number to 10 digits.
        Removes +91, 0 prefix, spaces, dashes.
        """
        if not phone: return None
        # Remove non-digits
        digits = re.sub(r"\D", "", str(phone))
        
        # Handle country code
        if len(digits) > 10:
            if digits.startswith("91"):
                digits = digits[2:]
            elif digits.startswith("0"):
                digits = digits[1:]
                
        if len(digits) == 10:
            return digits
        return None

    def get_domain(self, url):
        if not url: return None
        if not url.startswith("http"): url = "https://" + url
        try:
            return urlparse(url).netloc.replace("www.", "")
        except: return None
        
    def normalize_name(self, name):
        if not name: return ""
        return re.sub(r'[^a-zA-Z0-9]', '', name).lower()

    def validate_location(self, entity):
        """
        Strictly validates if the entity belongs to Ahmedabad or Gandhinagar area.
        Returns: (bool, reason)
        """
        address = (entity.get("address") or "").lower()
        if not address:
            # If no address, we can't be sure, but user wants strict check.
            # However, normally we trust the query context. 
            # For "Fast Hub", we'll be strict.
            return True, "No address (Assuming query context)"
            
        # Strict validation requirements: Ahmedabad OR Gandhinagar OR 380 OR 38xxxx
        has_ahmedabad = "ahmedabad" in address
        has_gandhinagar = "gandhinagar" in address
        has_380 = "380" in address
        has_pincode = bool(re.search(r"\b38\d{4}\b", address))
        
        if has_ahmedabad or has_gandhinagar or has_380 or has_pincode:
            return True, "Matched"
            
        return False, "Bad Location (Not Ahmedabad/Gandhinagar/38xxxx)"

    def upsert_entity(self, new_entity):
        """
        updates or inserts an entity into the master list.
        Matching logic: Domain (Primary) OR Name (Secondary).
        """
        # --- Strict Filter ---
        name = (new_entity.get("name") or "").lower()
        if any(term in name for term in self.BLACKLIST_TERMS):
            return "Skipped (Blacklist)"
            
        # --- Location Validation ---
        is_valid, reason = self.validate_location(new_entity)
        if not is_valid:
            # console.print(f"[dim red]Skipped Location: {reason}[/dim red]")
            return f"Skipped ({reason})"

        matched_idx = -1
        
        # 1. Match by Domain (High Confidence)
        new_domain = self.get_domain(new_entity.get("source") or new_entity.get("website"))
        
        if new_domain:
            for i, entity in enumerate(self.data):
                existing_domain = self.get_domain(entity.get("source") or entity.get("website"))
                if existing_domain and existing_domain == new_domain:
                    matched_idx = i
                    break
        
        # 2. Match by Name (If domain didn't match)
        if matched_idx == -1 and new_entity.get("name"):
            norm_name = self.normalize_name(new_entity["name"])
            if norm_name: # Only if name is valid
                for i, entity in enumerate(self.data):
                    if self.normalize_name(entity.get("name")) == norm_name:
                        matched_idx = i
                        break
                    
        if matched_idx != -1:
            # MERGE
            self.data[matched_idx] = self.merge_fields(self.data[matched_idx], new_entity)
            return "Updated"
        else:
            # INSERT
            # Clean before inserting
            new_entity = self.clean_entity(new_entity)
            self.data.append(new_entity)
            return "Inserted"

    def merge_fields(self, existing, new):
        """
        Smart merge of two entity dicts.
        """
        merged = existing.copy()
        
        # 1. Phones: Union + Standardize
        existing_phones = set()
        for p in existing.get("mobile", []):
            cp = self.clean_phone_10_digit(p)
            if cp: existing_phones.add(cp)
            
        new_phones = set()
        for p in new.get("mobile", []):
            cp = self.clean_phone_10_digit(p)
            if cp: new_phones.add(cp)
        
        # Conflict Checking (Visual Only)
        # If we have existing phones and new phones, and they are disjoint sets, it's a conflict
        if existing_phones and new_phones and existing_phones.isdisjoint(new_phones):
             self.unverified_numbers.append({
                 "name": existing.get("name"),
                 "existing_phones": list(existing_phones),
                 "new_phones": list(new_phones),
                 "source_existing": existing.get("source"),
                 "source_new": new.get("source")
             })
        
        combined_phones = existing_phones.union(new_phones)
        merged["mobile"] = list(combined_phones)
        
        # 2. Emails: Union
        existing_emails = set(existing.get("email", []))
        new_emails = set(new.get("email", []))
        merged["email"] = list(existing_emails.union(new_emails))
        
        # 3. Address: Priority to Google Maps
        # If new source is Maps, overwrite. Else keep existing if present.
        is_new_maps = "google" in (new.get("source") or "")
        
        if is_new_maps and new.get("address"):
             merged["address"] = new.get("address")
        elif not existing.get("address") and new.get("address"):
            merged["address"] = new.get("address")
            
        # 4. Website/Source
        if not existing.get("website") and new.get("website"):
            merged["website"] = new.get("website")

        # 5. Location Pages (Merge lists)
        existing_pages = set(existing.get("location_pages", []))
        new_pages = set(new.get("location_pages", []))
        merged["location_pages"] = list(existing_pages.union(new_pages))
            
        return merged

    def clean_entity(self, entity):
        """Cleans fields of a new entity before insertion."""
        # Clean phones
        phones = set()
        for p in entity.get("mobile", []):
            cp = self.clean_phone_10_digit(p)
            if cp: phones.add(cp)
        entity["mobile"] = list(phones)
        return entity
