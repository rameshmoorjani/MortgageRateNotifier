"""
Script: ai_generate_lender_urls.py
Purpose: Use OpenAI LLM to generate a list of major US banks and credit unions and their likely mortgage rates URLs.
"""

import openai
import json
import os

# Load API key from environment variable
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("OPENAI_API_KEY not set in environment.")

prompt = (
    "List 20 major banks and 20 major credit unions that operate in Arizona, and for each, provide the likely URL of their mortgage rates page. "
    "Return the result as a JSON array of objects with keys 'name' and 'url'. "
    "If you are unsure of the exact URL, provide the most likely mortgage rates page based on the institution's website structure. "
    "Do not include duplicates or section headers."
)

client = openai.OpenAI(api_key=API_KEY)
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}],
    temperature=0,
)
content = response.choices[0].message.content
print("[LLM Raw Output]\n", content)

# Try to parse JSON from LLM output
try:
    lender_list = json.loads(content)
    print("\n[Parsed Lender List]")
    lender_list_with_url = [l for l in lender_list if 'url' in l]
    for lender in lender_list_with_url:
        print(f"{lender['name']}: {lender['url']}")
    # Optionally, save to file (only entries with 'url')
    with open("lender_urls.json", "w", encoding="utf-8") as f:
        json.dump(lender_list_with_url, f, indent=2)
    print("\nSaved lender_urls.json")
except Exception as e:
    print("Error parsing LLM output as JSON:", e)
