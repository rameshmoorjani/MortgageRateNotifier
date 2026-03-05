
def get_fred_30yr_rate(fred_api_key):
    """Fetch and print latest 30yr fixed mortgage rate from FRED."""
    import requests
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": "MORTGAGE30US",
        "api_key": fred_api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        latest = data['observations'][0]
        print("FRED 30yr Mortgage Rate:")
        print("Date:", latest['date'])
        print("30yr:", latest['value'])
    except Exception as e:
        print(f"[ERROR] Failed to fetch FRED 30yr rate: {e}")


def main():
    import os
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("[WARNING] python-dotenv not installed. .env file will not be loaded.")
    fred_api_key = os.environ.get("FRED_API_KEY") or "YOUR_FRED_API_KEY_HERE"
    if fred_api_key == "YOUR_FRED_API_KEY_HERE":
        print("[ERROR] Please set your FRED API key in the FRED_API_KEY environment variable or in the script.")
    else:
        get_fred_30yr_rate(fred_api_key)

if __name__ == '__main__':
    main()
