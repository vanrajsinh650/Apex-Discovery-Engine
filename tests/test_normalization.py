from src.common.utils import normalize_url

def test_normalization():
    test_cases = [
        # Aggregators -> Root
        ("https://www.magicbricks.com/property-for-sale-in-ahmedabad-pppfs", "https://magicbricks.com/"),
        ("http://99acres.com/search/property/buy/residential-all/ahmedabad?src=SEARCH", "https://99acres.com/"),
        ("https://www.justdial.com/Ahmedabad/PG-In-Ahmedabad/nct-10360860", "https://justdial.com/"),
        
        # Local Biz -> Keep Path
        ("https://shree-ganesh-pg.business.site/", "https://shree-ganesh-pg.business.site"),
        ("http://www.my-local-pg.com/contact-us/", "https://my-local-pg.com/contact-us"),
        
        # Cleanup
        ("www.example.com", "https://example.com/"), # Non-aggregator, but clean host? Wait, non-aggregator logic keeps path. 
        # "www.example.com" -> defaults to http, parsed.path is empty. 
        # If I pass "www.example.com", parsed.path might be "www.example.com" if scheme missing? 
        # normalized adds https:// first. -> https://www.example.com -> example.com
        
        ("https://example.com/foo/?bar=baz", "https://example.com/foo"),
    ]
    
    print("Running Normalization Tests...")
    failures = 0
    for input_url, expected in test_cases:
        result = normalize_url(input_url)
        # Note: My logic for non-aggregators ensures no trailing slash if path exists, 
        # but if path is empty, it might return "https://hostname" without slash?
        # Let's check logic: path = parsed.path.rstrip("/") -> "https://hostname" + ""
        # So "https://example.com/" -> "https://example.com"
        
        # Adjust expectation for root non-aggregator if needed
        if input_url == "www.example.com": expected = "https://example.com"
        
        if result != expected:
            print(f"[FAIL] Input: {input_url}\n       Expected: {expected}\n       Got:      {result}")
            failures += 1
        else:
            print(f"[PASS] {input_url} -> {result}")
            
    if failures == 0:
        print("\nAll tests passed!")
    else:
        print(f"\n{failures} tests failed.")

if __name__ == "__main__":
    test_normalization()
