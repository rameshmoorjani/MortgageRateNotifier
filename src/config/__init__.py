"""
Configuration package for Mortgage Rate Notifier

Exports all configuration variables and AWS utilities for easy import across the application.
"""

# Import configuration variables
from .config import (
    OPENAI_API_KEY,
    PLAYWRIGHT_BROWS_PATH,
    GOOGLE_API_KEY,
    SEARCH_ENGINE_ID,
    SEARCH_API_KEY,
    USER_AGENT,
    SEARCH_QUERIES,
    AZ_KEYWORDS,
    RATE_THRESHOLD,
    TERMS,
    EMAIL_FROM,
    EMAIL_TO,
    EMAIL_PASSWORD,
    EMAIL_PREFIX,
    require_env,
)

# Import AWS utilities
from .aws import (
    AWSParameterStore,
    get_fred_api_key,
    get_openai_api_key,
)

__all__ = [
    # Configuration variables
    "OPENAI_API_KEY",
    "PLAYWRIGHT_BROWS_PATH",
    "GOOGLE_API_KEY",
    "SEARCH_ENGINE_ID",
    "SEARCH_API_KEY",
    "USER_AGENT",
    "SEARCH_QUERIES",
    "AZ_KEYWORDS",
    "RATE_THRESHOLD",
    "TERMS",
    "EMAIL_FROM",
    "EMAIL_TO",
    "EMAIL_PASSWORD",
    "EMAIL_PREFIX",
    "require_env",
    # AWS utilities
    "AWSParameterStore",
    "get_fred_api_key",
    "get_openai_api_key",
]
"""
Configuration package for Mortgage Rate Notifier.

Exports commonly used configuration values and AWS utilities.
"""

from .config import (
    OPENAI_API_KEY,
    PLAYWRIGHT_BROWS_PATH,
    GOOGLE_API_KEY,
    SEARCH_ENGINE_ID,
    SEARCH_API_KEY,
    USER_AGENT,
    SEARCH_QUERIES,
    AZ_KEYWORDS,
    RATE_THRESHOLD,
    TERMS,
    EMAIL_FROM,
    EMAIL_TO,
    EMAIL_PASSWORD,
    EMAIL_PREFIX,
)

from .aws import (
    AWSParameterStore,
    get_fred_api_key,
    get_openai_api_key,
)

__all__ = [
    "OPENAI_API_KEY",
    "PLAYWRIGHT_BROWS_PATH",
    "GOOGLE_API_KEY",
    "SEARCH_ENGINE_ID",
    "SEARCH_API_KEY",
    "USER_AGENT",
    "SEARCH_QUERIES",
    "AZ_KEYWORDS",
    "RATE_THRESHOLD",
    "TERMS",
    "EMAIL_FROM",
    "EMAIL_TO",
    "EMAIL_PASSWORD",
    "EMAIL_PREFIX",
    "AWSParameterStore",
    "get_fred_api_key",
    "get_openai_api_key",
]
