
import csv
import requests
import openai
import time
import os
from dotenv import load_dotenv
load_dotenv()


# Configuration values loaded from environment or defaults
OPENAI_API_KEY = "xxxx"  # Dummy value for OpenAI API key
PLAYWRIGHT_BROWS_PATH = os.getenv("PLAYWRIGHT_BROWS_PATH")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = "xxxx"  # Dummy value for Search Engine ID
USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

# Debug: print key values to verify environment loading
print("GOOGLE_API_KEY:", GOOGLE_API_KEY)
print("SEARCH_ENGINE_ID:", SEARCH_ENGINE_ID)


openai.api_key = OPENAI_API_KEY

FDIC_BANKS_CSV = './data/fdic_banks.csv'
NCUA_CREDIT_UNIONS_CSV = './data/ncua_credit_unions.csv'

HEADERS = {'User-Agent': USER_AGENT}

# 1. Extract Arizona banks and credit unions
def extract_az_institutions():
    az_banks = []
    with open(FDIC_BANKS_CSV, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['STNAME'].strip().lower() == 'arizona':
                az_banks.append({'name': row['NAME'], 'web': row['WEBADDR']})
    az_cus = []
    with open(NCUA_CREDIT_UNIONS_CSV, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row.get('State', '').strip().lower() == 'az':
                az_cus.append({'name': row['CreditUnionName'], 'web': row.get('URL', '')})
    return az_banks + az_cus

# 2. Search for mortgage rates page
def search_mortgage_page(inst_name):
    # Use Google Custom Search API
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': GOOGLE_API_KEY,
        'cx': SEARCH_ENGINE_ID,
        'q': f"{inst_name} 30 year fixed mortgage rates",
        'num': 3
    }
    print(f"[DEBUG] Querying Google CSE: {url} with params {params}")
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        data = resp.json()
        if 'items' in data and data['items']:
            for item in data['items']:
                return item.get('link')
        else:
            print(f"[DEBUG] No items found in response for {inst_name}. Full response:")
            print(data)
    else:
        print(f"[DEBUG] Google CSE API error: {resp.status_code} {resp.text}")
    return None

# 3. Fetch page HTML
def fetch_html(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return None

# 4. Use LLM to extract rate and promo
def extract_rate_and_promo(html, inst_name):
    prompt = f"""
You are a financial data extraction assistant. Given the following HTML from a bank or credit union's mortgage rates page, extract:
- The 30-year fixed mortgage rate (APR or interest rate, whichever is available)
- Any promotional offers or special discounts mentioned

If not found, say 'Not found'.

Institution: {inst_name}
HTML:
{html[:6000]}  # Truncate to fit token limits
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {e}"

# 5. Main pipeline
def main():
    az_institutions = extract_az_institutions()
    results = []
    for inst in az_institutions:
        print(f"Searching: {inst['name']}")
        page_url = search_mortgage_page(inst['name'])
        if not page_url:
            print("  No mortgage page found.")
            continue
        html = fetch_html(page_url)
        if not html:
            print("  Could not fetch page.")
            continue
        result = extract_rate_and_promo(html, inst['name'])
        print(f"  Result: {result}")
        results.append({'name': inst['name'], 'url': page_url, 'result': result})
        time.sleep(2)  # Be polite to APIs
    # Find lowest rate
    # (You can add code here to parse and compare rates from results)
    print("\nSummary:")
    for r in results:
        print(f"{r['name']}: {r['result']} (URL: {r['url']})")

if __name__ == "__main__":
    main()
