# agents/eligibility_agent.py
import aiohttp
import asyncio
from config import AZ_KEYWORDS


def _check_text_for_keywords(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    return any(keyword in t for keyword in AZ_KEYWORDS)



# Async version of eligibility check
async def fetch_url(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            return await response.text()
    except Exception:
        return None

async def is_eligible_async(lender):
    url = lender.get("url")
    if not url:
        return False
    async with aiohttp.ClientSession() as session:
        html = await fetch_url(session, url)
        if html and _check_text_for_keywords(html):
            return True
        # fallback: Playwright logic (sync fallback for now)
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=15000)
                content = page.content()
                browser.close()
                return _check_text_for_keywords(content)
        except Exception:
            return False


# Helper to check all lenders in parallel
async def check_all_lenders(lenders):
    tasks = [is_eligible_async(lender) for lender in lenders]
    return await asyncio.gather(*tasks)

# Synchronous wrapper for is_eligible_async
def is_eligible(lender):
    """Sync wrapper for is_eligible_async for compatibility with imports."""
    return asyncio.run(is_eligible_async(lender))