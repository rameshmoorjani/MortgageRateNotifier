import os
from agents.scraper_agent import scrape_rates
from agents.parser_agent import extract_rates

# List of lender URLs to debug
LENDER_URLS = [
    "https://www.cuwest.org/borrowing/mortgages/refinancing"
]

os.makedirs("debug_html", exist_ok=True)

for url in LENDER_URLS:
    print(f"Fetching: {url}")
    html = scrape_rates(url)
    with open(f"debug_html/{url.split('//')[1].split('/')[0]}.html", "w", encoding="utf-8") as f:
        f.write(html)
    rates = extract_rates(html)
    print(f"Extracted rates: {rates}")
    if all(rates.get(term) is None for term in ["15yr", "20yr", "30yr"]):
        print(f"[WARNING] No rates found for {url}. Check debug_html for raw HTML.")
