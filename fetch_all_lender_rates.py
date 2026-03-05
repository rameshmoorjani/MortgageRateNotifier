import json
import csv
import os
import requests
from bs4 import BeautifulSoup

# 1. Load top 50 banks from curated_lender_urls.json
with open('curated_lender_urls.json', 'r', encoding='utf-8') as f:
    banks = json.load(f)

# 2. Extract Arizona credit unions from ncua_credit_unions.csv
credit_unions = []
if os.path.exists('data/ncua_credit_unions.csv'):
    with open('data/ncua_credit_unions.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            state = row.get('State') or row.get('STATE')
            url = row.get('WebAddress') or row.get('Website')
            name = row.get('CreditUnionName') or row.get('Name')
            if state and state.upper() == 'AZ' and url and name:
                credit_unions.append({'name': name, 'url': url})

# 3. Combine both lists
lenders = banks + credit_unions


# --- New function to auto-discover refinance rates page ---
def discover_refinance_url(base_url):
    try:
        resp = requests.get(base_url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            text = a.get_text(strip=True).lower()
            href = a['href']
            if 'refinance' in text or 'refinance' in href.lower():
                # Make absolute URL if needed
                from urllib.parse import urljoin
                return urljoin(base_url, href)
        return base_url
    except Exception:
        return base_url

# 4. Scrape/extract mortgage rates from each lender’s URL (with refinance discovery)

def extract_rate(url):
    # Try requests/BeautifulSoup first
    try:
        refinance_url = discover_refinance_url(url)
        resp = requests.get(refinance_url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        for table in soup.find_all('table'):
            headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
            if any('term' in h for h in headers) and any('rate' in h for h in headers) and any('apr' in h for h in headers):
                for row in table.find_all('tr'):
                    cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                    if not cells or len(cells) < 3:
                        continue
                    if '30' in cells[0] and 'refinance' in cells[0].lower():
                        try:
                            rate_idx = next(i for i, h in enumerate(headers) if 'rate' in h and 'apr' not in h)
                        except StopIteration:
                            rate_idx = 1
                        try:
                            apr_idx = next(i for i, h in enumerate(headers) if 'apr' in h)
                        except StopIteration:
                            apr_idx = 2
                        rate = cells[rate_idx] if rate_idx < len(cells) else ''
                        apr = cells[apr_idx] if apr_idx < len(cells) else ''
                        return f"Rate: {rate}, APR: {apr}"
        text = soup.get_text(' ', strip=True)
        import re
        matches = re.findall(r'(\d+\.\d+%|\d+%|\d+\.\d+ APR|\d+ APR)', text)
        if matches:
            return matches[0]
        result = 'Not found'
    except Exception as e:
        result = f'Error: {e}'

    # If not found, try Playwright
    if result == 'Not found' or result.startswith('Error:'):
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(refinance_url, timeout=20000)
                html = page.content()
                soup = BeautifulSoup(html, 'html.parser')
                for table in soup.find_all('table'):
                    headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
                    if any('term' in h for h in headers) and any('rate' in h for h in headers) and any('apr' in h for h in headers):
                        for row in table.find_all('tr'):
                            cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                            if not cells or len(cells) < 3:
                                continue
                            if '30' in cells[0] and 'refinance' in cells[0].lower():
                                try:
                                    rate_idx = next(i for i, h in enumerate(headers) if 'rate' in h and 'apr' not in h)
                                except StopIteration:
                                    rate_idx = 1
                                try:
                                    apr_idx = next(i for i, h in enumerate(headers) if 'apr' in h)
                                except StopIteration:
                                    apr_idx = 2
                                rate = cells[rate_idx] if rate_idx < len(cells) else ''
                                apr = cells[apr_idx] if apr_idx < len(cells) else ''
                                browser.close()
                                return f"[PW] Rate: {rate}, APR: {apr}"
                text = soup.get_text(' ', strip=True)
                import re
                matches = re.findall(r'(\d+\.\d+%|\d+%|\d+\.\d+ APR|\d+ APR)', text)
                browser.close()
                if matches:
                    return f"[PW] {matches[0]}"
                return '[PW] Not found'
        except Exception as e:
            return f'[PW Error: {e}]'
    return result

# 5. Print the rates
print(f"{'Lender':60} | {'URL':50} | Rate")
print('-'*130)
for lender in lenders:
    name = lender['name'][:60]
    url = lender['url'][:50]
    rate = extract_rate(lender['url'])
    print(f"{name:60} | {url:50} | {rate}")
