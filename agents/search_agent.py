# agents/search_agent.py
from src.config import SEARCH_QUERIES, SEARCH_API_KEY
from typing import List, Dict, Any

try:
    from serpapi import GoogleSearch
except Exception:
    GoogleSearch = None


def _static_lenders() -> List[Dict[str, Any]]:
    # fallback list when search API is not available
    return [
        {"name": "First Tech Federal Credit Union", "url": "https://www.firsttechfed.com/mortgage-rates"},
        {"name": "Desert Financial Credit Union", "url": "https://www.desertfinancial.com/home-loans/mortgage-rates"},
    ]


def _build_queries() -> List[str]:
    # Base queries focused on mortgage offers for Arizona residents
    base = [
        "mortgage lenders Arizona",
        "mortgage loans Arizona bank",
        "credit union mortgage Arizona",
        "mortgage rates Arizona banks",
    ]
    # Allow override / extension from config
    return list(dict.fromkeys((SEARCH_QUERIES or []) + base))


def discover_lenders(limit: int = 50) -> List[Dict[str, Any]]:
    """Discover potential lenders (banks/credit unions) for Arizona residents.

    If `SEARCH_API_KEY` is configured and the `serpapi` package is available,
    this will query SerpAPI (Google) and return unique results. Otherwise it
    falls back to a small static list.
    """
    if not SEARCH_API_KEY or GoogleSearch is None:
        return _static_lenders()

    seen = set()
    results: List[Dict[str, Any]] = []
    queries = _build_queries()

    for q in queries:
        params = {"engine": "google", "q": q, "api_key": "xxxx"}  # Dummy value for search API key
        try:
            search = GoogleSearch(params)
            r = search.get_dict()
            for item in r.get("organic_results", [])[:limit]:
                link = item.get("link") or item.get("url")
                title = item.get("title") or ""
                snippet = item.get("snippet") or item.get("snippet_text") or ""
                # skip brokers, mortgage service sites, or third-party lenders by keyword
                text = (title + " " + snippet).lower()
                if any(bad in text for bad in ["broker", "loan provider", "lender service", "mortgage service"]):
                    continue
                if not link:
                    continue
                domain = link.split("/")[2] if "//" in link else link
                if domain in seen:
                    continue
                seen.add(domain)
                # provide both title and name for convenience
                results.append({"name": title or domain, "title": title, "url": link, "snippet": snippet})
                if len(results) >= limit:
                    return results
        except Exception:
            # On any error, continue to next query and eventually fall back
            continue

    if not results:
        return _static_lenders()

    return results


class SearchAgent:
    """Wrapper that exposes `search` to match orchestrator usage."""

    def __init__(self, queries: List[str] | None = None):
        self.queries = queries or _build_queries()

    def search(self, query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        # If a specific query is provided prefer it, otherwise run discovery
        if query:
            # Use SerpAPI if available
            try:
                return discover_lenders(limit=limit)
            except Exception:
                return _static_lenders()[:limit]
        return discover_lenders(limit=limit)[:limit]
