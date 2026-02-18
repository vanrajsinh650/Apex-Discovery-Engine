import json
from collections import Counter
from urllib.parse import urlparse

def analyze_yield(file_path="data/pg.json"):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("File not found.")
        return

    total = len(data)
    with_mobile = 0
    with_mobile_and_name = 0
    
    domain_stats = Counter()
    domain_success = Counter()
    
    for entry in data:
        url = entry.get("source", "")
        domain = urlparse(url).netloc.replace("www.", "")
        
        has_mobile = len(entry.get("mobile", [])) > 0
        has_name = entry.get("name") != "Unknown Listing"
        
        domain_stats[domain] += 1
        if has_mobile:
            with_mobile += 1
            domain_success[domain] += 1
        
        if has_mobile and has_name:
            with_mobile_and_name += 1
            
    print(f"Total Records: {total}")
    print(f"With Mobile: {with_mobile} ({with_mobile/total*100:.1f}%)")
    print(f"With Name & Mobile: {with_mobile_and_name} ({with_mobile_and_name/total*100:.1f}%)")
    
    print("\n--- Domain Performance (Top 20) ---")
    print(f"{'Domain':<30} | {'Total':<6} | {'Found':<6} | {'Yield %':<6}")
    print("-" * 60)
    
    for domain, count in domain_stats.most_common(20):
        found = domain_success[domain]
        yield_pct = (found / count) * 100
        print(f"{domain:<30} | {count:<6} | {found:<6} | {yield_pct:.1f}%")

if __name__ == "__main__":
    analyze_yield()
