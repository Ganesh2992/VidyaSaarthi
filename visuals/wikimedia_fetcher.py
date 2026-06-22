"""
wikimedia_fetcher.py
Fetches educational images from Wikimedia Commons API.
Prefers diagrams, illustrations, and anatomical drawings over photos.
"""

import requests
import re

_COMMONS_API = "https://commons.wikimedia.org/w/api.php"


def _search_commons(query: str, limit: int = 10) -> list[dict]:
    """Search Wikimedia Commons for images matching the query."""
    try:
        # Target educational, labeled diagrams and illustrations
        search_terms = f"{query} diagram OR {query} illustration OR {query} drawing OR {query} map"
        params = {
            "action": "query",
            "generator": "search",
            "gsrnamespace": 6,      # File namespace
            "gsrsearch": f"filetype:bitmap|drawing {search_terms}",
            "gsrlimit": limit,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata|size",
            "iiurlwidth": 800,
            "format": "json",
        }
        resp = requests.get(_COMMONS_API, params=params, timeout=10,
                            headers={"User-Agent": "AITeachingAssistant/3.0"})
        if not resp.ok:
            return []
        
        pages = resp.json().get("query", {}).get("pages", {})
        results = []
        for page in pages.values():
            ii = page.get("imageinfo", [{}])[0]
            url = ii.get("thumburl") or ii.get("url", "")
            if not url:
                continue
            meta = ii.get("extmetadata", {})
            desc = meta.get("ImageDescription", {}).get("value", "")
            
            # Clean up the description text
            desc = re.sub(r"<[^>]+>", "", desc)  # Remove HTML tags
            desc = re.sub(r"\{\{[^\}]*\}\}", "", desc)  # Remove template code
            desc = desc.strip()
            if len(desc) > 250:
                desc = desc[:247] + "..."
            
            title = page.get("title", "").replace("File:", "")
            # Clean title for presentation
            clean_title = title.split(".")[0].replace("_", " ").replace("-", " ")
            
            results.append({
                "title": clean_title,
                "image_url": url,
                "description": desc or f"Educational diagram illustrating {query}.",
                "source": "Wikimedia Commons",
            })
        return results
    except Exception as e:
        print("[wikimedia_fetcher] Commons search error:", e)
        return []


def _clean_search_query(topic: str) -> str:
    # Split by common delimiters (e.g. "Plant Cell - Paudhe Ki Koshika" -> "Plant Cell")
    for delimiter in ["-", "(", "[", ":", "—"]:
        if delimiter in topic:
            topic = topic.split(delimiter)[0]
    
    # Remove any non-ASCII characters (like Hindi or Devanagari script)
    topic = ''.join(c for c in topic if ord(c) < 128)
    
    # Strip common visual command words
    topic = topic.replace("Show ", "").replace("Anatomy of ", "").replace("Diagram of ", "").replace("Structure of ", "")
    
    return topic.strip()


def fetch_wikimedia_image(topic: str) -> dict | None:
    """
    Fetch an educational image for the given topic.
    Returns dict with keys: title, image_url, description, source
    Returns None if nothing found.
    """
    query = _clean_search_query(topic)
    if not query:
        return None
        
    results = _search_commons(query)
    for r in results:
        if r.get("image_url"):
            # Return the first matching image
            return r
            
    return None
