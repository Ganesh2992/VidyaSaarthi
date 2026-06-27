"""
wikimedia_fetcher.py
Fetches educational images using a hybrid approach:
1. Tries to find a high-quality labeled diagram/SVG on Wikimedia Commons.
2. Falls back to Wikipedia's main page image if no diagram is found.
"""

import requests
import re

_WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
_COMMONS_API = "https://commons.wikimedia.org/w/api.php"

def clean_search_query(q: str) -> str:
    """Clean query for Wikipedia/Wikimedia to maximize search matches."""
    # 1. Take the part before any dash, colon or separator
    for sep in ("—", "-", ":", "|"):
        if sep in q:
            q = q.split(sep)[0]
    
    # 2. Lowercase and remove common action/noise words
    q_clean = q.lower().strip()
    noise_words = [
        "explain me", "explain", "what is", "what are", "define", "show me", 
        "show", "diagram of", "diagram", "how does", "how do", "works", "work", 
        "about", "concept of", "the concept of", "process of", "the process of",
        "quiz", "test", "questions", "mcq", "on"
    ]
    for word in noise_words:
        q_clean = re.sub(r'\b' + re.escape(word) + r'\b', '', q_clean)
        
    # 3. Clean up extra spaces and punctuation
    q_clean = re.sub(r'[^\w\s]', '', q_clean)
    q_clean = " ".join(q_clean.split())
    
    return q_clean if q_clean else q.strip()

def fetch_wikimedia_image(topic: str) -> dict | None:
    if not topic or not topic.strip():
        return None
        
    query = clean_search_query(topic)
    
    # STEP 1: Search Commons for explicitly labeled diagrams/SVGs
    try:
        commons_params = {
            "action": "query",
            "generator": "search",
            "gsrnamespace": 6,
            "gsrsearch": f'{query} diagram',
            "gsrlimit": 5,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata|size",
            "format": "json",
        }
        resp = requests.get(_COMMONS_API, params=commons_params, timeout=5, headers={"User-Agent": "AITeachingAssistant/3.0"})
        if resp.ok:
            pages = resp.json().get("query", {}).get("pages", {})
            best_img = None
            for page in pages.values():
                title = page.get("title", "").lower()
                ii = page.get("imageinfo", [{}])[0]
                url = ii.get("thumburl") or ii.get("url", "")
                
                if not url: continue
                
                # Exclude explicitly non-English diagrams if they are marked as such, 
                # but allow neutral or 'en' SVGs.
                if re.search(r'-(fr|es|de|ru|zh|ar|bn|hi)\.svg', title):
                    continue
                    
                meta = ii.get("extmetadata", {})
                desc = meta.get("ImageDescription", {}).get("value", "")
                desc = re.sub(r"<[^>]+>", "", desc).strip()
                
                # Basic relevance check: the query words must appear in title or description
                query_words = query.lower().split()
                text_to_search = (title + " " + desc).lower()
                if not all(word in text_to_search for word in query_words):
                    continue
                    
                if len(desc) > 200: desc = desc[:197] + "..."
                
                clean_title = page.get("title", "").replace("File:", "").split(".")[0]
                
                # Prefer SVGs as they are usually the best labeled diagrams
                if title.endswith(".svg"):
                    best_img = {"title": clean_title, "image_url": url, "description": desc, "source": "Wikimedia Commons (Diagram)"}
                    break
                elif not best_img:
                    best_img = {"title": clean_title, "image_url": url, "description": desc, "source": "Wikimedia Commons"}
            
            if best_img:
                return best_img
    except Exception as e:
        pass

    # STEP 2: Fallback to Wikipedia Page Images (for topics like 'Solar System' or general photos)
    try:
        wiki_params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrlimit": 1,
            "prop": "pageimages|extracts",
            "exintro": 1,
            "explaintext": 1,
            "format": "json",
            "pithumbsize": 800
        }
        
        resp = requests.get(_WIKIPEDIA_API, params=wiki_params, timeout=5, headers={"User-Agent": "AITeachingAssistant/3.0"})
        if resp.ok:
            pages = resp.json().get("query", {}).get("pages", {})
            if pages:
                page = list(pages.values())[0]
                img_url = page.get("thumbnail", {}).get("source", "")
                if img_url:
                    title = page.get("title", "")
                    # Ensure at least one word from the clean query is in the title to prevent unrelated images
                    query_words = set(query.lower().split())
                    title_words = set(title.lower().split())
                    
                    if not query_words.intersection(title_words) and len(query_words) > 0:
                        return None
                        
                    desc = page.get("extract", "").strip()
                    if len(desc) > 200: desc = desc[:197] + "..."
                    return {
                        "title": title,
                        "image_url": img_url,
                        "description": desc or f"Educational image for {query}.",
                        "source": "Wikipedia"
                    }
    except Exception as e:
        pass
        
    return None
