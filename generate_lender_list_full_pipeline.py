"""
Full pipeline to generate a comprehensive lender list for mortgage rate extraction:
- Download and parse FDIC (banks) and NCUA (credit unions) official lists
- Filter for all US national banks and only Arizona-specific credit unions
- Use LLM/search to find mortgage rates URLs for each institution
- Merge, deduplicate, and output a clean JSON file
"""
import os
import json
import requests
import csv
from typing import List, Dict

FDIC_BANKS_URL = "https://banks.data.fdic.gov/api/institutions?filters=ACTIVE%3A1&fields=NAME,WEBADDR,OFFICES,ACTIVE,CHARTER,STATE,ZIP,STNAME,CBSA,COUNTY,ASSET,ESTYMD,UNINUM,NAMEFULL&limit=10000&format=csv"
NCUA_CREDIT_UNIONS_URL = "https://mapping.ncua.gov/ResearchCreditUnion/DownloadData"

OUTPUT_LENDERS_FILE = "lender_list_full.json"


def download_fdic_banks_csv(dest_path: str):
    print("Downloading FDIC banks list...")
    r = requests.get(FDIC_BANKS_URL)
    r.raise_for_status()
    with open(dest_path, "wb") as f:
        f.write(r.content)
    print(f"Saved FDIC banks CSV to {dest_path}")

def download_ncua_credit_unions_csv(dest_path: str):
    print("Downloading NCUA credit unions list...")
    r = requests.get(NCUA_CREDIT_UNIONS_URL)
    r.raise_for_status()
    with open(dest_path, "wb") as f:
        f.write(r.content)
    print(f"Saved NCUA credit unions CSV to {dest_path}")


def parse_fdic_banks(csv_path: str) -> List[Dict]:
    banks = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            banks.append(row)
    return banks

def parse_ncua_credit_unions(csv_path: str) -> List[Dict]:
    credit_unions = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            credit_unions.append(row)
    return credit_unions


def main():
    os.makedirs("data", exist_ok=True)
    fdic_csv = os.path.join("data", "fdic_banks.csv")
    ncua_csv = os.path.join("data", "ncua_credit_unions.csv")

    download_fdic_banks_csv(fdic_csv)
    download_ncua_credit_unions_csv(ncua_csv)

    banks = parse_fdic_banks(fdic_csv)
    credit_unions = parse_ncua_credit_unions(ncua_csv)


    print(f"Loaded {len(banks)} banks and {len(credit_unions)} credit unions.")

    # --- Filter all US national banks ---
    national_banks = [
        {
            "name": b["NAMEFULL"] or b["NAME"],
            "website": b.get("WEBADDR", "")
        }
        for b in banks
        if b.get("CHARTER", "").upper() == "NAT"  # National charter
    ]
    print(f"Filtered {len(national_banks)} national banks.")

    # --- Filter only Arizona-specific credit unions ---
    # NCUA CSV: look for 'State' == 'AZ' and filter out those with multi-state fields of membership
    arizona_credit_unions = []
    for cu in credit_unions:
        state = cu.get("State", "")
        # Some NCUA files use 'State' or 'STATE'
        if state.upper() == "AZ":
            # Optionally, check for multi-state membership in 'CharterName' or 'FieldOfMembershipDesc'
            field_desc = cu.get("FieldOfMembershipDesc", "")
            if not any(s in field_desc for s in ["California", "Nevada", "New Mexico", "Utah", "Colorado", "Texas", "Mexico", "multi-state", "nationwide", "all states"]):
                arizona_credit_unions.append({
                    "name": cu.get("CreditUnionName", cu.get("Name", "")),
                    "website": cu.get("WebAddress", cu.get("Website", ""))
                })
    print(f"Filtered {len(arizona_credit_unions)} Arizona-specific credit unions.")

    # Combine for next step
    lenders = national_banks + arizona_credit_unions
    print(f"Total lenders to process: {len(lenders)}")

    # --- LLM-powered mortgage rates URL discovery ---

    import openai
    import os
    API_KEY = os.getenv("OPENAI_API_KEY")
    if not API_KEY:
        raise ValueError("OPENAI_API_KEY not set in environment.")
    client = openai.OpenAI(api_key=API_KEY)

    results = []
    for lender in lenders:
        name = lender["name"]
        website = lender.get("website", "")
        prompt = (
            f"Given the following financial institution, provide the most likely direct URL to their mortgage rates page. "
            f"If you are unsure, provide the closest mortgage/home loan rates page. "
            f"Return a JSON object with keys 'name', 'url', and 'source'. "
            f"Institution name: {name}\n"
            f"Website: {website}\n"
        )
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            content = response.choices[0].message.content
            # Try to parse JSON from LLM output
            url_obj = json.loads(content)
            if url_obj.get("url"):
                results.append({
                    "name": name,
                    "url": url_obj["url"],
                    "source": url_obj.get("source", "LLM")
                })
                print(f"[OK] {name}: {url_obj['url']}")
            else:
                print(f"[NO URL] {name}")
        except Exception as e:
            print(f"[ERROR] {name}: {e}")

    # Deduplicate by URL
    seen = set()
    deduped = []
    for entry in results:
        if entry["url"] not in seen:
            deduped.append(entry)
            seen.add(entry["url"])

    with open(OUTPUT_LENDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(deduped, f, indent=2)
    print(f"\nSaved {len(deduped)} lenders with URLs to {OUTPUT_LENDERS_FILE}")

if __name__ == "__main__":
    main()
