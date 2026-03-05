from dotenv import load_dotenv
import os

load_dotenv()


# Configuration values loaded from environment or defaults
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set in environment.")
PLAYWRIGHT_BROWS_PATH = os.getenv("PLAYWRIGHT_BROWS_PATH")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")
USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

# Default search queries used by the search agent; override in .env if desired
SEARCH_QUERIES = [
    "mortgage rates today",
    "current mortgage rates",
]

# Keywords used by the eligibility agent to detect Arizona-specific pages
AZ_KEYWORDS = [
    "arizona",
    "az",
    "phoenix",
    "tucson",
    "scottsdale",
    "mesa",
    "tempe",
    "glendale",
]

# Thresholds and terms used by filter agent
# `RATE_THRESHOLD` is the numeric rate threshold (set to 6.0 for testing)
RATE_THRESHOLD = 6.0
# `TERMS` should list keys that may contain numeric rates in parsed items
TERMS = ["15yr", "20yr", "30yr"]

# Email configuration (set in .env for real sends)
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_PREFIX = os.getenv("EMAIL_PREFIX", "Mortgage Rate Notifier")


def require_env(var_name):
    val = os.getenv(var_name)
    if not val:
        raise EnvironmentError(f"Required environment variable '{var_name}' is not set.")
    return val
