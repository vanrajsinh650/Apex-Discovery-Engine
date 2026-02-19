from src.core.utils import console, normalize_url

def search_ddg(query: str, limit: int = 50, headless: bool = True):
    """
    Searches DuckDuckGo using the DDGS library.
    """
    console.print(f"[bold yellow]Starting DuckDuckGo Search for:[/bold yellow] {query}")
    unique_links = set()
    
    try:
        from duckduckgo_search import DDGS
        
        # DDGS is synchronous
        max_results = 100 if limit <= 0 else min(limit, 100)
        
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
            
            if results:
                for r in results:
                    href = r.get("href")
                    if href:
                        norm = normalize_url(href)
                        if norm and norm not in unique_links:
                            unique_links.add(norm)
                            console.print(f"Found (DDG): {norm}")
                            if limit > 0 and len(unique_links) >= limit:
                                break
            else:
                console.print("[red]DDG returned no results.[/red]")
                
    except Exception as e:
        console.print(f"[bold red]DDG Error:[/bold red] {e}")
        
    return list(unique_links)
