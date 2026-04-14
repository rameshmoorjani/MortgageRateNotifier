def extract_rates_table_markdown(html: str) -> str:
    """
    Extract the first rates table from HTML and return it as a Markdown table string.
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return ""
    rows = table.find_all("tr")
    md_lines = []
    for i, row in enumerate(rows):
        cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
        if not cells:
            continue
        line = "| " + " | ".join(cells) + " |"
        md_lines.append(line)
        if i == 0:
            md_lines.append("|" + "---|" * len(cells))
    return "\n".join(md_lines)
def find_lowest_20yr_lender(lender_rates: list) -> dict:
    """
    Given a list of dicts like [{"lender": ..., "rates": {"20yr": ...}}, ...],
    return the dict for the lender with the lowest 20yr fixed rate (ignoring None).
    """
    lowest = None
    for entry in lender_rates:
        rate = None
        # Support both LLM and traditional output
        if isinstance(entry.get("rates"), dict):
            rate = entry["rates"].get("20yr")
        elif isinstance(entry.get("20yr"), (float, int)):
            rate = entry.get("20yr")
        if rate is not None:
            if lowest is None or rate < lowest["rate"]:
                lowest = {"lender": entry.get("lender"), "rate": rate, "entry": entry}
    return lowest
from bs4 import BeautifulSoup
import re
import openai
import json


def extract_rates_llm(text: str, api_key: str) -> dict:
    """
    Use OpenAI GPT-4 to extract 10yr, 15yr, 30yr mortgage rates and APRs from text.
    Returns a dict like {"10yr": {"rate": ..., "apr": ...}, ...}
    """
    prompt = (
        "Extract the 15-year, 20-year, and 30-year mortgage interest rates and APRs from the following text. "
        "Ignore any information about points. Only extract interest rate and APR for each term. "
        "Only extract rates that actually appear in the text. Do not guess or use default values. "
        "If a rate or APR is not present, return null for that value. "
        "Return the result as JSON with keys '15yr', '20yr', '30yr', each containing 'rate' and 'apr'. "
        "Treat all of the following as equivalent: '15 Year', '15 Yr', '15yr', '15-yr' → '15yr'; '20 Year', '20 Yr', '20yr', '20-yr' → '20yr'; '30 Year', '30 Yr', '30yr', '30-yr' → '30yr'. "
        "If there are multiple rates for the same term, prefer the one labeled 'Conventional' or the lowest rate.\n\n"
        f"Text:\n{text}"
    )
    # print("\n[DEBUG] LLM Prompt:\n", prompt)  # Commented as requested
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    content = response.choices[0].message.content
    print("[DEBUG] Raw LLM Response:\n", content)
    try:
        result = json.loads(content)
        print("[DEBUG] Parsed LLM JSON Result:\n", result)
    except Exception as e:
        import re
        print("[DEBUG] JSON decode error:", e)
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            result = json.loads(match.group(0))
            print("[DEBUG] Parsed LLM JSON from substring:\n", result)
        else:
            raise ValueError("Could not parse JSON from LLM response")
    print("[DEBUG] Extracted rates (LLM):", result)
    return result


def extract_rates(html: str) -> dict:
    # --- Site-specific logic for cuwest.org ---
    soup = BeautifulSoup(html, "html.parser")
    rates = {"15yr": None, "20yr": None, "30yr": None}
    aliases = {
        "15yr": r"(?:15[-\s]?year|15[-\s]?yr|15yr|15-yr)",
        "20yr": r"(?:20[-\s]?year|20[-\s]?yr|20yr|20-yr)",
        "30yr": r"(?:30[-\s]?year|30[-\s]?yr|30yr|30-yr)",
    }
    text = re.sub(r"\s+", " ", soup.get_text()).lower()

    aprs = {"15yr": None, "20yr": None, "30yr": None}
    # --- Generic table extraction logic ---
    mortgage_keywords = [
        "conventional", "fixed", "mortgage", "home", "refinance", "purchase", "loan"
    ]
    exclude_keywords = [
        "auto", "vehicle", "car", "credit card", "personal", "boat", "rv", "motorcycle", "share", "savings", "checking", "certificate", "cd", "student"
    ]
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        header_row_idx = None
        header_map = {}
        # 1. Find header row with loan terms, but only if table context is mortgage-related
        table_text = table.get_text(" ", strip=True).lower()
        if not any(k in table_text for k in mortgage_keywords):
            continue
        if any(k in table_text for k in exclude_keywords):
            continue
        for i, row in enumerate(rows):
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            row_text = " ".join(cells).lower()
            # Skip header rows that are not mortgage-related
            if not any(k in row_text for k in mortgage_keywords):
                continue
            if any(k in row_text for k in exclude_keywords):
                continue
            for term, alias in aliases.items():
                if any(re.search(alias, c.lower()) for c in cells):
                    header_row_idx = i
                    break
            if header_row_idx is not None:
                break
        if header_row_idx is not None:
            header_cells = [td.get_text(strip=True) for td in rows[header_row_idx].find_all(["td", "th"])]
            # Map term to column index
            for idx, cell in enumerate(header_cells):
                lcell = cell.lower()
                for term, alias in aliases.items():
                    if re.search(alias, lcell):
                        header_map[term] = idx
            # 2. Find rows labeled 'Interest Rate' and 'APR'
            interest_row = None
            apr_row = None
            for row in rows[header_row_idx+1:]:
                cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                lrow = [c.lower() for c in cells]
                row_text = " ".join(lrow)
                # Only consider rows that are mortgage-related
                if not any(k in row_text for k in mortgage_keywords):
                    continue
                if any(k in row_text for k in exclude_keywords):
                    continue
                if any("interest rate" in c for c in lrow):
                    interest_row = cells
                if any("apr" in c for c in lrow):
                    apr_row = cells
                if interest_row and apr_row:
                    break
            # 3. Extract rates and APRs by column mapping
            if interest_row:
                for term, idx in header_map.items():
                    if idx < len(interest_row):
                        m = re.search(r"(\d+(?:\.\d+)?)", interest_row[idx])
                        if m:
                            val = float(m.group(1))
                            if 0.5 <= val <= 15.0:
                                rates[term] = val
            if apr_row:
                for term, idx in header_map.items():
                    if idx < len(apr_row):
                        m = re.search(r"(\d+(?:\.\d+)?)", apr_row[idx])
                        if m:
                            val = float(m.group(1))
                            if 0.5 <= val <= 15.0:
                                aprs[term] = val
            # If we found at least one rate or APR, stop after this table
            if any(rates.values()) or any(aprs.values()):
                break

    # Fallback: If APR row not found, use previous logic (first percent-looking value in row)
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True).lower() for td in row.find_all(["td", "th"])]
            for term, alias in aliases.items():
                if rates[term] is None and any(re.search(alias, c) for c in cells):
                    for c in cells:
                        m = re.search(r"(\d+(?:\.\d+)?)\s*%", c)
                        if m:
                            val = float(m.group(1))
                            if 0.5 <= val <= 15.0:
                                rates[term] = val
                                break

    # If still all None, try any percent-looking value in any table cell
    if all(rates.get(term) is None for term in aliases):
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = [td.get_text(strip=True).lower() for td in row.find_all(["td", "th"])]
                for term in aliases:
                    if rates[term] is None:
                        for c in cells:
                            m = re.search(r"(\d+(?:\.\d+)?)\s*%", c)
                            if m:
                                val = float(m.group(1))
                                if 0.5 <= val <= 15.0:
                                    rates[term] = val
                                    break

    # try to find explicit points (e.g. "0 points" or "1.5 point")
    p = re.search(r"(\d+(?:\.\d+)?)\s*(?:points|point)", text)
    if p:
        try:
            pt = float(p.group(1))
            rates["points"] = str(pt) if 0 <= pt <= 10 else "0"
        except Exception:
            rates["points"] = "0"
    else:
        rates["points"] = "0"

    # Fallback: extract all numbers that look like rates (0.5-15.0) if all rates are still None
    if all(rates.get(term) is None for term in ["15yr", "20yr", "30yr"]):
        rate_candidates = []
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(%|apr|rate)?", text):
            val = float(m.group(1))
            if 0.5 <= val <= 15.0:
                rate_candidates.append(val)
        # Remove duplicates and sort descending
        rate_candidates = sorted(set(rate_candidates), reverse=True)
        # Assign to 30yr, 20yr, 15yr if not already set
        for i, term in enumerate(["30yr", "20yr", "15yr"]):
            if rates[term] is None and i < len(rate_candidates):
                rates[term] = rate_candidates[i]

    return {"rates": rates, "aprs": aprs, "points": rates.get("points", "0")}


if __name__ == "__main__":
    import glob
    import os
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment.")
    html_dir = os.path.join(os.path.dirname(__file__), "..", "debug_html")
    html_files = glob.glob(os.path.join(html_dir, "*.html"))
    all_results = []
    for html_path in html_files:
        lender_name = os.path.splitext(os.path.basename(html_path))[0]
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
            table_md = extract_rates_table_markdown(html)
            print(f"\n[DEBUG] Extracted Markdown Table for LLM from {lender_name}:\n", table_md)
            try:
                rates_llm = extract_rates_llm(table_md, api_key)
                print(f"Extracted rates (LLM, Markdown table) for {lender_name}: {rates_llm}")
                all_results.append({"lender": lender_name, "rates": rates_llm})
            except Exception as llm_error:
                print(f"LLM extraction failed for {lender_name}: {llm_error}")
                rates = extract_rates(html)
                print(f"Extracted rates (traditional) for {lender_name}: {rates}")
                all_results.append({"lender": lender_name, "rates": rates})
        except Exception as e:
            print(f"Error reading or parsing {html_path}: {e}")
    print("\nSummary of all lenders:")
    for result in all_results:
        print(result)