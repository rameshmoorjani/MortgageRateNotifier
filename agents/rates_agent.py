"""
Mortgage Rates Agent - Fetches real-time mortgage rates from free APIs

Sources:
1. Freddie Mac PMMS - Official US mortgage rates (30-yr, 15-yr, 5/1 ARM)
2. FRED API - Federal Reserve Economic Data (historical rates)
3. MortgageNewsDaily - Current rates (web scraping fallback)

Usage:
    agent = RatesAgent()
    rates = agent.get_current_rates(state="CA")
    
    # Or get historical rates
    historical = agent.get_historical_rates(days=30)
"""

import os
import sys
import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv
import re
import time
from functools import lru_cache
from pathlib import Path

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Try to import config_aws for Parameter Store support
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from src.config_aws import get_fred_api_key as get_fred_api_key_aws
    HAS_AWS_CONFIG = True
except ImportError:
    HAS_AWS_CONFIG = False
    get_fred_api_key_aws = None


class RatesAgent:
    """Fetch mortgage rates from free public sources."""
    
    # Freddie Mac PMMS data
    FREDDIE_MAC_URL = "https://www.freddiemac.com/pmms/pmmshistoricaldata.html"
    FREDDIE_MAC_API = "https://freddiemac.com/pmms/current"
    
    # FRED API - Federal Reserve Economic Data (FREE, requires registration)
    # API key loaded from FRED_API_KEY environment variable in __init__
    FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
    
    # Alternative FRED endpoints (in case primary fails)
    FRED_ALT_URL = "https://api.stlouisfed.org/fred/data"
    FRED_SERIES = {
        "30YR": "MORTGAGE30US",      # 30-year mortgage rate
        "15YR": "MORTGAGE15US",      # 15-year mortgage rate
        "5_1ARM": "MORTGAGE5US",     # 5/1 ARM rate
    }
    
    # Cache for 1 hour to avoid rate limiting
    CACHE_DURATION = 3600  # seconds
    
    def __init__(self):
        """Initialize rates agent."""
        self.cache = {}
        self.cache_time = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Load FRED API key - try Parameter Store first (production), then environment (development)
        self.fred_api_key = None
        
        if HAS_AWS_CONFIG and get_fred_api_key_aws:
            # Production: Try AWS Parameter Store
            self.fred_api_key = get_fred_api_key_aws()
        
        if not self.fred_api_key:
            # Development: Try environment variable
            self.fred_api_key = os.getenv("FRED_API_KEY")
        
        if self.fred_api_key:
            logger.info("✓ FRED API key loaded - using real Federal Reserve data")
        else:
            logger.warning("✗ FRED_API_KEY not set - will use mock data. Get free key at https://stlouisfed.org/")
    
    def get_current_rates(self, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current mortgage rates from Freddie Mac PMMS.
        
        Args:
            state: Optional state code (currently not filtered by state in free data)
        
        Returns:
            Dict with current rates:
            {
                'source': 'Freddie Mac PMMS',
                'timestamp': '2024-01-15T10:00:00Z',
                'rates': {
                    '30_year': 6.75,
                    '15_year': 6.15,
                    '5_1_arm': 6.10
                },
                'week_change': {'30_year': 0.05, ...},
                'confidence': 'high'
            }
        """
        # Check cache
        cache_key = f"current_rates_{state or 'national'}"
        if self._is_cached(cache_key):
            return self.cache[cache_key]
        
        try:
            # Try Freddie Mac PMMS (official source)
            rates = self._fetch_freddie_mac_rates()
            
            if rates:
                self.cache[cache_key] = rates
                self.cache_time[cache_key] = time.time()
                return rates
            
            # Fallback to FRED API
            logger.info("Freddie Mac unavailable, trying FRED API...")
            rates = self._fetch_fred_rates()
            
            if rates:
                self.cache[cache_key] = rates
                self.cache_time[cache_key] = time.time()
                return rates
            
            # Return mock data if both fail
            logger.warning("All rate sources failed, returning mock data")
            return self._get_mock_rates()
            
        except Exception as e:
            logger.error(f"Error fetching current rates: {e}")
            return self._get_mock_rates()
    
    def _fetch_freddie_mac_rates(self) -> Optional[Dict[str, Any]]:
        """
        Fetch rates from Freddie Mac PMMS.
        
        Official US mortgage rates, updated Thursdays.
        """
        try:
            # Freddie Mac publishes JSON data
            response = self.session.get(
                "https://www.freddiemac.com/pmms/current",
                timeout=10
            )
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # Extract current rates
            return {
                'source': 'Freddie Mac PMMS (Official)',
                'timestamp': datetime.now().isoformat(),
                'rates': {
                    '30_year': float(data.get('mortgage30US', {}).get('rate')),
                    '15_year': float(data.get('mortgage15US', {}).get('rate')),
                    '5_1_arm': float(data.get('mortgage5US', {}).get('rate')),
                },
                'week_change': {
                    '30_year': float(data.get('mortgage30US', {}).get('wk1chg')),
                    '15_year': float(data.get('mortgage15US', {}).get('wk1chg')),
                    '5_1_arm': float(data.get('mortgage5US', {}).get('wk1chg')),
                },
                'confidence': 'high',
                'notice': 'Updated Thursdays at 10am ET'
            }
            
        except Exception as e:
            logger.warning(f"Freddie Mac fetch failed: {e}")
            return None
    
    def _fetch_fred_rates(self) -> Optional[Dict[str, Any]]:
        """
        Fetch rates from Federal Reserve FRED API.
        
        Requires free API key from: https://stlouisfed.org/
        """
        try:
            if not self.fred_api_key:
                logger.debug("FRED API key not configured")
                return None
            
            rates = {}
            
            for rate_type, series_id in self.FRED_SERIES.items():
                # Use the observations endpoint which is the correct FRED API endpoint
                response = self.session.get(
                    "https://api.stlouisfed.org/fred/series/observations",
                    params={
                        'series_id': series_id,
                        'api_key': self.fred_api_key,
                        'limit': 1,
                        'sort_order': 'desc',
                        'file_type': 'json'
                    },
                    timeout=10
                )
                response.raise_for_status()
                
                data = response.json()
                if data.get('observations'):
                    latest = data['observations'][0]
                    value = latest.get('value')
                    if value and value != '.':
                        rates[rate_type] = float(value)
            
            if rates:
                return {
                    'source': 'Federal Reserve FRED',
                    'timestamp': datetime.now().isoformat(),
                    'rates': {
                        '30_year': rates.get('30YR'),
                        '15_year': rates.get('15YR'),
                        '5_1_arm': rates.get('5_1ARM'),
                    },
                    'confidence': 'high',
                    'notice': 'Updated weekly'
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"FRED API fetch failed: {e}")
            return None
    
    def get_historical_rates(self, days: int = 30) -> Dict[str, Any]:
        """
        Get historical mortgage rates for the last N days.
        
        Args:
            days: Number of days of history to retrieve (max 365)
        
        Returns:
            Dict with time series of historical rates
        """
        cache_key = f"historical_rates_{days}"
        if self._is_cached(cache_key):
            return self.cache[cache_key]
        
        try:
            historical = self._fetch_fred_historical(days)
            
            if historical:
                self.cache[cache_key] = historical
                self.cache_time[cache_key] = time.time()
                return historical
            
            return {
                'source': 'Historical Data Unavailable',
                'message': 'Consider setting up FRED API key for historical data',
                'setup_url': 'https://stlouisfed.org/apps/fred/'
            }
            
        except Exception as e:
            logger.error(f"Error fetching historical rates: {e}")
            return {'error': str(e)}
    
    def _fetch_fred_historical(self, days: int) -> Optional[Dict[str, Any]]:
        """Fetch historical rates from FRED."""
        try:
            if not self.fred_api_key:
                logger.debug("FRED API key not configured for historical data")
                return None
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            historical_data = {}
            
            for rate_type, series_id in self.FRED_SERIES.items():
                response = self.session.get(
                    "https://api.stlouisfed.org/fred/series/observations",
                    params={
                        'series_id': series_id,
                        'api_key': self.fred_api_key,
                        'observation_start': start_date.isoformat(),
                        'observation_end': end_date.isoformat(),
                        'sort_order': 'asc',
                        'file_type': 'json'
                    },
                    timeout=10
                )
                response.raise_for_status()
                
                data = response.json()
                observations = data.get('observations', [])
                
                historical_data[rate_type] = [
                    {
                        'date': obs['date'],
                        'rate': float(obs['value']) if obs['value'] and obs['value'] != '.' else None
                    }
                    for obs in observations
                ]
            
            return {
                'source': 'Federal Reserve FRED',
                'period': f'Last {days} days',
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'historical_data': historical_data,
                'confidence': 'high'
            }
            
        except Exception as e:
            logger.warning(f"FRED historical fetch failed: {e}")
            return None
    
    def get_rates_for_prediction(
        self,
        predicted_direction: str,
        confidence: float
    ) -> Dict[str, Any]:
        """
        Get rates and estimate predicted rates based on market direction.
        
        Args:
            predicted_direction: "UP", "DOWN", or "STABLE"
            confidence: Confidence in prediction (0.0 - 1.0)
        
        Returns:
            Dict with current and predicted rates
        """
        current = self.get_current_rates()
        
        if 'rates' not in current:
            return current
        
        # Estimate predicted rates based on direction and confidence
        rate_30yr = current['rates']['30_year']
        
        if predicted_direction == "DOWN":
            # Predict drop proportional to confidence
            drop = rate_30yr * 0.01 * confidence  # 1% drop per 100% confidence
            predicted_30yr = max(rate_30yr - drop, rate_30yr - 0.5)  # Cap at -0.5%
        elif predicted_direction == "UP":
            # Predict rise proportional to confidence
            rise = rate_30yr * 0.01 * confidence  # 1% rise per 100% confidence
            predicted_30yr = min(rate_30yr + rise, rate_30yr + 0.5)  # Cap at +0.5%
        else:
            predicted_30yr = rate_30yr
        
        return {
            'source': current['source'],
            'timestamp': current.get('timestamp'),
            'current_rates': current['rates'],
            'predicted_rates': {
                '30_year': round(predicted_30yr, 2),
                '15_year': round(current['rates']['15_year'] - (rate_30yr - predicted_30yr), 2),
                '5_1_arm': round(current['rates']['5_1_arm'] - (rate_30yr - predicted_30yr), 2),
            },
            'predicted_direction': predicted_direction,
            'prediction_confidence': confidence,
            'confidence_in_rates': current.get('confidence', 'medium')
        }
    
    def _is_cached(self, key: str) -> bool:
        """Check if cache is still valid."""
        if key not in self.cache:
            return False
        
        age = time.time() - self.cache_time.get(key, 0)
        return age < self.CACHE_DURATION
    
    def _get_mock_rates(self) -> Dict[str, Any]:
        """Return realistic mock data for testing."""
        return {
            'source': 'Mock Data (APIs Unavailable)',
            'timestamp': datetime.now().isoformat(),
            'rates': {
                '30_year': 6.75,
                '15_year': 6.15,
                '5_1_arm': 6.10
            },
            'week_change': {
                '30_year': 0.05,
                '15_year': 0.03,
                '5_1_arm': 0.02
            },
            'confidence': 'low',
            'notice': 'Using cached/mock data. Set up Freddie Mac or FRED API for real data.'
        }
    
    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
        self.cache_time.clear()
        logger.info("Rates cache cleared")


# Example usage
if __name__ == "__main__":
    agent = RatesAgent()
    
    # Get current rates
    print("=== CURRENT RATES ===")
    rates = agent.get_current_rates()
    print(f"30-Year: {rates['rates']['30_year']}%")
    print(f"15-Year: {rates['rates']['15_year']}%")
    print(f"5/1 ARM: {rates['rates']['5_1_arm']}%")
    
    # Get rates for a prediction
    print("\n=== PREDICTED RATES (DOWN 80% CONFIDENCE) ===")
    predicted = agent.get_rates_for_prediction("DOWN", 0.80)
    print(f"Predicted 30-Year: {predicted['predicted_rates']['30_year']}%")
