from playwright.sync_api import sync_playwright
import time

def inspect_pagination():
    with sync_playwright() as p:
        # Run headed so user can potentially see/solve CAPTCHA
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 1024})
        page = context.new_page()
        
        print("Navigating to Brave Search...")
        page.goto("https://search.brave.com/search?q=PG+in+Ahmedabad", timeout=60000)
        
        # Check for CAPTCHA
        if "captcha" in page.title().lower() or "captcha" in page.url:
            print("CAPTCHA detected! Please solve it manually in the browser window.")
            # Wait for user to solve
            page.wait_for_function("document.title.indexOf('Captcha') === -1", timeout=120000)
            print("CAPTCHA solved (or bypassed). Proceeding...")
        
        time.sleep(5)
        
        print("Scrolling to bottom...")
        for _ in range(3):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
        
        # Dump footer HTML to file
        html = page.content()
        with open("debug_tools/brave_results.html", "w") as f:
            f.write(html)
        print("Saved HTML to debug_tools/brave_results.html")

        # Try to find specific text again
        more_btn = page.get_by_role("button", name="More results").first
        if more_btn.is_visible():
            print("Found 'More results' button!")
            print(f"Selector: {more_btn}")

        next_btn = page.get_by_role("button", name="Next").first
        if not next_btn.is_visible():
             next_btn = page.get_by_role("link", name="Next").first
        
        if next_btn.is_visible():
             print(f"Found 'Next' element! Tag: {next_btn.evaluate('el => el.tagName')}")
             # Get class and id
             print(f"Classes: {next_btn.get_attribute('class')}")
             print(f"ID: {next_btn.get_attribute('id')}")
        else:
             print("'Next' element not visible.")

        # Also look for the 'load more' specific classes seen in other brave implementations
        # commonly .btn-load-more or similar
        load_more = page.locator(".btn-load-more, .load-more, [id*='more']").all()
        if load_more:
            print(f"Found {len(load_more)} potential load more buttons by class/id.")
            for btn in load_more:
                if btn.is_visible():
                    print(f"Visible Candidate: {btn.inner_text()} | Class: {btn.get_attribute('class')}")

        browser.close()

if __name__ == "__main__":
    inspect_pagination()
