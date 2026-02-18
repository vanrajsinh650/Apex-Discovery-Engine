from src.core.utils import normalize_url

def extract_local_pack(page) -> list[str]:
    """ Extract links from Local/Map Pack if present """
    local_links = []
    try:
        # Generic approach for Brave/Bing map cards
        cards = page.locator(".local-pack-item, .map-card, .loc-card").all()
        for card in cards:
            web_link = card.locator("a[title='Website'], a:has-text('Website')").first
            if web_link.is_visible():
                href = web_link.get_attribute("href")
                if href: 
                    norm = normalize_url(href)
                    if norm:
                        local_links.append(norm)
    except:
        pass
    return local_links
